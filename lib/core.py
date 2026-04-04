#!/usr/bin/env python3
"""
Base Test Tool Class for NFS Benchmark Suite

This module provides the abstract base class that all test tools must inherit from.
It defines the interface and provides common functionality for all test tools.
"""

import subprocess
import signal
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List

from .nfs_metrics import NFSMetricsCollector
from .command_utils import (
    run_command_with_timeout as _run_command_with_timeout,
    CommandTimeoutError,
    check_command_exists,
    run_sync
)


class BaseTestTool(ABC):
    """
    Abstract base class for all test tools.
    
    This class defines the interface that all test tools must implement,
    ensuring consistency across different testing tools and making it
    easy to add new tools in the future.
    
    Attributes:
        name (str): Name of the test tool
        config (dict): Configuration for this tool
        mount_path (Path): NFS mount path for testing
        logger: Logger instance for output
        results (dict): Storage for test results
        metrics_collector: Optional system metrics collector
        nfs_metrics_collector: Optional NFS metrics collector
        network_intel: Network intelligence for validation
    """
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        mount_path: Path,
        logger,
        metrics_collector=None,
        nfs_metrics_collector=None,
        network_intel=None
    ):
        """
        Initialize the test tool.
        
        Args:
            name: Name of the test tool (e.g., 'dd', 'fio')
            config: Configuration dictionary for this tool
            mount_path: Path to NFS mount point
            logger: Logger instance for output
            metrics_collector: Optional SystemMetricsCollector instance
            nfs_metrics_collector: Optional NFSMetricsCollector instance
            network_intel: Optional NetworkIntelligence instance
        """
        self.name = name
        self.config = config
        self.mount_path = mount_path
        self.logger = logger
        self.metrics_collector = metrics_collector
        self.nfs_metrics_collector = nfs_metrics_collector
        self.network_intel = network_intel
        self.results = {}
    
    @abstractmethod
    def validate_tool(self) -> bool:
        """
        Validate that the tool is available and properly configured.
        
        Returns:
            bool: True if tool is available and ready, False otherwise
        """
        pass
    
    @abstractmethod
    def run_tests(self) -> Dict[str, Any]:
        """
        Run all tests for this tool.
        
        Returns:
            dict: Test results with status, metrics, and any errors
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """
        Clean up any files or resources created during testing.
        """
        pass
    
    def log(self, message: str, level: str = "INFO"):
        """
        Log a message using the provided logger.
        
        Args:
            message: Message to log
            level: Log level (INFO, ERROR, WARNING, SUCCESS, DEBUG)
        """
        if level == "ERROR":
            self.logger.error(message)
        elif level == "SUCCESS":
            self.logger.info(f"✓ {message}")
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "DEBUG":
            self.logger.debug(message)
        else:
            self.logger.info(message)
    
    def run_command_with_timeout(
        self,
        cmd: List[str],
        timeout: Optional[int] = None,
        capture_output: bool = True,
        text: bool = True,
        check: bool = False,
        **kwargs
    ) -> subprocess.CompletedProcess:
        """
        Run a command with timeout protection to prevent NFS hangs from stalling tests.
        
        This is a convenience wrapper that uses the centralized command_utils function
        but adds logging and config-based timeout defaults.
        
        Args:
            cmd: Command and arguments as list
            timeout: Timeout in seconds (None = use config default or 300s)
            capture_output: Whether to capture stdout/stderr
            text: Whether to decode output as text
            check: Whether to raise exception on non-zero exit
            **kwargs: Additional arguments to pass to subprocess.run
            
        Returns:
            CompletedProcess: Result of command execution
            
        Raises:
            CommandTimeoutError: If command exceeds timeout
            subprocess.CalledProcessError: If check=True and command fails
        """
        # Determine timeout from config or use default
        if timeout is None:
            timeout = self.config.get('timeout', 300)
        
        self.log(f"Command: {' '.join(cmd)}", "INFO")
        
        try:
            result = _run_command_with_timeout(
                cmd,
                timeout=timeout,
                capture_output=capture_output,
                text=text,
                check=check,
                **kwargs
            )
            
            # Log command output to log file
            if capture_output and result.stdout:
                self.log("Command stdout:", "DEBUG")
                for line in result.stdout.splitlines():
                    if line.strip():  # Only log non-empty lines
                        self.log(f"  {line}", "DEBUG")
            
            if capture_output and result.stderr:
                self.log("Command stderr:", "DEBUG")
                for line in result.stderr.splitlines():
                    if line.strip():  # Only log non-empty lines
                        self.log(f"  {line}", "DEBUG")
            
            return result
            
        except CommandTimeoutError as e:
            self.log(str(e), "ERROR")
            self.log("⚠️  NFS Timeout Detected - System may be unresponsive", "WARNING")
            self.log("  Recommended actions:", "WARNING")
            self.log("  1. Check if NFS mount is still accessible", "WARNING")
            self.log("  2. Verify network connectivity to NFS server", "WARNING")
            self.log("  3. Check NFS server logs for errors", "WARNING")
            self.log("  4. Consider remounting with different options", "WARNING")
            raise
        
        except subprocess.CalledProcessError as e:
            if check:
                cmd_str = ' '.join(cmd)
                self.log(f"❌ Command failed with exit code {e.returncode}: {cmd_str}", "ERROR")
                if e.stderr:
                    self.log(f"  Error output: {e.stderr[:200]}", "ERROR")
                self.log(f"  Troubleshooting:", "ERROR")
                self.log(f"  • Check command syntax and parameters", "ERROR")
                self.log(f"  • Verify file/directory permissions", "ERROR")
                self.log(f"  • Check available disk space: df -h", "ERROR")
                self.log(f"  • Review test configuration for this operation", "ERROR")
            raise
    
    def _check_command(self, command: str) -> bool:
        """
        Check if a command is available in the system.
        
        Args:
            command: Command name to check
            
        Returns:
            bool: True if command exists, False otherwise
        """
        return check_command_exists(command)
    
    def _start_metrics_collection(self):
        """Start system and NFS metrics collection if available."""
        if self.metrics_collector:
            self.metrics_collector.start()
        if self.nfs_metrics_collector:
            self.nfs_metrics_collector.start()
    def _stop_metrics_collection(self) -> Dict[str, Any]:
        """
        Stop metrics collection and return combined summary.
        
        Returns:
            dict: Combined metrics summary with system and NFS metrics
        """
        summary = {}
        
        # Collect system metrics
        if self.metrics_collector:
            self.metrics_collector.stop()
            system_metrics = self.metrics_collector.get_summary()
            if system_metrics:
                summary['system'] = system_metrics
        
        # Collect NFS metrics
        if self.nfs_metrics_collector:
            self.nfs_metrics_collector.stop()
            nfs_metrics = self.nfs_metrics_collector.get_summary()
            if nfs_metrics:
                summary['nfs'] = nfs_metrics
        
        return summary
        
    
    def _attach_metrics_to_result(self, result: Dict[str, Any], metrics_summary: Dict[str, Any]) -> None:
        """
        Attach metrics to test result dictionary.
        
        This helper method eliminates code duplication across all benchmark modules
        by providing a consistent way to attach system and NFS metrics to results.
        
        Args:
            result: Test result dictionary to attach metrics to
            metrics_summary: Metrics summary from _stop_metrics_collection()
        """
        if metrics_summary:
            if 'system' in metrics_summary:
                result["system_metrics"] = metrics_summary['system']
            if 'nfs' in metrics_summary:
                result["nfs_metrics"] = metrics_summary['nfs']
    
    def _check_test_enabled(self, test_name: str, test_config: Dict[str, Any]) -> bool:
        """
        Check if a test is enabled in configuration.
        
        This helper method eliminates code duplication by providing a consistent
        way to check if a test should be skipped.
        
        Args:
            test_name: Name of the test
            test_config: Test configuration dictionary
            
        Returns:
            bool: True if test is enabled, False if skipped
        """
        if not test_config.get('enabled', True):
            self.log(f"Skipping {test_name} (disabled in config)", "INFO")
            self.results[test_name] = {"status": "skipped", "reason": "disabled"}
            return False
        return True
    
    def _handle_test_error(
        self,
        test_name: str,
        exception: Exception,
        duration: float = 0.0
    ) -> Dict[str, Any]:
        """
        Handle test errors consistently across all benchmark modules.
        
        This helper method eliminates code duplication by providing a consistent
        way to handle and format test errors.
        
        Args:
            test_name: Name of the test that failed
            exception: Exception that was raised
            duration: Test duration before failure (optional)
            
        Returns:
            dict: Formatted error result dictionary
        """
        import subprocess
        
        error_details = str(exception)
        
        # Extract stderr if it's a CalledProcessError
        if isinstance(exception, subprocess.CalledProcessError):
            if hasattr(exception, 'stderr') and exception.stderr:
                error_details = exception.stderr[:300]
        
        result = {
            "status": "failed",
            "error": error_details
        }
        
        if duration > 0:
            result["duration_seconds"] = duration
        
        return result
    
    def _run_test_with_metrics(
        self,
        test_name: str,
        test_func,  # Callable - avoiding type hint for compatibility
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run a test function with automatic metrics collection.
        
        This helper method wraps test execution with metrics collection,
        eliminating the need to manually start/stop metrics in each test.
        
        Args:
            test_name: Name of the test
            test_func: Test function to execute
            *args: Positional arguments for test_func
            **kwargs: Keyword arguments for test_func
            
        Returns:
            dict: Test result with metrics attached
        """
        import time
        
        # Start metrics collection
        self._start_metrics_collection()
        start_time = time.time()
        
        try:
            result = test_func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Stop metrics and attach to result
            metrics_summary = self._stop_metrics_collection()
            
            if isinstance(result, dict):
                if 'duration_seconds' not in result:
                    result['duration_seconds'] = round(duration, 2)
                self._attach_metrics_to_result(result, metrics_summary)
            
            return result
            
        except Exception as e:
            # Stop metrics on error
            self._stop_metrics_collection()
            
            duration = time.time() - start_time
            return self._handle_test_error(test_name, e, duration)
        return summary
    def _safe_remove_path(self, path: Path, is_directory: bool = False) -> bool:
        """
        Safely remove a file or directory with verification.
        
        This method ensures proper cleanup by:
        1. Syncing filesystem buffers before removal
        2. Removing the file/directory
        3. Syncing again after removal
        4. Verifying the path no longer exists
        
        Args:
            path: Path to remove
            is_directory: True if path is a directory, False for file
            
        Returns:
            bool: True if successfully removed and verified, False otherwise
        """
        try:
            if not path.exists():
                self.log(f"Path does not exist (already cleaned): {path}", "DEBUG")
                return True
            
            # Sync filesystem buffers before removal
            run_sync(timeout=30)
            
            # Remove the path
            if is_directory:
                _run_command_with_timeout(
                    ['rm', '-rf', str(path)],
                    timeout=300,
                    check=True,
                    capture_output=True
                )
                self.log(f"Removed directory: {path}", "SUCCESS")
            else:
                path.unlink()
                self.log(f"Removed file: {path}", "SUCCESS")
            
            # Sync again after removal
            run_sync(timeout=30)
            
            # Verify removal
            if path.exists():
                self.log(f"⚠️  Path still exists after removal attempt: {path}", "WARNING")
                self.log(f"  Possible causes:", "WARNING")
                self.log(f"  • File is locked by another process", "WARNING")
                self.log(f"  • Insufficient permissions", "WARNING")
                self.log(f"  • NFS caching/stale file handle", "WARNING")
                self.log(f"  Try: lsof {path} to see what's using it", "WARNING")
                return False
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"❌ Failed to remove path {path}: {e}", "ERROR")
            self.log(f"  Check permissions: ls -la {path.parent}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Unexpected error removing path {path}: {e}", "ERROR")
            self.log(f"  Error type: {type(e).__name__}", "ERROR")
            return False
    
    
    def _validate_throughput(self, throughput: float, test_type: str = "sequential") -> Dict[str, Any]:
        """
        Validate throughput against network capacity.
        
        Args:
            throughput: Measured throughput in MB/s
            test_type: Type of test (sequential, random, etc.)
            
        Returns:
            dict: Validation results with status and message
        """
        if self.network_intel:
            return self.network_intel.validate_throughput(throughput, test_type)
        return {}

# Made with Bob
