#!/usr/bin/env python3
"""
IOzone Test Tool for NFS Benchmark Suite

This module implements the IOzoneTestTool class for running IOzone
performance tests on NFS mounts. IOzone is a filesystem benchmark tool
that generates and measures a variety of file operations.
"""

import subprocess
import re
import time
from pathlib import Path
from typing import Dict, Any, List

from .core import BaseTestTool


class IOzoneTestTool(BaseTestTool):
    """
    IOzone test tool implementation.
    
    Performs comprehensive filesystem I/O tests including:
    - Baseline throughput (sequential read/write with direct I/O)
    - Cache behavior analysis (read without direct I/O)
    - Random I/O performance (4k random read/write)
    - Concurrency testing (16 threads)
    - Metadata operations (32 threads, 4k blocks)
    - Scaling tests (4, 8, 16, 32 threads)
    - Mixed workload (sequential + random)
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        mount_path: Path,
        logger,
        metrics_collector=None,
        nfs_metrics_collector=None,
        network_intel=None
    ):
        """
        Initialize IOzone test tool.
        
        Args:
            config: IOzone test configuration
            mount_path: NFS mount path
            logger: Logger instance
            metrics_collector: Optional metrics collector
            nfs_metrics_collector: Optional NFS metrics collector
            network_intel: Optional network intelligence
        """
        super().__init__("iozone", config, mount_path, logger, metrics_collector, nfs_metrics_collector, network_intel)
        
        # Test directory
        self.test_dir = self.mount_path / "iozone_test"
        
        # Results storage
        self.results = {}
    
    def validate_tool(self) -> bool:
        """
        Validate that iozone command is available.
        
        Returns:
            bool: True if iozone is available
        """
        if not self._check_command("iozone"):
            self.log("❌ iozone command not found", "ERROR")
            self.log("  iozone is required for file system I/O testing", "ERROR")
            self.log("", "ERROR")
            self.log("  Quick Fix:", "ERROR")
            self.log("  • Run: ./setup_and_verify.sh --auto", "ERROR")
            self.log("", "ERROR")
            self.log("  Manual Installation:", "ERROR")
            self.log("  • Ubuntu/Debian: sudo apt-get install iozone", "ERROR")
            self.log("  • RHEL/CentOS: sudo yum install iozone", "ERROR")
            self.log("  Verify installation: iozone -v", "ERROR")
            return False
        return True
    
    def run_tests(self) -> Dict[str, Any]:
        """
        Run all IOzone tests.
        
        Returns:
            dict: Test results for all IOzone tests
        """
        self.log("=" * 60, "INFO")
        self.log("Starting IOzone Tests", "INFO")
        self.log("=" * 60, "INFO")
        
        # Create test directory
        self.test_dir.mkdir(exist_ok=True)
        
        # Run all IOzone tests
        self._iozone_baseline_throughput()
        self._iozone_cache_behavior()
        self._iozone_random_io()
        self._iozone_concurrency()
        self._iozone_metadata_ops()
        self._iozone_scaling_test()
        self._iozone_mixed_workload()
        
        return self.results
    
    def cleanup(self):
        """Clean up IOzone test directory with verification."""
        self.log("Cleaning up IOzone test directory...", "INFO")
        
        if self.test_dir.exists():
            if self._safe_remove_path(self.test_dir, is_directory=True):
                self.log("IOzone cleanup completed successfully", "SUCCESS")
            else:
                self.log("IOzone cleanup completed with warnings", "WARNING")
        else:
            self.log("IOzone test directory does not exist (already cleaned)", "SUCCESS")
    
    def _build_iozone_command(self, test_config: Dict[str, Any]) -> List[str]:
        """
        Build IOzone command from configuration.
        
        Args:
            test_config: Test-specific configuration
            
        Returns:
            list: IOzone command with parameters
        """
        cmd = ['iozone']
        
        # Add automatic mode flag
        if test_config.get('auto_mode', False):
            cmd.append('-a')
        
        # Add test type flags
        test_types = test_config.get('test_types', [])
        for test_type in test_types:
            cmd.append(f'-i {test_type}')
        
        # File size
        if 'file_size' in test_config:
            cmd.extend(['-s', test_config['file_size']])
        
        # Record size (block size)
        if 'record_size' in test_config:
            cmd.extend(['-r', test_config['record_size']])
        
        # Number of threads
        threads = test_config.get('threads')
        if threads:
            cmd.extend(['-t', str(threads)])
        
        # Direct I/O
        if test_config.get('direct_io', False):
            cmd.append('-I')
        
        # Throughput mode
        if test_config.get('throughput_mode', False):
            cmd.append('-+n')
        
        # Include flush/close in timing
        if test_config.get('include_close', False):
            cmd.append('-e')
        
        # Output format
        if test_config.get('excel_output', False):
            cmd.append('-b')
            output_file = self.test_dir / f"{test_config.get('name', 'test')}.xls"
            cmd.append(str(output_file))
        
        # File specification: use -F for multiple threads, -f for single thread
        if threads and threads > 1:
            # Multiple threads require -F with one file per thread
            cmd.append('-F')
            for i in range(threads):
                cmd.append(str(self.test_dir / f'iozone.tmp.{i}'))
        else:
            # Single thread uses -f with one file
            cmd.extend(['-f', str(self.test_dir / 'iozone.tmp')])
        
        return cmd
    
    def _iozone_baseline_throughput(self):
        """
        Test 1: Baseline throughput (sequential read/write with direct I/O).
        
        This test measures raw sequential I/O performance with direct I/O
        to bypass caching and get true NFS performance.
        """
        test_name = "baseline_throughput"
        self.log(f"Running IOzone {test_name} test...", "INFO")
        
        # Get test configuration
        test_config = self.config.get(test_name, {})
        if not isinstance(test_config, dict):
            test_config = {}
        
        # Set defaults for baseline test
        test_config.setdefault('name', test_name)
        test_config.setdefault('test_types', [0, 1])  # 0=write, 1=read
        test_config.setdefault('file_size', '4g')
        test_config.setdefault('record_size', '1m')
        test_config.setdefault('direct_io', True)
        test_config.setdefault('include_close', True)
        
        cmd = self._build_iozone_command(test_config)
        self._run_iozone_test(test_name, cmd, test_config)
    
    def _iozone_cache_behavior(self):
        """
        Test 2: Cache behavior (read without direct I/O).
        
        This test measures the impact of caching on read performance
        by running reads without direct I/O flag.
        """
        test_name = "cache_behavior"
        self.log(f"Running IOzone {test_name} test...", "INFO")
        
        test_config = self.config.get(test_name, {})
        if not isinstance(test_config, dict):
            test_config = {}
        
        test_config.setdefault('name', test_name)
        test_config.setdefault('test_types', [0, 1])  # 0=write, 1=read (need write first to create file)
        test_config.setdefault('file_size', '2g')
        test_config.setdefault('record_size', '1m')
        test_config.setdefault('direct_io', False)  # No direct I/O to test cache
        
        cmd = self._build_iozone_command(test_config)
        self._run_iozone_test(test_name, cmd, test_config)
    
    def _iozone_random_io(self):
        """
        Test 3: Random I/O (4k random read/write).
        
        This test measures random I/O performance with 4KB blocks,
        which is typical for database and small file workloads.
        """
        test_name = "random_io_4k"
        self.log(f"Running IOzone {test_name} test...", "INFO")
        
        test_config = self.config.get(test_name, {})
        if not isinstance(test_config, dict):
            test_config = {}
        
        test_config.setdefault('name', test_name)
        test_config.setdefault('test_types', [0, 2, 4])  # 0=write first, then 2=random read, 4=random write
        test_config.setdefault('file_size', '1g')
        test_config.setdefault('record_size', '4k')
        test_config.setdefault('direct_io', True)
        
        cmd = self._build_iozone_command(test_config)
        self._run_iozone_test(test_name, cmd, test_config)
    
    def _iozone_concurrency(self):
        """
        Test 4: Concurrency (16 threads).
        
        This test measures performance with multiple concurrent threads
        to simulate multi-user or multi-process workloads.
        """
        test_name = "concurrency_16_threads"
        self.log(f"Running IOzone {test_name} test...", "INFO")
        
        test_config = self.config.get(test_name, {})
        if not isinstance(test_config, dict):
            test_config = {}
        
        test_config.setdefault('name', test_name)
        test_config.setdefault('test_types', [0, 1])  # write and read
        test_config.setdefault('file_size', '1g')
        test_config.setdefault('record_size', '1m')
        test_config.setdefault('threads', 16)
        test_config.setdefault('direct_io', True)
        test_config.setdefault('throughput_mode', True)
        
        cmd = self._build_iozone_command(test_config)
        self._run_iozone_test(test_name, cmd, test_config)
    
    def _iozone_metadata_ops(self):
        """
        Test 5: Metadata operations (32 threads, 4k blocks).
        
        This test focuses on metadata-intensive operations with many
        small files, simulating workloads with frequent file operations.
        """
        test_name = "metadata_operations"
        self.log(f"Running IOzone {test_name} test...", "INFO")
        
        test_config = self.config.get(test_name, {})
        if not isinstance(test_config, dict):
            test_config = {}
        
        test_config.setdefault('name', test_name)
        test_config.setdefault('test_types', [0, 1])  # write and read
        test_config.setdefault('file_size', '64m')  # Smaller files
        test_config.setdefault('record_size', '4k')
        test_config.setdefault('threads', 32)
        test_config.setdefault('direct_io', False)  # Metadata ops don't need direct I/O
        test_config.setdefault('throughput_mode', True)
        
        cmd = self._build_iozone_command(test_config)
        self._run_iozone_test(test_name, cmd, test_config)
    
    def _iozone_scaling_test(self):
        """
        Test 6: Scaling test (4, 8, 16, 32 threads).
        
        This test measures how performance scales with increasing
        thread count to identify optimal concurrency levels.
        """
        test_name = "scaling_test"
        self.log(f"Running IOzone {test_name} test...", "INFO")
        
        test_config = self.config.get(test_name, {})
        if not isinstance(test_config, dict):
            test_config = {}
        
        thread_counts = test_config.get('thread_counts', [4, 8, 16, 32])
        
        scaling_results = {}
        
        for thread_count in thread_counts:
            sub_test_name = f"{test_name}_{thread_count}_threads"
            self.log(f"  Testing with {thread_count} threads...", "INFO")
            
            sub_config = test_config.copy()
            sub_config['name'] = sub_test_name
            sub_config.setdefault('test_types', [0, 1])
            sub_config.setdefault('file_size', '512m')
            sub_config.setdefault('record_size', '1m')
            sub_config['threads'] = thread_count
            sub_config.setdefault('direct_io', True)
            sub_config.setdefault('throughput_mode', True)
            
            cmd = self._build_iozone_command(sub_config)
            result = self._run_iozone_test(sub_test_name, cmd, sub_config, store_separately=False)
            
            if result:
                scaling_results[f"{thread_count}_threads"] = result
        
        # Store combined scaling results
        if scaling_results:
            self.results[test_name] = {
                "status": "passed",
                "scaling_results": scaling_results
            }
            self.log(f"IOzone {test_name} completed successfully", "SUCCESS")
    
    def _iozone_mixed_workload(self):
        """
        Test 7: Mixed workload (sequential + random).
        
        This test runs a combination of sequential and random operations
        to simulate real-world mixed workload patterns.
        """
        test_name = "mixed_workload"
        self.log(f"Running IOzone {test_name} test...", "INFO")
        
        test_config = self.config.get(test_name, {})
        if not isinstance(test_config, dict):
            test_config = {}
        
        test_config.setdefault('name', test_name)
        # 0=write, 1=read, 2=random read, 4=random write
        test_config.setdefault('test_types', [0, 1, 2, 4])
        test_config.setdefault('file_size', '2g')
        test_config.setdefault('record_size', '128k')
        test_config.setdefault('threads', 8)
        test_config.setdefault('direct_io', True)
        test_config.setdefault('throughput_mode', True)
        
        cmd = self._build_iozone_command(test_config)
        self._run_iozone_test(test_name, cmd, test_config)
    
    def _run_iozone_test(self, test_name: str, cmd: List[str], test_config: Dict[str, Any], store_separately: bool = True) -> Dict[str, Any]:
        """
        Run an IOzone test and parse results.
        
        Args:
            test_name: Name of the test
            cmd: IOzone command to execute
            test_config: Test configuration
            store_separately: Whether to store results in self.results
            
        Returns:
            dict: Test results
        """
        # Ensure test directory exists
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Start metrics collection
        self._start_metrics_collection()
        
        try:
            start = time.time()
            result = self.run_command_with_timeout(
                cmd,
                timeout=self.config.get('timeout', 1800),
                check=True,
                cwd=str(self.test_dir)
            )
            duration = time.time() - start
            
            # Stop metrics and get summary
            metrics_summary = self._stop_metrics_collection()
            
            # Parse IOzone output
            parsed_results = self._parse_iozone_output(result.stdout, test_config)
            
            # Build result dictionary
            test_result = {
                "status": "passed",
                "duration_seconds": round(duration, 2),
                "config": {
                    "file_size": test_config.get('file_size', 'N/A'),
                    "record_size": test_config.get('record_size', 'N/A'),
                    "threads": test_config.get('threads', 1),
                    "direct_io": test_config.get('direct_io', False),
                    "test_types": test_config.get('test_types', [])
                }
            }
            
            # Add parsed metrics
            test_result.update(parsed_results)
            
            # Add metrics - properly separated
            if metrics_summary:
                if 'system' in metrics_summary:
                    test_result["system_metrics"] = metrics_summary['system']
                if 'nfs' in metrics_summary:
                    test_result["nfs_metrics"] = metrics_summary['nfs']
            
            # Validate throughput if available
            if 'write_throughput_mbps' in parsed_results:
                validation = self._validate_throughput(
                    parsed_results['write_throughput_mbps'],
                    "sequential"
                )
                if validation.get('valid') is not None:
                    test_result["write_validation"] = validation
            
            if 'read_throughput_mbps' in parsed_results:
                validation = self._validate_throughput(
                    parsed_results['read_throughput_mbps'],
                    "sequential"
                )
                if validation.get('valid') is not None:
                    test_result["read_validation"] = validation
            
            if store_separately:
                self.results[test_name] = test_result
                self.log(f"IOzone {test_name} completed successfully", "SUCCESS")
            
            return test_result
            
        except subprocess.CalledProcessError as e:
            self._stop_metrics_collection()
            error_result = {
                "status": "failed",
                "error": str(e),
                "stderr": e.stderr if hasattr(e, 'stderr') else ''
            }
            
            if store_separately:
                self.results[test_name] = error_result
                self.log(f"IOzone {test_name} failed: {e}", "ERROR")
            
            return error_result
            
        except Exception as e:
            self._stop_metrics_collection()
            error_result = {
                "status": "failed",
                "error": str(e)
            }
            
            if store_separately:
                self.results[test_name] = error_result
                self.log(f"IOzone {test_name} parsing failed: {e}", "ERROR")
            
            return error_result
    
    def _parse_iozone_output(self, output: str, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse IOzone output to extract performance metrics.
        
        IOzone outputs results in a tabular format. This parser extracts
        throughput values for different operations.
        
        Args:
            output: IOzone command stdout
            test_config: Test configuration for context
            
        Returns:
            dict: Parsed metrics including throughput values
        """
        metrics = {}
        
        # IOzone output patterns
        # Looking for lines like:
        # "Children see throughput for  8 initial writers  =  1234.56 KB/sec"
        # "Children see throughput for  8 readers           =  5678.90 KB/sec"
        
        # Pattern for throughput lines
        throughput_pattern = r'Children see throughput for\s+\d+\s+(?:initial\s+)?(\w+)\s+=\s+([\d.]+)\s+(\w+)/sec'
        
        for match in re.finditer(throughput_pattern, output):
            operation = match.group(1).lower()
            value = float(match.group(2))
            unit = match.group(3).upper()
            
            # Convert to MB/s
            if unit == 'KB':
                value_mbps = value / 1024
            elif unit == 'MB':
                value_mbps = value
            elif unit == 'GB':
                value_mbps = value * 1024
            else:
                value_mbps = value
            
            # Map operation names to metric keys
            if 'writer' in operation:
                metrics['write_throughput_mbps'] = round(value_mbps, 2)
            elif 'reader' in operation or 'read' in operation:
                metrics['read_throughput_mbps'] = round(value_mbps, 2)
            elif 'rewriter' in operation:
                metrics['rewrite_throughput_mbps'] = round(value_mbps, 2)
            elif 'rereader' in operation:
                metrics['reread_throughput_mbps'] = round(value_mbps, 2)
        
        # Alternative pattern for single-threaded results
        # "  Initial write  1234.56"
        single_pattern = r'^\s+(Initial write|Read|Random read|Random write|Backward read|Record rewrite|Stride read|Fwrite|Frewrite|Fread|Freread)\s+([\d.]+)'
        
        for match in re.finditer(single_pattern, output, re.MULTILINE):
            operation = match.group(1).lower()
            value = float(match.group(2))
            
            # IOzone single-threaded output is in KB/s
            value_mbps = value / 1024
            
            if 'initial write' in operation or operation == 'fwrite':
                metrics['write_throughput_mbps'] = round(value_mbps, 2)
            elif operation == 'read' or operation == 'fread':
                metrics['read_throughput_mbps'] = round(value_mbps, 2)
            elif 'random read' in operation:
                metrics['random_read_throughput_mbps'] = round(value_mbps, 2)
            elif 'random write' in operation:
                metrics['random_write_throughput_mbps'] = round(value_mbps, 2)
            elif 'rewrite' in operation or operation == 'frewrite':
                metrics['rewrite_throughput_mbps'] = round(value_mbps, 2)
            elif 'reread' in operation or operation == 'freread':
                metrics['reread_throughput_mbps'] = round(value_mbps, 2)
        
        # If no metrics were parsed, add a note
        if not metrics:
            metrics['note'] = 'No throughput metrics found in output'
        
        return metrics

# Made with Bob