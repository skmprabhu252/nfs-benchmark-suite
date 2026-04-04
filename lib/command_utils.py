#!/usr/bin/env python3
"""
Command Execution Utilities for NFS Performance Testing

This module provides centralized command execution with timeout protection
to prevent NFS hangs from stalling the entire test framework.
"""

import subprocess
import time
import logging
from typing import List, Optional, Any, Callable
from functools import wraps


class CommandTimeoutError(Exception):
    """Exception raised when a command times out."""
    pass


class RetryableError(Exception):
    """Exception raised when an operation should be retried."""
    pass


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 30.0,
    retryable_exceptions: tuple = (subprocess.CalledProcessError, OSError, IOError),
    logger: Optional[logging.Logger] = None
):
    """
    Decorator to retry a function with exponential backoff.
    
    This decorator automatically retries operations that fail due to transient
    errors like network issues, temporary NFS unavailability, or resource contention.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay between retries in seconds (default: 1.0)
        backoff_factor: Multiplier for delay after each retry (default: 2.0)
        max_delay: Maximum delay between retries in seconds (default: 30.0)
        retryable_exceptions: Tuple of exceptions that should trigger retry
        logger: Optional logger for retry messages
        
    Returns:
        Decorated function with retry logic
        
    Example:
        >>> @retry_with_backoff(max_retries=3, initial_delay=2.0)
        ... def unstable_operation():
        ...     # Operation that might fail transiently
        ...     pass
        
    Retry Schedule (with defaults):
        - Attempt 1: Immediate
        - Attempt 2: After 1.0s delay
        - Attempt 3: After 2.0s delay (1.0 * 2.0)
        - Attempt 4: After 4.0s delay (2.0 * 2.0)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except retryable_exceptions as e:
                    last_exception = e
                    
                    # Don't retry on last attempt
                    if attempt >= max_retries:
                        if logger:
                            logger.error(f"❌ Operation failed after {max_retries + 1} attempts: {func.__name__}")
                        raise
                    
                    # Log retry attempt
                    if logger:
                        logger.warning(
                            f"⚠️  Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {str(e)[:100]}"
                        )
                        logger.info(f"  Retrying in {delay:.1f}s...")
                    
                    # Wait before retry
                    time.sleep(delay)
                    
                    # Increase delay for next retry (exponential backoff)
                    delay = min(delay * backoff_factor, max_delay)
                    
                except Exception as e:
                    # Non-retryable exception - fail immediately
                    if logger:
                        logger.error(f"❌ Non-retryable error in {func.__name__}: {type(e).__name__}")
                    raise
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def run_command_with_timeout(
    cmd: List[str],
    timeout: Optional[int] = None,
    capture_output: bool = True,
    text: bool = True,
    check: bool = False,
    default_timeout: int = 300,
    retry: bool = False,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    logger: Optional[logging.Logger] = None,
    **kwargs
) -> subprocess.CompletedProcess:
    """
    Run a command with timeout protection and optional retry logic.
    
    This is a centralized wrapper around subprocess.run() that ensures all
    command executions have timeout protection. This prevents the framework
    from hanging indefinitely if NFS becomes unresponsive or commands block.
    
    Optionally supports automatic retry with exponential backoff for transient
    failures like temporary network issues or NFS hiccups.
    
    Args:
        cmd: Command and arguments as list
        timeout: Timeout in seconds (None = use default_timeout)
        capture_output: Whether to capture stdout/stderr
        text: Whether to decode output as text
        check: Whether to raise exception on non-zero exit
        default_timeout: Default timeout if none specified (default: 300s/5min)
        retry: Enable automatic retry on transient failures (default: False)
        max_retries: Maximum retry attempts if retry=True (default: 3)
        retry_delay: Initial delay between retries in seconds (default: 1.0)
        logger: Optional logger for retry messages
        **kwargs: Additional arguments to pass to subprocess.run
        
    Returns:
        CompletedProcess: Result of command execution
        
    Raises:
        CommandTimeoutError: If command exceeds timeout
        subprocess.CalledProcessError: If check=True and command fails
        
    Examples:
        >>> # Basic usage
        >>> result = run_command_with_timeout(['ls', '-la'], timeout=10)
        >>> print(result.stdout)
        
        >>> # With retry for transient failures
        >>> result = run_command_with_timeout(
        ...     ['nfsstat', '-m'],
        ...     timeout=30,
        ...     retry=True,
        ...     max_retries=3
        ... )
    """
    # Use provided timeout or default
    if timeout is None:
        timeout = default_timeout
    
    # Define the actual command execution function
    def _execute_command():
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=text,
                check=check,
                timeout=timeout,
                **kwargs
            )
            return result
            
        except subprocess.TimeoutExpired as e:
            # Command timed out - provide actionable guidance
            cmd_str = ' '.join(cmd)
            error_msg = (
                f"Command timed out after {timeout}s: {cmd_str}\n"
                f"  Possible causes:\n"
                f"  • NFS server is unresponsive or hung\n"
                f"  • Network connectivity issues\n"
                f"  • Command is taking longer than expected\n"
                f"  Troubleshooting:\n"
                f"  • Check NFS server status: ping <server>\n"
                f"  • Verify mount is responsive: ls -la <mount_path>\n"
                f"  • Check network: netstat -s | grep -i timeout\n"
                f"  • Increase timeout if operation is legitimately slow"
            )
            raise CommandTimeoutError(error_msg) from e
        
        except subprocess.CalledProcessError:
            # Re-raise CalledProcessError as-is if check=True
            raise
    
    # Execute with or without retry
    if retry:
        # Apply retry logic with exponential backoff
        delay = retry_delay
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return _execute_command()
                
            except (subprocess.CalledProcessError, OSError, IOError) as e:
                last_exception = e
                
                # Don't retry on last attempt
                if attempt >= max_retries:
                    if logger:
                        logger.error(f"❌ Command failed after {max_retries + 1} attempts: {' '.join(cmd)}")
                    raise
                
                # Log retry attempt
                if logger:
                    logger.warning(
                        f"⚠️  Attempt {attempt + 1}/{max_retries + 1} failed: {str(e)[:100]}"
                    )
                    logger.info(f"  Retrying in {delay:.1f}s...")
                
                # Wait before retry
                time.sleep(delay)
                
                # Exponential backoff
                delay = min(delay * 2.0, 30.0)
            
            except CommandTimeoutError:
                # Don't retry timeouts - they indicate a more serious problem
                raise
        
        # Should never reach here, but satisfy type checker
        if last_exception:
            raise last_exception
        # Fallback - execute one more time
        return _execute_command()
    else:
        # No retry - execute once
        return _execute_command()


def check_command_exists(command: str, timeout: int = 5) -> bool:
    """
    Check if a command is available in the system.
    
    Args:
        command: Command name to check
        timeout: Timeout in seconds (default: 5s)
        
    Returns:
        bool: True if command exists, False otherwise
        
    Example:
        >>> if check_command_exists('fio'):
        ...     print("fio is available")
    """
    try:
        run_command_with_timeout(
            ['which', command],
            timeout=timeout,
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, CommandTimeoutError):
        return False


def run_sync(timeout: int = 30) -> bool:
    """
    Run sync command to flush filesystem buffers.
    
    Args:
        timeout: Timeout in seconds (default: 30s)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        run_command_with_timeout(
            ['sync'],
            timeout=timeout,
            check=False,
            capture_output=True
        )
        return True
    except CommandTimeoutError:
        return False

# Made with Bob
