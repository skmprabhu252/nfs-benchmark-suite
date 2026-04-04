#!/usr/bin/env python3
"""
NFS Benchmark Suite Script

This script performs comprehensive DD and FIO tests on NFS mounts to evaluate
performance across various workload patterns. Results are automatically saved
to timestamped JSON log files.

Usage:
    python3 runtest.py --mount-path /mnt/nfs1
    python3 runtest.py --mount-path /mnt/nfs1 --config custom_config.yaml
    python3 runtest.py --mount-path /mnt/nfs1 --skip-dd
    python3 runtest.py --mount-path /mnt/nfs1 --skip-fio
    python3 runtest.py --mount-path /mnt/nfs1 --skip-bonnie
    python3 runtest.py --mount-path /mnt/nfs1 --skip-dbench
    python3 runtest.py --mount-path /mnt/nfs1 --cleanup-only
"""

import argparse
import subprocess
import json
import os
import sys
import time
import re
from typing import Dict, Any

# Import validation utilities
from lib.validation import validate_mount_and_config, ValidationError
import signal
import threading
import logging
# Import command utilities for timeout protection
from lib.command_utils import run_command_with_timeout, check_command_exists, run_sync
from logging.handlers import RotatingFileHandler
# Import historical comparison
from lib.historical_comparison import HistoricalComparison

# Check for PyYAML dependency
try:
    import yaml
except ImportError:
    print("❌ Error: PyYAML is required but not installed.")
    print("  PyYAML is needed to parse configuration files")
    print("  Installation:")
    print("  • pip install pyyaml")
    print("  • pip3 install pyyaml")
    print("  • Or install all dependencies: pip install -r requirements.txt")
    print("Or: pip3 install pyyaml")
    sys.exit(1)

# Check for psutil dependency (optional for metrics)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️  Warning: psutil not installed. System metrics collection will be disabled.")
    print("  psutil provides CPU, memory, disk, and network monitoring")
    print("  Installation:")
    print("  • pip install psutil")
    print("  • pip3 install psutil")
    print("  • Or install all dependencies: pip install -r requirements.txt")
    print("  Tests will continue without system metrics")

from datetime import datetime
from pathlib import Path

# Import benchmark classes from lib package
from lib.core import BaseTestTool
from lib.dd_benchmark import DDTestTool
from lib.fio_benchmark import FIOTestTool
from lib.iozone_benchmark import IOzoneTestTool
from lib.bonnie_benchmark import BonnieTestTool
from lib.dbench_benchmark import DBenchTestTool
from lib.nfs_metrics import NFSMetricsCollector


def setup_logging(log_dir="logs", log_level=logging.INFO, debug=False):
    """
    Configure logging with both file and console handlers.
    
    Creates a rotating log file for execution tracking and a separate debug log
    for troubleshooting. Console output shows INFO and above, while files capture
    all levels including DEBUG.
    
    Args:
        log_dir (str): Directory to store log files. Created if doesn't exist.
        log_level (int): Logging level for console output (default: INFO)
        debug (bool): If True, enables DEBUG level logging to separate file
        
    Returns:
        tuple: (logger, log_file_path, debug_log_path)
        
    Example:
        >>> logger, log_file, debug_file = setup_logging(debug=True)
        >>> logger.info("Test started")
        >>> logger.debug("Detailed debug information")
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Generate timestamped log filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"nfs_test_{timestamp}.log"
    debug_log_file = log_path / f"nfs_test_debug_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger('nfs_benchmark_suite')
    logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # File handler for general execution log (INFO and above)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Debug file handler (all levels including DEBUG)
    if debug:
        debug_handler = RotatingFileHandler(
            debug_log_file,
            maxBytes=50*1024*1024,  # 50MB for debug logs
            backupCount=3
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S.%f'
        )
        debug_handler.setFormatter(debug_formatter)
        logger.addHandler(debug_handler)
    
    # Console handler (INFO and above, or DEBUG if debug mode)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug else log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    logger.info(f"Logging initialized - Log file: {log_file}")
    if debug:
        logger.debug(f"Debug logging enabled - Debug file: {debug_log_file}")
    
    return logger, str(log_file), str(debug_log_file) if debug else None


class Colors:
    """
    ANSI color codes for terminal output formatting.
    
    Provides color constants for enhancing console output readability.
    Colors are compatible with most modern terminals.
    
    Attributes:
        HEADER (str): Magenta color for headers
        OKBLUE (str): Blue color for informational messages
        OKCYAN (str): Cyan color for progress indicators
        OKGREEN (str): Green color for success messages
        WARNING (str): Yellow color for warnings
        FAIL (str): Red color for errors
        ENDC (str): Reset to default color
        BOLD (str): Bold text formatting
        UNDERLINE (str): Underlined text formatting
        
    Example:
        >>> print(f"{Colors.OKGREEN}Success!{Colors.ENDC}")
        >>> print(f"{Colors.BOLD}{Colors.HEADER}Test Results{Colors.ENDC}")
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ProgressMonitor:
    """
    Monitor and display real-time progress for long-running tests.
    
    Provides visual progress bars with percentage completion, elapsed time,
    and estimated time to completion (ETA). Supports both time-based tests
    (FIO) and size-based tests (DD).
    
    The progress monitor runs in a background thread for time-based tests
    and updates every 2 seconds to minimize overhead while providing
    meaningful feedback.
    
    Attributes:
        total_duration (float): Expected test duration in seconds
        total_size (float): Expected data size in MB
        test_name (str): Display name for the test
        start_time (float): Test start timestamp
        last_update (float): Last progress update timestamp
        running (bool): Monitor active status
        thread (Thread): Background monitoring thread
        current_progress (float): Current progress percentage
        update_interval (float): Seconds between updates (default: 2.0)
        
    Example:
        >>> # Time-based monitoring (FIO test)
        >>> progress = ProgressMonitor(total_duration=120, test_name="FIO Test")
        >>> progress.start()
        >>> # ... test runs ...
        >>> progress.stop()
        
        >>> # Size-based monitoring (DD test)
        >>> progress = ProgressMonitor(total_size=10000, test_name="DD Write")
        >>> progress.start()
        >>> for chunk in range(100):
        >>>     progress.update_size_progress(chunk * 100)
        >>> progress.stop()
    """
    
    def __init__(self, total_duration=None, total_size=None, test_name="Test"):
        """
        Initialize progress monitor for test execution tracking.
        
        Args:
            total_duration (float, optional): Expected duration in seconds for time-based tests.
                Used for FIO tests where runtime is known upfront.
            total_size (float, optional): Expected size in MB for size-based tests.
                Used for DD tests where data volume is known.
            test_name (str): Human-readable name displayed in progress bar.
                Default is "Test".
                
        Note:
            Provide either total_duration OR total_size, not both.
            The monitor automatically selects the appropriate tracking method.
        """
        self.total_duration = total_duration
        self.total_size = total_size
        self.test_name = test_name
        self.start_time = None
        self.last_update = 0
        self.running = False
        self.thread = None
        self.current_progress = 0
        self.update_interval = 2.0  # Update every 2 seconds
    
    def start(self):
        """
        Start progress monitoring and initialize tracking.
        
        For time-based tests, launches a background daemon thread that
        updates progress automatically. For size-based tests, progress
        must be updated manually via update_size_progress().
        
        Thread-safe and can be called multiple times (restarts monitoring).
        """
        self.start_time = time.time()
        self.running = True
        self.last_update = 0
        self.current_progress = 0
        
        if self.total_duration:
            # For time-based tests, start background thread
            self.thread = threading.Thread(target=self._monitor_time_progress, daemon=True)
            self.thread.start()
    
    def stop(self):
        """
        Stop progress monitoring and display final completion.
        
        Terminates background thread (if running), displays 100% completion,
        and adds a newline for clean console output. Safe to call multiple
        times or if monitoring was never started.
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        # Print final 100% completion
        if self.start_time:
            self._print_progress(100, time.time() - self.start_time, 0)
            print()  # New line after completion
    
    def update_size_progress(self, current_size_mb):
        """
        Update progress for size-based tests (DD operations).
        
        Call this method periodically as data is processed to update the
        progress bar. Updates are throttled to update_interval (2 seconds)
        to avoid excessive console output.
        
        Args:
            current_size_mb (float): Current amount of data processed in MB.
                Should be between 0 and total_size.
                
        Note:
            This method does nothing if total_size was not provided during
            initialization or if start() has not been called.
            
        Example:
            >>> progress = ProgressMonitor(total_size=1000, test_name="DD Write")
            >>> progress.start()
            >>> progress.update_size_progress(250)  # 25% complete
            >>> progress.update_size_progress(500)  # 50% complete
            >>> progress.stop()
        """
        if not self.total_size or not self.start_time:
            return
        
        elapsed = time.time() - self.start_time
        
        # Only update if enough time has passed
        if elapsed - self.last_update < self.update_interval:
            return
        
        self.last_update = elapsed
        percentage = min(100, (current_size_mb / self.total_size) * 100)
        
        # Calculate ETA
        if percentage > 0:
            eta = (elapsed / percentage) * (100 - percentage)
        else:
            eta = 0
        
        self._print_progress(percentage, elapsed, eta)
    
    def _monitor_time_progress(self):
        """
        Monitor progress for time-based tests in background thread.
        
        Private method that runs in a daemon thread, automatically updating
        progress based on elapsed time. Updates every update_interval seconds
        until stop() is called or total_duration is reached.
        
        Thread-safe and handles graceful shutdown.
        """
        while self.running and self.start_time:
            elapsed = time.time() - self.start_time
            
            if elapsed - self.last_update >= self.update_interval:
                self.last_update = elapsed
                
                if self.total_duration:
                    percentage = min(100, (elapsed / self.total_duration) * 100)
                    eta = max(0, self.total_duration - elapsed)
                    self._print_progress(percentage, elapsed, eta)
            
            time.sleep(0.5)
    
    def _print_progress(self, percentage, elapsed, eta):
        """
        Print formatted progress bar with statistics to console.
        
        Creates a 40-character progress bar with filled (█) and unfilled (░)
        segments, along with percentage, elapsed time, and ETA. Uses ANSI
        escape codes to overwrite the previous line for smooth updates.
        
        Args:
            percentage (float): Completion percentage (0-100)
            elapsed (float): Elapsed time in seconds since start
            eta (float): Estimated time remaining in seconds
            
        Note:
            Output format: [████████░░░░] 50.0% | Elapsed: 01:30 | ETA: 01:30
        """
        # Create progress bar
        bar_length = 40
        filled = int(bar_length * percentage / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        # Format time strings
        elapsed_str = self._format_time(elapsed)
        eta_str = self._format_time(eta) if eta > 0 else "00:00"
        
        # Print progress (overwrite previous line)
        print(f'\r{Colors.OKCYAN}{self.test_name}{Colors.ENDC} [{bar}] '
              f'{percentage:5.1f}% | Elapsed: {elapsed_str} | ETA: {eta_str}',
              end='', flush=True)
    
    def _format_time(self, seconds):
        """
        Format seconds as human-readable time string.
        
        Converts seconds to MM:SS format for durations under 1 hour,
        or HH:MM:SS format for longer durations.
        
        Args:
            seconds (float): Time duration in seconds
            
        Returns:
            str: Formatted time string (e.g., "05:30" or "01:05:30")
            
        Example:
            >>> monitor._format_time(90)
            '01:30'
            >>> monitor._format_time(3665)
            '01:01:05'
        """
        seconds = int(seconds)
        if seconds < 3600:
            return f"{seconds // 60:02d}:{seconds % 60:02d}"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class SystemMetricsCollector:
    """Collect system metrics during test execution"""
    
    def __init__(self, interval=1.0, network_interface=None):
        """
        Initialize metrics collector
        
        Args:
            interval: Collection interval in seconds
            network_interface: Specific network interface to monitor (e.g., 'eth0')
        """
        self.interval = interval
        self.network_interface = network_interface
        self.metrics = []
        self.running = False
        self.thread = None
        self.enabled = PSUTIL_AVAILABLE
    
    def start(self):
        """Start collecting metrics in background thread"""
        if not self.enabled:
            return
        
        self.running = True
        self.metrics = []
        self.thread = threading.Thread(target=self._collect_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop collecting metrics"""
        if not self.enabled:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _collect_loop(self):
        """Collect metrics in background thread"""
        while self.running:
            try:
                # Collect CPU and memory metrics
                cpu_percent = psutil.cpu_percent(interval=None)
                memory = psutil.virtual_memory()
                
                # Collect disk I/O metrics
                disk_io = psutil.disk_io_counters()
                
                # Collect network I/O metrics (global)
                net_io = psutil.net_io_counters()
                
                metrics = {
                    'timestamp': time.time(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_gb': memory.used / (1024**3),
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_read_mb': disk_io.read_bytes / (1024**2) if disk_io else 0,
                    'disk_write_mb': disk_io.write_bytes / (1024**2) if disk_io else 0,
                    'net_sent_mb': net_io.bytes_sent / (1024**2) if net_io else 0,
                    'net_recv_mb': net_io.bytes_recv / (1024**2) if net_io else 0
                }
                
                # Collect interface-specific network statistics
                if self.network_interface:
                    interface_stats = self._collect_interface_stats(self.network_interface)
                    if interface_stats:
                        metrics['interface_stats'] = interface_stats
                
                self.metrics.append(metrics)
                
            except Exception:
                pass  # Silently ignore collection errors
            
            time.sleep(self.interval)
    
    def _collect_interface_stats(self, interface):
        """Collect detailed statistics for specific network interface"""
        try:
            # Get per-interface I/O counters
            net_io_counters = psutil.net_io_counters(pernic=True)
            
            if interface not in net_io_counters:
                return None
            
            stats = net_io_counters[interface]
            
            return {
                'bytes_sent': stats.bytes_sent,
                'bytes_recv': stats.bytes_recv,
                'packets_sent': stats.packets_sent,
                'packets_recv': stats.packets_recv,
                'errin': stats.errin,
                'errout': stats.errout,
                'dropin': stats.dropin,
                'dropout': stats.dropout
            }
        except Exception:
            return None
    
    def get_summary(self):
        """Get summary statistics from collected metrics"""
        if not self.enabled or not self.metrics:
            return {}
        
        try:
            cpu_values = [m['cpu_percent'] for m in self.metrics]
            mem_values = [m['memory_percent'] for m in self.metrics]
            
            # Calculate deltas for disk and network
            if len(self.metrics) > 1:
                first = self.metrics[0]
                last = self.metrics[-1]
                duration = last['timestamp'] - first['timestamp']
                
                disk_read_rate = (last['disk_read_mb'] - first['disk_read_mb']) / duration if duration > 0 else 0
                disk_write_rate = (last['disk_write_mb'] - first['disk_write_mb']) / duration if duration > 0 else 0
                net_sent_rate = (last['net_sent_mb'] - first['net_sent_mb']) / duration if duration > 0 else 0
                net_recv_rate = (last['net_recv_mb'] - first['net_recv_mb']) / duration if duration > 0 else 0
            else:
                disk_read_rate = disk_write_rate = net_sent_rate = net_recv_rate = 0
            
            summary = {
                'cpu': {
                    'avg_percent': round(sum(cpu_values) / len(cpu_values), 2),
                    'max_percent': round(max(cpu_values), 2),
                    'min_percent': round(min(cpu_values), 2)
                },
                'memory': {
                    'avg_percent': round(sum(mem_values) / len(mem_values), 2),
                    'max_percent': round(max(mem_values), 2),
                    'min_percent': round(min(mem_values), 2)
                },
                'disk_io': {
                    'read_rate_mbps': round(disk_read_rate, 2),
                    'write_rate_mbps': round(disk_write_rate, 2)
                },
                'network_io': {
                    'sent_rate_mbps': round(net_sent_rate, 2),
                    'recv_rate_mbps': round(net_recv_rate, 2)
                },
                'samples_collected': len(self.metrics)
            }
            
            # Add interface-specific statistics if available
            if self.network_interface and 'interface_stats' in self.metrics[0]:
                interface_summary = self._summarize_interface_stats()
                if interface_summary:
                    summary['interface_stats'] = interface_summary
            
            return summary
        except Exception:
            return {}
    
    def _summarize_interface_stats(self):
        """Summarize interface-specific statistics"""
        try:
            # Get first and last samples with interface stats
            first = None
            last = None
            
            for m in self.metrics:
                if 'interface_stats' in m:
                    if first is None:
                        first = m
                    last = m
            
            if not first or not last or first == last:
                return None
            
            duration = last['timestamp'] - first['timestamp']
            if duration <= 0:
                return None
            
            first_stats = first['interface_stats']
            last_stats = last['interface_stats']
            
            # Calculate rates and totals
            bytes_sent_delta = last_stats['bytes_sent'] - first_stats['bytes_sent']
            bytes_recv_delta = last_stats['bytes_recv'] - first_stats['bytes_recv']
            packets_sent_delta = last_stats['packets_sent'] - first_stats['packets_sent']
            packets_recv_delta = last_stats['packets_recv'] - first_stats['packets_recv']
            
            # Calculate error and drop totals
            total_errors = (last_stats['errin'] - first_stats['errin']) + (last_stats['errout'] - first_stats['errout'])
            total_drops = (last_stats['dropin'] - first_stats['dropin']) + (last_stats['dropout'] - first_stats['dropout'])
            
            return {
                'interface': self.network_interface,
                'duration_seconds': round(duration, 2),
                'throughput': {
                    'sent_mbps': round((bytes_sent_delta / duration) / (1024**2), 2),
                    'recv_mbps': round((bytes_recv_delta / duration) / (1024**2), 2),
                    'total_mbps': round(((bytes_sent_delta + bytes_recv_delta) / duration) / (1024**2), 2)
                },
                'packets': {
                    'sent_total': packets_sent_delta,
                    'recv_total': packets_recv_delta,
                    'sent_per_sec': round(packets_sent_delta / duration, 2),
                    'recv_per_sec': round(packets_recv_delta / duration, 2)
                },
                'errors': {
                    'total': total_errors,
                    'per_sec': round(total_errors / duration, 4),
                    'input': last_stats['errin'] - first_stats['errin'],
                    'output': last_stats['errout'] - first_stats['errout']
                },
                'drops': {
                    'total': total_drops,
                    'per_sec': round(total_drops / duration, 4),
                    'input': last_stats['dropin'] - first_stats['dropin'],
                    'output': last_stats['dropout'] - first_stats['dropout']
                }
            }
        except Exception:
            return None


class NetworkIntelligence:
    """Detect and analyze network configuration from NFS mount"""
    
    def __init__(self, mount_path):
        self.mount_path = mount_path
        self.network_info = {}
    
    def detect_network_config(self):
        """Detect network configuration from NFS mount"""
        try:
            # Get NFS server IP from mount point
            server_ip = self._get_nfs_server_ip()
            if not server_ip:
                return {}
            
            # Get local IP that routes to server
            local_ip = self._get_local_ip_for_server(server_ip)
            if not local_ip:
                return {}
            
            # Get network interface from local IP
            interface = self._get_interface_from_ip(local_ip)
            if not interface:
                return {}
            
            # Get interface details (speed, duplex, etc.)
            interface_details = self._get_interface_details(interface)
            
            self.network_info = {
                'nfs_server_ip': server_ip,
                'local_ip': local_ip,
                'interface': interface,
                'interface_details': interface_details,
                'theoretical_max_throughput_mbps': self._calculate_max_throughput(interface_details)
            }
            
            return self.network_info
            
        except Exception as e:
            print(f"⚠️  Warning: Could not detect network configuration: {e}")
            print(f"  Network intelligence features will be limited")
            print(f"  This is not critical - tests will continue")
            return {}
    
    def _get_nfs_server_ip(self):
        """Extract NFS server IP from mount information"""
        try:
            # Read /proc/mounts to find NFS mount
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == str(self.mount_path):
                        # NFS mount format: server:/path
                        mount_source = parts[0]
                        if ':' in mount_source:
                            server = mount_source.split(':')[0]
                            # Could be hostname or IP, resolve to IP
                            return self._resolve_to_ip(server)
            return None
        except Exception:
            return None
    
    def _resolve_to_ip(self, hostname):
        """Resolve hostname to IP address"""
        try:
            import socket
            return socket.gethostbyname(hostname)
        except Exception:
            # If it's already an IP, return it
            return hostname if self._is_valid_ip(hostname) else None
    
    def _is_valid_ip(self, ip):
        """Check if string is a valid IP address"""
        try:
            import socket
            socket.inet_aton(ip)
            return True
        except Exception:
            return False
    
    def _get_local_ip_for_server(self, server_ip):
        """Get local IP address that routes to the NFS server"""
        try:
            import socket
            # Create a socket to determine which local IP would be used
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((server_ip, 2049))  # NFS port
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return None
    
    def _get_interface_from_ip(self, ip_address):
        """Get network interface name from IP address"""
        try:
            if not PSUTIL_AVAILABLE:
                # Fallback to ip command
                result = run_command_with_timeout(
                    ['ip', '-o', 'addr', 'show'],
                    timeout=10,
                    capture_output=True,
                    text=True,
                    check=True
                )
                for line in result.stdout.split('\n'):
                    if ip_address in line:
                        # Format: "2: eth0    inet 192.168.1.10/24 ..."
                        parts = line.split()
                        if len(parts) >= 2:
                            return parts[1]
                return None
            else:
                # Use psutil for better cross-platform support
                import psutil
                for iface, addrs in psutil.net_if_addrs().items():
                    for addr in addrs:
                        if addr.family == 2 and addr.address == ip_address:  # AF_INET
                            return iface
                return None
        except Exception:
            return None
    
    def _get_interface_details(self, interface):
        """Get detailed information about network interface"""
        details = {
            'speed_mbps': None,
            'duplex': None,
            'mtu': None,
            'driver': None
        }
        
        try:
            # Try ethtool for speed and duplex
            result = run_command_with_timeout(
                ['ethtool', interface],
                timeout=10,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if 'Speed:' in line:
                        # Extract speed (e.g., "Speed: 10000Mb/s" or "Speed: 1000Mb/s")
                        speed_str = line.split(':')[1].strip()
                        if 'Mb/s' in speed_str:
                            details['speed_mbps'] = int(speed_str.replace('Mb/s', '').strip())
                        elif 'Gb/s' in speed_str:
                            details['speed_mbps'] = int(float(speed_str.replace('Gb/s', '').strip()) * 1000)
                    elif 'Duplex:' in line:
                        details['duplex'] = line.split(':')[1].strip()
            
            # Get MTU
            if PSUTIL_AVAILABLE:
                import psutil
                stats = psutil.net_if_stats().get(interface)
                if stats:
                    details['mtu'] = stats.mtu
            else:
                # Fallback to ip command
                result = run_command_with_timeout(
                    ['ip', 'link', 'show', interface],
                    timeout=10,
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'mtu' in line.lower():
                            parts = line.split('mtu')
                            if len(parts) > 1:
                                mtu_str = parts[1].strip().split()[0]
                                details['mtu'] = int(mtu_str)
            
            # Try to get driver info
            driver_path = f"/sys/class/net/{interface}/device/driver"
            if os.path.exists(driver_path):
                driver_link = os.readlink(driver_path)
                details['driver'] = os.path.basename(driver_link)
                
        except Exception:
            pass
        
        return details
    
    def _calculate_max_throughput(self, interface_details):
        """Calculate theoretical maximum throughput in MB/s"""
        speed_mbps = interface_details.get('speed_mbps')
        if not speed_mbps:
            return None
        
        # Convert Mbps to MB/s (divide by 8 for bits to bytes)
        # Apply 95% efficiency factor for realistic maximum
        max_throughput_mbs = (speed_mbps / 8) * 0.95
        return round(max_throughput_mbs, 2)
    
    def validate_throughput(self, measured_mbps, test_type="sequential"):
        """Validate if measured throughput is reasonable given network capacity"""
        max_throughput = self.network_info.get('theoretical_max_throughput_mbps')
        
        if not max_throughput:
            return {
                'valid': None,
                'message': 'Network capacity unknown, cannot validate'
            }
        
        # Calculate percentage of network capacity used
        utilization_pct = (measured_mbps / max_throughput) * 100
        
        # Validation thresholds
        if measured_mbps > max_throughput * 1.05:  # Allow 5% margin for measurement variance
            return {
                'valid': False,
                'message': f'Throughput {measured_mbps:.1f} MB/s exceeds network capacity {max_throughput:.1f} MB/s',
                'utilization_pct': utilization_pct,
                'severity': 'error'
            }
        elif utilization_pct > 90:
            return {
                'valid': True,
                'message': f'Excellent: {utilization_pct:.1f}% network utilization',
                'utilization_pct': utilization_pct,
                'severity': 'success'
            }
        elif utilization_pct > 70:
            return {
                'valid': True,
                'message': f'Good: {utilization_pct:.1f}% network utilization',
                'utilization_pct': utilization_pct,
                'severity': 'success'
            }
        elif utilization_pct > 40:
            return {
                'valid': True,
                'message': f'Moderate: {utilization_pct:.1f}% network utilization - potential for improvement',
                'utilization_pct': utilization_pct,
                'severity': 'warning'
            }
        else:
            return {
                'valid': True,
                'message': f'Low: {utilization_pct:.1f}% network utilization - significant bottleneck detected',
                'utilization_pct': utilization_pct,
                'severity': 'warning'
            }


class NFSPerformanceTest:
    """Main class for NFS performance testing"""
    
    def __init__(self, mount_path, config_file=None, skip_dd=False, skip_fio=False, skip_iozone=False, skip_bonnie=False, skip_dbench=False, cleanup_only=False, verbose=False):
        self.mount_path = Path(mount_path)
        self.skip_dd = skip_dd
        self.skip_fio = skip_fio
        self.skip_iozone = skip_iozone
        self.skip_bonnie = skip_bonnie
        self.skip_dbench = skip_dbench
        self.cleanup_only = cleanup_only
        self.verbose = verbose
        
        # Load configuration
        self.config = self._load_config(config_file)
        
        # Initialize logging
        log_config = self.config.get('logging', {})
        debug_mode = log_config.get('debug', False) or verbose
        self.logger, self.log_file, self.debug_log_file = setup_logging(
            log_dir=log_config.get('log_dir', 'logs'),
            log_level=logging.DEBUG if debug_mode else logging.INFO,
            debug=debug_mode
        )
        
        # Initialize network intelligence
        self.network_intel = NetworkIntelligence(self.mount_path)
        
        # Detect network configuration early to get interface name
        network_config = self.network_intel.detect_network_config()
        network_interface = network_config.get('interface') if network_config else None
        
        # Initialize metrics collector with network interface
        metrics_config = self.config.get('monitoring', {})
        if isinstance(metrics_config, dict):
            metrics_enabled = metrics_config.get('system_metrics_enabled', True)
            nfs_metrics_enabled = metrics_config.get('nfs_stats_enabled', True)
            metrics_interval = metrics_config.get('collection_interval', 1.0)
        else:
            metrics_enabled = True
            nfs_metrics_enabled = True
            metrics_interval = 1.0
        
        self.metrics_collector = SystemMetricsCollector(
            interval=metrics_interval,
            network_interface=network_interface
        ) if metrics_enabled else None
        
        # Initialize NFS metrics collector
        self.nfs_metrics_collector = NFSMetricsCollector(
            mount_path=self.mount_path,
            logger=self.logger,
            collection_interval=metrics_interval
        ) if nfs_metrics_enabled else None
        
        # Generate timestamped output filename in logs directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        self.output_file = log_dir / f"nfs_benchmark_suite_{timestamp}.json"
        
        # Test directories and files (for backward compatibility)
        self.test_dir = self.mount_path / "cthon"
        self.file1 = self.mount_path / "file1"
        self.file2 = self.mount_path / "file2"
        
        # Initialize test tools
        dd_config = self.config.get('dd_tests', {})
        fio_config = self.config.get('fio_tests', {})
        iozone_config = self.config.get('iozone_tests', {})
        bonnie_config = self.config.get('bonnie_tests', {})
        dbench_config = self.config.get('dbench_tests', {})
        
        self.dd_tool = DDTestTool(
            config=dd_config,
            mount_path=self.mount_path,
            logger=self.logger,
            metrics_collector=self.metrics_collector,
            nfs_metrics_collector=self.nfs_metrics_collector,
            network_intel=self.network_intel
        )
        
        self.fio_tool = FIOTestTool(
            config=fio_config,
            mount_path=self.mount_path,
            logger=self.logger,
            metrics_collector=self.metrics_collector,
            nfs_metrics_collector=self.nfs_metrics_collector,
            network_intel=self.network_intel
        )
        
        self.iozone_tool = IOzoneTestTool(
            config=iozone_config,
            mount_path=self.mount_path,
            logger=self.logger,
            metrics_collector=self.metrics_collector,
            nfs_metrics_collector=self.nfs_metrics_collector,
            network_intel=self.network_intel
        )
        
        self.bonnie_tool = BonnieTestTool(
            config=bonnie_config,
            mount_path=self.mount_path,
            logger=self.logger,
            metrics_collector=self.metrics_collector,
            nfs_metrics_collector=self.nfs_metrics_collector,
            network_intel=self.network_intel
        )
        
        self.dbench_tool = DBenchTestTool(
            config=dbench_config,
            mount_path=self.mount_path,
            logger=self.logger,
            metrics_collector=self.metrics_collector,
            nfs_metrics_collector=self.nfs_metrics_collector,
            network_intel=self.network_intel
        )
        
        # Results storage
        self.results = {
            "test_run": {
                "timestamp": datetime.now().isoformat(),
                "mount_path": str(self.mount_path),
                "hostname": self._get_hostname(),
                "network_config": {}
            },
            "dd_tests": {},
            "fio_tests": {},
            "iozone_tests": {},
            "bonnie_tests": {},
            "dbench_tests": {},
            "summary": {
                "total_duration": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "errors": [],
                "performance_validation": []
            }
        }
        
        self.start_time = time.time()
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully (Ctrl+C, SIGTERM)"""
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        print(f"\n{Colors.WARNING}Interrupt signal ({signal_name}) received, cleaning up...{Colors.ENDC}")
        
        # Save partial results if any tests have run
        if self.results['dd_tests'] or self.results['fio_tests']:
            self.results['summary']['interrupted'] = True
            self.results['summary']['interrupt_time'] = datetime.now().isoformat()
            
            try:
                self.save_results()
                print(f"{Colors.OKBLUE}Partial results saved to: {self.output_file}{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.WARNING}Could not save partial results: {e}{Colors.ENDC}")
        
        # Cleanup test files
        try:
            self.cleanup()
            print(f"{Colors.OKGREEN}Cleanup completed successfully{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.WARNING}⚠️  Cleanup encountered errors: {e}{Colors.ENDC}")
            print(f"{Colors.WARNING}  Some test files may still exist on NFS mount{Colors.ENDC}")
            print(f"{Colors.WARNING}  Manual cleanup may be required{Colors.ENDC}")
        
        print(f"{Colors.OKBLUE}Exiting gracefully...{Colors.ENDC}")
        sys.exit(1)
    
    def _load_config(self, config_file):
        """Load configuration from YAML file"""
        if config_file is None:
            config_file = Path(__file__).parent / "test_config.yaml"
        else:
            config_file = Path(config_file)
        
        if not config_file.exists():
            print(f"⚠️  Warning: Config file not found: {config_file}, using defaults")
            return self._get_default_config()
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            # Logger not initialized yet, will log after initialization
            return config
        except Exception as e:
            print(f"⚠️  Warning: Error loading config file: {e}")
            print("   Using default configuration")
            return self._get_default_config()
    
    def _get_default_config(self):
        """Return default configuration if config file is not available"""
        return {
            'dd_tests': {'enabled': True},
            'fio_tests': {'enabled': True},
            'iozone_tests': {'enabled': True},
            'bonnie_tests': {'enabled': True},
            'execution': {
                'stop_on_error': False,
                'cleanup_on_completion': True,
                'verbose': False
            }
        }
    
    def _get_hostname(self):
        """Get system hostname"""
        try:
            result = run_command_with_timeout(
                ['hostname'],
                timeout=5,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"
    
    def log(self, message, level="INFO"):
        """
        Log message using Python's logging module.
        
        This method provides backward compatibility while using proper logging.
        Maps custom log levels to standard Python logging levels.
        
        Args:
            message (str): The message to log
            level (str): Log level - "INFO", "ERROR", "WARNING", "SUCCESS", "DEBUG"
        """
        # Map custom levels to standard logging levels
        if level == "ERROR":
            self.logger.error(message)
        elif level == "SUCCESS":
            # SUCCESS is treated as INFO with a success indicator
            self.logger.info(f"✓ {message}")
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "DEBUG":
            self.logger.debug(message)
        elif level == "INFO":
            self.logger.info(message)
        else:
            # Default to INFO for unknown levels
            self.logger.info(message)
    
    def validate_environment(self):
        """Validate environment and dependencies"""
        self.log("Validating environment...", "INFO")
        
        # Check if mount path exists
        if not self.mount_path.exists():
            self.log(f"Mount path does not exist: {self.mount_path}", "ERROR")
            return False
        
        if not self.mount_path.is_dir():
            self.log(f"Mount path is not a directory: {self.mount_path}", "ERROR")
            return False
        
        # Check if mount path is writable
        if not os.access(self.mount_path, os.W_OK):
            self.log(f"Mount path is not writable: {self.mount_path}", "ERROR")
            return False
        
        # Detect network configuration
        if not self.cleanup_only:
            self.log("Detecting network configuration...", "INFO")
            network_config = self.network_intel.detect_network_config()
            
            if network_config:
                self.results["test_run"]["network_config"] = network_config
                self.log(f"NFS Server: {network_config.get('nfs_server_ip', 'unknown')}", "INFO")
                self.log(f"Local IP: {network_config.get('local_ip', 'unknown')}", "INFO")
                self.log(f"Interface: {network_config.get('interface', 'unknown')}", "INFO")
                
                interface_details = network_config.get('interface_details', {})
                if interface_details.get('speed_mbps'):
                    speed_gbps = interface_details['speed_mbps'] / 1000
                    self.log(f"Network Speed: {speed_gbps:.1f} Gbps ({interface_details['speed_mbps']} Mbps)", "INFO")
                
                max_throughput = network_config.get('theoretical_max_throughput_mbps')
                if max_throughput:
                    self.log(f"Theoretical Max Throughput: {max_throughput:.1f} MB/s", "INFO")
            else:
                self.log("Could not detect network configuration - validation will be limited", "WARNING")
        
        # Validate test tools
        if not self.skip_dd and not self.cleanup_only:
            if not self.dd_tool.validate_tool():
                return False
        
        if not self.skip_fio and not self.cleanup_only:
            if not self.fio_tool.validate_tool():
                return False
        
        if not self.skip_iozone and not self.cleanup_only:
            if not self.iozone_tool.validate_tool():
                return False
        
        if not self.skip_bonnie and not self.cleanup_only:
            if not self.bonnie_tool.validate_tool():
                return False
        
        # Check disk space
        if not self._check_disk_space():
            return False
        
        self.log("Environment validation passed", "SUCCESS")
        return True
    
    def _check_command(self, command):
        """Check if a command exists"""
        return check_command_exists(command)
    
    def _parse_size_to_gb(self, block_size, count):
        """Parse block size string and count to calculate size in GB
        
        Args:
            block_size: Block size string (e.g., '1M', '4K', '1G')
            count: Number of blocks
        
        Returns:
            float: Size in GB
        """
        # Remove any whitespace
        block_size = block_size.strip().upper()
        
        # Extract number and unit
        import re
        match = re.match(r'(\d+)([KMGT]?)', block_size)
        if not match:
            return 0.0
        
        size_num = int(match.group(1))
        unit = match.group(2) if match.group(2) else 'B'
        
        # Convert to bytes
        multipliers = {
            'B': 1,
            'K': 1024,
            'M': 1024**2,
            'G': 1024**3,
            'T': 1024**4
        }
        
        bytes_per_block = size_num * multipliers.get(unit, 1)
        total_bytes = bytes_per_block * count
        total_gb = total_bytes / (1024**3)
        
        return total_gb
    
    def _check_disk_space(self):
        """Check if sufficient disk space is available for tests"""
        if self.cleanup_only:
            return True
        
        self.log("Checking available disk space...", "INFO")
        
        try:
            stat = os.statvfs(self.mount_path)
            available_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
            
            # Calculate required space based on config
            required_gb = 0.0
            
            # Calculate DD test space requirements
            if not self.skip_dd:
                dd_config = self.config.get('dd_tests', {})
                for test_name, test_config in dd_config.items():
                    if test_name == 'enabled':
                        continue
                    
                    if not isinstance(test_config, dict):
                        continue
                    
                    if not test_config.get('enabled', True):
                        continue
                    
                    block_size = test_config.get('block_size', '1M')
                    count = test_config.get('count', 100000)
                    size_gb = self._parse_size_to_gb(block_size, count)
                    required_gb += size_gb
            
            # Calculate FIO test space requirements
            if not self.skip_fio:
                fio_config = self.config.get('fio_tests', {})
                for test_name, test_config in fio_config.items():
                    if test_name in ['enabled', 'common']:
                        continue
                    
                    if not isinstance(test_config, dict):
                        continue
                    
                    if not test_config.get('enabled', True):
                        continue
                    
                    # Get size parameter
                    size_str = test_config.get('size', '0')
                    if size_str:
                        # Parse size (e.g., '4G', '2G', '1G')
                        size_gb = self._parse_size_to_gb(size_str, 1)
                        numjobs = test_config.get('numjobs', 1)
                        required_gb += size_gb * numjobs
                    
                    # Handle filesize and nrfiles for metadata tests
                    if 'filesize' in test_config and 'nrfiles' in test_config:
                        filesize = test_config.get('filesize', '1M')
                        nrfiles = test_config.get('nrfiles', 1)
                        numjobs = test_config.get('numjobs', 1)
                        file_gb = self._parse_size_to_gb(filesize, 1)
                        required_gb += file_gb * nrfiles * numjobs
            
            # Add 10GB buffer for safety
            required_gb += 10
            
            self.log(f"Disk space available: {available_gb:.1f} GB", "INFO")
            self.log(f"Disk space required: {required_gb:.1f} GB", "INFO")
            
            if available_gb < required_gb:
                error_msg = (
                    f"Insufficient disk space:\n"
                    f"  Available: {available_gb:.1f} GB\n"
                    f"  Required:  {required_gb:.1f} GB\n"
                    f"  Shortfall: {required_gb - available_gb:.1f} GB"
                )
                self.log(error_msg, "ERROR")
                return False
            
            self.log(f"Disk space check passed: {available_gb:.1f} GB available, {required_gb:.1f} GB required", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Failed to check disk space: {e}", "WARNING")
            # Don't fail validation if we can't check disk space
            return True
    def cleanup(self):
        """
        Clean up any remaining test files and directories.
        Note: Individual test cleanups are now done after each test for better isolation.
        This method handles any remaining cleanup in case of errors.
        """
        self.log("Starting final cleanup...", "INFO")
        
        cleanup_needed = False
        
        # Cleanup DD test files if they still exist
        if not self.skip_dd and hasattr(self, 'dd_tool'):
            try:
                if self.dd_tool.test_dir.exists() or any(self.mount_path.glob("dd_test_*")):
                    self.dd_tool.cleanup()
                    self._clear_cache()
                    cleanup_needed = True
            except Exception as e:
                self.log(f"Error during DD cleanup: {e}", "WARNING")
        
        # Cleanup FIO test directory if it still exists
        if not self.skip_fio and hasattr(self, 'fio_tool'):
            try:
                if self.fio_tool.test_dir.exists():
                    self.fio_tool.cleanup()
                    self._clear_cache()
                    cleanup_needed = True
            except Exception as e:
                self.log(f"Error during FIO cleanup: {e}", "WARNING")
        
        # Cleanup IOzone test directory if it still exists
        if not self.skip_iozone and hasattr(self, 'iozone_tool'):
            try:
                if self.iozone_tool.test_dir.exists():
                    self.iozone_tool.cleanup()
                    self._clear_cache()
                    cleanup_needed = True
            except Exception as e:
                self.log(f"Error during IOzone cleanup: {e}", "WARNING")
        
        # Cleanup Bonnie++ test directory if it still exists
        if not self.skip_bonnie and hasattr(self, 'bonnie_tool'):
            try:
                if self.bonnie_tool.test_dir.exists():
                    self.bonnie_tool.cleanup()
                    self._clear_cache()
                    cleanup_needed = True
            except Exception as e:
                self.log(f"Error during Bonnie++ cleanup: {e}", "WARNING")
        
        # Cleanup dbench test directory if it still exists
        if not self.skip_dbench and hasattr(self, 'dbench_tool'):
            try:
                if self.dbench_tool.test_dir.exists():
                    self.dbench_tool.cleanup()
                    self._clear_cache()
                    cleanup_needed = True
            except Exception as e:
                self.log(f"Error during dbench cleanup: {e}", "WARNING")
        
        if cleanup_needed:
            self.log("✓ Final cleanup completed", "SUCCESS")
        else:
            self.log("✓ No cleanup needed (already cleaned after each test)", "SUCCESS")
    
    def run_dd_tests(self):
        """Run DD performance tests using DDTestTool"""
        if self.skip_dd:
            self.log("Skipping DD tests", "INFO")
            return
        
        # Run tests using the DD tool
        dd_results = self.dd_tool.run_tests()
        
        # Store results and update summary
        self.results["dd_tests"] = dd_results
        
        # Update summary statistics
        for test_name, test_data in dd_results.items():
            if test_data.get('status') == 'passed':
                self.results["summary"]["tests_passed"] += 1
            elif test_data.get('status') == 'failed':
                self.results["summary"]["tests_failed"] += 1
                error_msg = f"DD {test_name} failed: {test_data.get('error', 'Unknown error')}"
                self.results["summary"]["errors"].append(error_msg)
            
            # Collect validation results
            validation = test_data.get('validation')
            if validation and validation.get('severity') in ['error', 'warning']:
                self.results["summary"]["performance_validation"].append({
                    'test': test_name,
                    'type': 'dd',
                    'validation': validation
                })
    
    
    def run_fio_tests(self):
        """Run FIO performance tests using FIOTestTool"""
        if self.skip_fio:
            self.log("Skipping FIO tests", "INFO")
            return
        
        # Run tests using the FIO tool
        fio_results = self.fio_tool.run_tests()
        
        # Store results and update summary
        self.results["fio_tests"] = fio_results
        
        # Update summary statistics
        for test_name, test_data in fio_results.items():
            if test_data.get('status') == 'passed':
                self.results["summary"]["tests_passed"] += 1
            elif test_data.get('status') == 'failed':
                self.results["summary"]["tests_failed"] += 1
                error_msg = f"FIO {test_name} failed: {test_data.get('error', 'Unknown error')}"
                self.results["summary"]["errors"].append(error_msg)
    
    
    def run_iozone_tests(self):
        """Run IOzone performance tests using IOzoneTestTool"""
        if self.skip_iozone:
            self.log("Skipping IOzone tests", "INFO")
            return
        
        # Run tests using the IOzone tool
        iozone_results = self.iozone_tool.run_tests()
        
        # Store results and update summary
        self.results["iozone_tests"] = iozone_results
        
        # Update summary statistics
        for test_name, test_data in iozone_results.items():
            if test_data.get('status') == 'passed':
                self.results["summary"]["tests_passed"] += 1
            elif test_data.get('status') == 'failed':
                self.results["summary"]["tests_failed"] += 1
                error_msg = f"IOzone {test_name} failed: {test_data.get('error', 'Unknown error')}"
                self.results["summary"]["errors"].append(error_msg)
            
            # Collect validation results
            for validation_key in ['write_validation', 'read_validation']:
                validation = test_data.get(validation_key)
                if validation and validation.get('severity') in ['error', 'warning']:
                    self.results["summary"]["performance_validation"].append({
                        'test': test_name,
                        'type': 'iozone',
                        'validation': validation
                    })
    
    def run_bonnie_tests(self):
        """Run Bonnie++ performance tests using BonnieTestTool"""
        if self.skip_bonnie:
            self.log("Skipping Bonnie++ tests", "INFO")
            return
        
        # Run tests using the Bonnie++ tool
        bonnie_results = self.bonnie_tool.run_tests()
        
        # Store results and update summary
        self.results["bonnie_tests"] = bonnie_results
        
        # Update summary statistics
        for test_name, test_data in bonnie_results.items():
            if test_data.get('status') == 'passed':
                self.results["summary"]["tests_passed"] += 1
            elif test_data.get('status') == 'failed':
                self.results["summary"]["tests_failed"] += 1
                error_msg = f"Bonnie++ {test_name} failed: {test_data.get('error', 'Unknown error')}"
                self.results["summary"]["errors"].append(error_msg)
            
            # Collect validation results
            validation = test_data.get('network_validation')
            if validation and validation.get('severity') in ['error', 'warning']:
                self.results["summary"]["performance_validation"].append({
                    'test': test_name,
                    'type': 'bonnie',
                    'validation': validation
                })
    
    def run_dbench_tests(self):
        """Run dbench performance tests using DBenchTestTool"""
        if self.skip_dbench:
            self.log("Skipping dbench tests", "INFO")
            return
        
        # Check if dbench tests are enabled in config
        if not self.config.get('dbench_tests', {}).get('enabled', True):
            self.log("dbench tests disabled in configuration", "INFO")
            return
        
        # Validate dbench tool availability
        if not self.dbench_tool.validate_tool():
            self.log("dbench tool not available, skipping tests", "WARNING")
            return
        
        # Run tests using the dbench tool
        dbench_results = self.dbench_tool.run_tests()
        
        # Store results and update summary
        self.results["dbench_tests"] = dbench_results
        
        # Update summary statistics
        for test_name, test_data in dbench_results.items():
            if test_data.get('status') == 'passed':
                self.results["summary"]["tests_passed"] += 1
            elif test_data.get('status') == 'failed':
                self.results["summary"]["tests_failed"] += 1
                error_msg = f"dbench {test_name} failed: {test_data.get('error', 'Unknown error')}"
                self.results["summary"]["errors"].append(error_msg)
            
            # Collect validation results
            validation = test_data.get('network_validation')
            if validation and validation.get('severity') in ['error', 'warning']:
                self.results["summary"]["performance_validation"].append({
                    'test': test_name,
                    'type': 'dbench',
                    'validation': validation
                })
    
    
    def save_results(self):
        """Save results to JSON file"""
        self.results["summary"]["total_duration"] = round(time.time() - self.start_time, 2)
        
        try:
            with open(self.output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            self.log(f"Results saved to: {self.output_file}", "SUCCESS")
        except Exception as e:
            self.log(f"Failed to save results: {e}", "ERROR")
    
    def print_summary(self):
        """Print test summary to console"""
        print("\n" + "=" * 80)
        print(f"{Colors.BOLD}{Colors.HEADER}NFS Benchmark Suite Summary{Colors.ENDC}")
        print("=" * 80)
        
        print(f"\n{Colors.BOLD}Test Run Information:{Colors.ENDC}")
        print(f"  Timestamp: {self.results['test_run']['timestamp']}")
        print(f"  Mount Path: {self.results['test_run']['mount_path']}")
        print(f"  Hostname: {self.results['test_run']['hostname']}")
        print(f"  Total Duration: {self.results['summary']['total_duration']}s")
        
        # Network Configuration Summary
        network_config = self.results['test_run'].get('network_config', {})
        if network_config:
            print(f"\n{Colors.BOLD}Network Configuration:{Colors.ENDC}")
            print(f"  NFS Server: {network_config.get('nfs_server_ip', 'unknown')}")
            print(f"  Local IP: {network_config.get('local_ip', 'unknown')}")
            print(f"  Interface: {network_config.get('interface', 'unknown')}")
            
            interface_details = network_config.get('interface_details', {})
            if interface_details.get('speed_mbps'):
                speed_gbps = interface_details['speed_mbps'] / 1000
                print(f"  Network Speed: {speed_gbps:.1f} Gbps")
            
            max_throughput = network_config.get('theoretical_max_throughput_mbps')
            if max_throughput:
                print(f"  Theoretical Max Throughput: {max_throughput:.1f} MB/s")
        
        # DD Tests Summary
        if self.results['dd_tests']:
            print(f"\n{Colors.BOLD}DD Tests:{Colors.ENDC}")
            for test_name, data in self.results['dd_tests'].items():
                if data.get('status') == 'passed':
                    throughput = data.get('throughput_mbps', 0)
                    duration = data.get('duration_seconds', 0)
                    print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {test_name}: {throughput:.2f} MB/s ({duration:.2f}s)")
                    
                    # Show interface stats if available
                    sys_metrics = data.get('system_metrics', {})
                    if_stats = sys_metrics.get('interface_stats')
                    if if_stats:
                        print(f"      Interface {if_stats['interface']}: "
                              f"TX {if_stats['throughput']['sent_mbps']:.1f} MB/s, "
                              f"RX {if_stats['throughput']['recv_mbps']:.1f} MB/s, "
                              f"Errors: {if_stats['errors']['total']}, "
                              f"Drops: {if_stats['drops']['total']}")
                else:
                    print(f"  {Colors.FAIL}✗{Colors.ENDC} {test_name}: FAILED")
        
        # FIO Tests Summary
        if self.results['fio_tests']:
            print(f"\n{Colors.BOLD}FIO Tests:{Colors.ENDC}")
            for test_name, data in self.results['fio_tests'].items():
                if data.get('status') == 'passed':
                    read_iops = data.get('read_iops', 0)
                    write_iops = data.get('write_iops', 0)
                    print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {test_name}:")
                    print(f"      Read IOPS: {read_iops:.2f}, Write IOPS: {write_iops:.2f}")
                    
                    # Show interface stats if available
                    sys_metrics = data.get('system_metrics', {})
                    if_stats = sys_metrics.get('interface_stats')
                    if if_stats:
                        print(f"      Interface {if_stats['interface']}: "
                              f"TX {if_stats['throughput']['sent_mbps']:.1f} MB/s, "
                              f"RX {if_stats['throughput']['recv_mbps']:.1f} MB/s, "
                              f"Errors: {if_stats['errors']['total']}, "
                              f"Drops: {if_stats['drops']['total']}")
                else:
                    print(f"  {Colors.FAIL}✗{Colors.ENDC} {test_name}: FAILED")
        
        # Performance Validation Summary
        validations = self.results['summary'].get('performance_validation', [])
        if validations:
            print(f"\n{Colors.BOLD}Performance Validation:{Colors.ENDC}")
            for val in validations:
                test_name = val.get('test', 'unknown')
                validation = val.get('validation', {})
                severity = validation.get('severity', 'info')
                message = validation.get('message', '')
                utilization = validation.get('utilization_pct', 0)
                
                if severity == 'error':
                    print(f"  {Colors.FAIL}✗{Colors.ENDC} {test_name}: {message}")
                elif severity == 'warning':
                    print(f"  {Colors.WARNING}⚠{Colors.ENDC} {test_name}: {message}")
                else:
                    print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {test_name}: {message}")
        
        # Overall Summary
        print(f"\n{Colors.BOLD}Overall Results:{Colors.ENDC}")
        passed = self.results['summary']['tests_passed']
        failed = self.results['summary']['tests_failed']
        total = passed + failed
        
        print(f"  Total Tests: {total}")
        print(f"  {Colors.OKGREEN}Passed: {passed}{Colors.ENDC}")
        if failed > 0:
            print(f"  {Colors.FAIL}Failed: {failed}{Colors.ENDC}")
        
        # Errors
        if self.results['summary']['errors']:
            print(f"\n{Colors.BOLD}{Colors.FAIL}Errors:{Colors.ENDC}")
            for error in self.results['summary']['errors']:
                print(f"  - {error}")
        
        print(f"\n{Colors.BOLD}Output Files:{Colors.ENDC}")
        print(f"  JSON Results: {Colors.OKCYAN}{os.path.abspath(self.output_file)}{Colors.ENDC}")
        print(f"  Log File: {Colors.OKCYAN}{os.path.abspath(self.log_file)}{Colors.ENDC}")
        print("=" * 80 + "\n")
    
    def _collect_nfs_stats(self):
        """Collect NFS client statistics using nfsstat command"""
        monitoring_config = self.config.get('monitoring', {})
        if not isinstance(monitoring_config, dict):
            return {}
        
        if not monitoring_config.get('nfs_stats_enabled', True):
            return {}
        
        try:
            # Check if nfsstat command is available
            if not self._check_command('nfsstat'):
                self.log("nfsstat command not available, skipping NFS stats collection", "WARNING")
                return {}
            
            # Get NFS client statistics
            result = run_command_with_timeout(
                ['nfsstat', '-c'],
                timeout=10,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {}
            
            # Parse nfsstat output
            stats = self._parse_nfsstat_output(result.stdout)
            
            return stats
            
        except subprocess.TimeoutExpired:
            self.log("nfsstat command timed out", "WARNING")
            return {}
        except Exception as e:
            self.log(f"Failed to collect NFS stats: {e}", "WARNING")
            return {}
    
    def _parse_nfsstat_output(self, output):
        """Parse nfsstat command output
        
        Args:
            output: nfsstat command output
            
        Returns:
            dict: Parsed NFS statistics
        """
        stats = {
            'nfs_version': 'unknown',
            'operations': {},
            'rpc_stats': {}
        }
        
        try:
            lines = output.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                # Detect NFS version
                if 'nfs v3' in line.lower() or 'nfs v4' in line.lower():
                    if 'v3' in line.lower():
                        stats['nfs_version'] = 'NFSv3'
                    elif 'v4' in line.lower():
                        stats['nfs_version'] = 'NFSv4'
                
                # Parse operation counts
                if line and not line.startswith('-') and current_section == 'operations':
                    parts = line.split()
                    # Format: operation_name count percentage
                    if len(parts) >= 2:
                        try:
                            op_name = parts[0]
                            op_count = int(parts[1])
                            stats['operations'][op_name] = op_count
                        except (ValueError, IndexError):
                            pass
                
                # Detect sections
                if 'Client rpc stats' in line or 'RPC statistics' in line:
                    current_section = 'rpc'
                elif 'Client nfs' in line or 'NFS statistics' in line:
                    current_section = 'operations'
            
            return stats
            
        except Exception:
            return stats
    
    def _warmup_test(self):
        """Perform warm-up run to stabilize performance"""
        execution_config = self.config.get('execution', {})
        if not isinstance(execution_config, dict):
            return
        
        warmup_config = execution_config.get('warmup', {})
        if not isinstance(warmup_config, dict):
            return
        
        if not warmup_config.get('enabled', False):
            return
        
        self.log("=" * 60, "INFO")
        self.log("Running warm-up test to stabilize performance...", "INFO")
        self.log("=" * 60, "INFO")
        
        warmup_file = self.mount_path / "warmup_test"
        warmup_size_mb = warmup_config.get('size_mb', 1000)  # Default 1GB
        
        try:
            # Small write cycle
            self.log(f"Warm-up: Writing {warmup_size_mb}MB...", "INFO")
            write_cmd = [
                'dd', 'if=/dev/zero', f'of={warmup_file}',
                'bs=1M', f'count={warmup_size_mb}', 'oflag=direct'
            ]
            run_command_with_timeout(write_cmd, timeout=120, capture_output=True, check=True)
            
            # Small read cycle
            self.log(f"Warm-up: Reading {warmup_size_mb}MB...", "INFO")
            read_cmd = [
                'dd', f'if={warmup_file}', 'of=/dev/null',
                'bs=1M', 'iflag=direct'
            ]
            run_command_with_timeout(read_cmd, timeout=120, capture_output=True, check=True)
            
            # Cleanup warm-up file
            warmup_file.unlink()
            
            self.log("Warm-up completed successfully", "SUCCESS")
            self.log("=" * 60, "INFO")
            
        except subprocess.TimeoutExpired:
            self.log("Warm-up timed out (this is not critical)", "WARNING")
            if warmup_file.exists():
                warmup_file.unlink()
        except Exception as e:
            self.log(f"Warm-up failed: {e} (continuing with tests)", "WARNING")
            if warmup_file.exists():
                warmup_file.unlink()
    
    def _clear_cache(self):
        """Clear system cache before tests"""
        try:
            self.log("Clearing system cache...", "INFO")
            # Sync to flush file system buffers
            run_sync(timeout=30)
            # Drop caches (requires root/sudo)
            result = run_command_with_timeout(
                ['sudo', '-n', 'sh', '-c', 'echo 3 > /proc/sys/vm/drop_caches'],
                timeout=10,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.log("System cache cleared successfully", "SUCCESS")
            else:
                self.log("Warning: Could not clear cache (requires sudo). Results may be affected by cache.", "WARNING")
        except Exception as e:
            self.log(f"Warning: Could not clear cache: {e}. Results may be affected by cache.", "WARNING")
    
    def run(self):
        """Main execution method"""
        if not self.validate_environment():
            sys.exit(1)
        
        if self.cleanup_only:
            self.cleanup()
            return
        
        try:
            # Clear system cache before tests
            self._clear_cache()
            
            # Collect NFS stats before tests
            nfs_stats_before = self._collect_nfs_stats()
            if nfs_stats_before:
                self.results['nfs_stats'] = {'before_tests': nfs_stats_before}
            
            # Run warm-up if enabled
            self._warmup_test()
            
            # Run tests with cleanup and cache clearing after each tool for proper isolation
            self.run_dd_tests()
            if not self.skip_dd:
                self.dd_tool.cleanup()
                self._clear_cache()
            
            self.run_fio_tests()
            if not self.skip_fio:
                self.fio_tool.cleanup()
                self._clear_cache()
            
            self.run_iozone_tests()
            if not self.skip_iozone:
                self.iozone_tool.cleanup()
                self._clear_cache()
            
            self.run_bonnie_tests()
            if not self.skip_bonnie:
                self.bonnie_tool.cleanup()
                self._clear_cache()
            
            self.run_dbench_tests()
            if not self.skip_dbench:
                self.dbench_tool.cleanup()
                self._clear_cache()
            
            # Collect NFS stats after tests
            nfs_stats_after = self._collect_nfs_stats()
            if nfs_stats_after:
                if 'nfs_stats' not in self.results:
                    self.results['nfs_stats'] = {}
                self.results['nfs_stats']['after_tests'] = nfs_stats_after
            
            # Save results
            self.save_results()
            
            # Print summary
            self.print_summary()
            
        except KeyboardInterrupt:
            self.log("\nTest interrupted by user", "WARNING")
            self.save_results()
            self.print_summary()
            sys.exit(1)
        except Exception as e:
            self.log(f"Unexpected error: {e}", "ERROR")
            self.save_results()
            sys.exit(1)
        finally:
            # Always cleanup
            self.cleanup()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='NFS Benchmark Suite Script with Configurable Parameters',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run quick test profile (~15 minutes)
  python3 runtest.py --mount-path /mnt/nfs1 --quick-test
  
  # Run long test profile (~60 minutes)
  python3 runtest.py --mount-path /mnt/nfs1 --long-test
  
  # Run all tests with default config
  python3 runtest.py --mount-path /mnt/nfs1
  
  # Run with custom configuration
  python3 runtest.py --mount-path /mnt/nfs1 --config my_config.yaml
  
  # Skip DD tests
  python3 runtest.py --mount-path /mnt/nfs1 --skip-dd
  
  # Skip FIO tests
  python3 runtest.py --mount-path /mnt/nfs1 --skip-fio
  
  # Skip IOzone tests
  python3 runtest.py --mount-path /mnt/nfs1 --skip-iozone
  
  # Skip Bonnie++ tests
  python3 runtest.py --mount-path /mnt/nfs1 --skip-bonnie
  
  # Skip dbench tests
  python3 runtest.py --mount-path /mnt/nfs1 --skip-dbench
  
  # Cleanup only
  python3 runtest.py --mount-path /mnt/nfs1 --cleanup-only
  
  # Verbose mode
  python3 runtest.py --mount-path /mnt/nfs1 --verbose

Test Profiles:
  --quick-test: Reduced file sizes and shorter runtimes (~15 minutes)
  --long-test:  Full-scale testing with comprehensive coverage (~60 minutes)

Configuration:
  Edit test_config.yaml to customize test parameters including:
  - Block sizes, file sizes, and test durations
  - Number of parallel jobs and queue depths
  - I/O engines and flags
  - Enable/disable individual tests
        """
    )
    
    parser.add_argument(
        '--mount-path',
        required=True,
        help='NFS mount path (e.g., /mnt/nfs1)'
    )
    
    parser.add_argument(
        '--config',
        default=None,
        help='Path to custom configuration file (default: test_config.yaml)'
    )
    
    parser.add_argument(
        '--skip-dd',
        action='store_true',
        help='Skip DD tests'
    )
    
    parser.add_argument(
        '--skip-fio',
        action='store_true',
        help='Skip FIO tests'
    )
    
    parser.add_argument(
        '--skip-iozone',
        action='store_true',
        help='Skip IOzone tests'
    )
    
    parser.add_argument(
        '--skip-bonnie',
        action='store_true',
        help='Skip Bonnie++ tests'
    )
    
    parser.add_argument(
        '--skip-dbench',
        action='store_true',
        help='Skip dbench tests'
    )
    
    parser.add_argument(
        '--cleanup-only',
        action='store_true',
        help='Only perform cleanup of test files'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--quick-test',
        action='store_true',
        help='Run quick test profile (~15 minutes, uses config_quick_test.yaml)'
    )
    
    parser.add_argument(
        '--long-test',
        action='store_true',
        help='Run long test profile (~60 minutes, uses config_long_test.yaml)'
    )
    
    parser.add_argument(
        '--no-save-history',
        action='store_true',
        help='Do not save results to history (for testing/debugging)'
    )
    
    args = parser.parse_args()
    
    # Determine config file based on test profile
    config_file = args.config
    if args.quick_test and args.long_test:
        print("❌ Error: Cannot specify both --quick-test and --long-test")
        print("  Choose one test profile:")
        print("  • --quick-test: Fast tests (~15 minutes)")
        print("  • --long-test: Comprehensive tests (~60 minutes)")
        print("  • Or use default configuration")
        sys.exit(1)
    elif args.quick_test:
        config_file = Path(__file__).parent / "config" / "config_quick_test.yaml"
        print(f"Using quick test profile: config/config_quick_test.yaml")
    elif args.long_test:
        config_file = Path(__file__).parent / "config" / "config_long_test.yaml"
        print(f"Using long test profile: config/config_long_test.yaml")
    
    # Validate mount path and configuration
    print("\n" + "=" * 60)
    print("Validating inputs...")
    print("=" * 60)
    
    try:
        # Determine minimum space based on test profile
        min_space_gb = 50.0 if args.quick_test else 100.0
        
        # Validate mount path and config
        validated_path, mount_info, validated_config = validate_mount_and_config(
            args.mount_path,
            str(config_file) if config_file else None,
            min_space_gb=min_space_gb
        )
        
        # Print validation results
        print(f"✅ Mount path validated: {validated_path}")
        print(f"  • NFS Server: {mount_info.get('server', 'unknown')}")
        print(f"  • Mount Point: {mount_info.get('mount_point', 'unknown')}")
        print(f"  • Free Space: {mount_info.get('free_space_gb', 0):.1f}GB")
        print(f"  • Total Space: {mount_info.get('total_space_gb', 0):.1f}GB")
        print(f"  • Used: {mount_info.get('used_percent', 0):.1f}%")
        
        if validated_config:
            print(f"✅ Configuration validated: {config_file}")
        
        print("=" * 60 + "\n")
        
    except ValidationError as e:
        print(f"\n{e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed: {e}\n")
        sys.exit(1)
    
    # Create and run test
    test = NFSPerformanceTest(
        mount_path=str(validated_path),
        config_file=config_file,
        skip_dd=args.skip_dd,
        skip_fio=args.skip_fio,
        skip_iozone=args.skip_iozone,
        skip_bonnie=args.skip_bonnie,
        skip_dbench=args.skip_dbench,
        cleanup_only=args.cleanup_only,
        verbose=args.verbose
    )
    
    test.run()
    
    # Save to historical data (if not cleanup-only)
    if not args.cleanup_only and not args.no_save_history:
        try:
            hist = HistoricalComparison()
            timestamp = hist.save_result(test.results)
            print(f"\n✅ Results saved to history: {timestamp}")
            print(f"   Use generate_html_report.py to view historical comparison")
        except Exception as e:
            print(f"\n⚠️  Failed to save to history: {e}")
            print("   Test results are still saved to JSON file")


if __name__ == '__main__':
    main()

# Made with Bob
