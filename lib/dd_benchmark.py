#!/usr/bin/env python3
"""
DD Test Tool for NFS Benchmark Suite

This module implements the DDTestTool class for running DD (Data Duplicator)
performance tests on NFS mounts.
"""

import subprocess
import time
import re
from pathlib import Path
from typing import Dict, Any

from .core import BaseTestTool


class DDTestTool(BaseTestTool):
    """
    DD (Data Duplicator) test tool implementation.
    
    Performs sequential read/write tests using the dd command.
    Tests include direct I/O, synchronized I/O, and cached operations.
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
        Initialize DD test tool.
        
        Args:
            config: DD test configuration
            mount_path: NFS mount path
            logger: Logger instance
            metrics_collector: Optional metrics collector
            nfs_metrics_collector: Optional NFS metrics collector
            network_intel: Optional network intelligence
        """
        super().__init__("dd", config, mount_path, logger, metrics_collector, nfs_metrics_collector, network_intel)
        
        # Test files
        self.file1 = self.mount_path / "file1"
        self.file2 = self.mount_path / "file2"
        
        # Results storage
        self.results = {}
    
    def validate_tool(self) -> bool:
        """
        Validate that dd command is available.
        
        Returns:
            bool: True if dd is available
        """
        if not self._check_command("dd"):
            self.log("❌ dd command not found", "ERROR")
            self.log("  dd is required for sequential I/O testing", "ERROR")
            self.log("", "ERROR")
            self.log("  Quick Fix:", "ERROR")
            self.log("  • Run: ./setup_and_verify.sh --auto", "ERROR")
            self.log("", "ERROR")
            self.log("  Manual Installation:", "ERROR")
            self.log("  • Ubuntu/Debian: sudo apt-get install coreutils", "ERROR")
            self.log("  • RHEL/CentOS: sudo yum install coreutils", "ERROR")
            self.log("  • macOS: dd is pre-installed", "ERROR")
            self.log("  Verify installation: which dd", "ERROR")
            return False
        return True
    
    def run_tests(self) -> Dict[str, Any]:
        """
        Run all DD tests.
        
        Returns:
            dict: Test results for all DD tests
        """
        self.log("=" * 60, "INFO")
        self.log("Starting DD Tests (Sanity Test - Fixed 5GB)", "INFO")
        self.log("=" * 60, "INFO")
        
        # Test 1: Sequential write with direct I/O
        self._dd_write_test("sequential_write_direct", self.file1, direct=True)
        
        # Test 2: Sequential write with sync
        self._dd_write_test("sequential_write_sync", self.file2, sync=True)
        
        # Test 3: Sequential read with direct I/O
        self._dd_read_test("sequential_read_direct", self.file1, direct=True)
        
        # Test 4: Sequential read cached
        self._dd_read_test("sequential_read_cached", self.file1, direct=False)
        
        # Test 5: Delete files
        self._dd_delete_test()
        
        return self.results
    
    def cleanup(self):
        """Clean up DD test files with verification."""
        self.log("Cleaning up DD test files...", "INFO")
        
        success = True
        if self.file1.exists():
            if not self._safe_remove_path(self.file1, is_directory=False):
                success = False
        
        if self.file2.exists():
            if not self._safe_remove_path(self.file2, is_directory=False):
                success = False
        
        if success:
            self.log("DD cleanup completed successfully", "SUCCESS")
        else:
            self.log("DD cleanup completed with warnings", "WARNING")
    
    def _dd_write_test(self, name: str, filepath: Path, direct: bool = False, sync: bool = False):
        """
        Perform DD write test.
        
        Args:
            name: Test name
            filepath: Path to write file
            direct: Use direct I/O (bypasses cache)
            sync: Use synchronized I/O (ensures data is written)
        """
        self.log(f"Running DD write test (sanity): {name}...", "INFO")
        
        # Start metrics collection
        self._start_metrics_collection()
        
        # Get test configuration
        test_config = self.config.get(name, {})
        if not isinstance(test_config, dict):
            test_config = {}
        
        block_size = test_config.get('block_size', '1M')
        count = test_config.get('count', 100000)
        
        # Get flags from config
        flags_config = test_config.get('flags', {})
        if isinstance(flags_config, dict):
            direct = flags_config.get('direct', direct)
            sync = flags_config.get('sync', sync)
        
        # Build command
        cmd = [
            'dd',
            'if=/dev/zero',
            f'of={filepath}',
            f'bs={block_size}',
            f'count={count}',
            'status=progress'
        ]
        
        if direct:
            cmd.append('oflag=direct')
        if sync:
            cmd.append('conv=fdatasync')
        
        try:
            start = time.time()
            result = self.run_command_with_timeout(cmd, timeout=self.config.get('timeout', 600), check=True)
            duration = time.time() - start
            
            # Stop metrics and get summary
            metrics_summary = self._stop_metrics_collection()
            
            # Parse throughput
            throughput = self._parse_dd_output(result.stderr)
            
            # Calculate size in MB
            size_mb = count if 'M' in block_size.upper() else count * int(block_size.rstrip('KkMmGg')) // 1024
            
            # Store results
            self.results[name] = {
                "status": "passed",
                "duration_seconds": round(duration, 2),
                "throughput_mbps": throughput,
                "size_mb": size_mb,
                "block_size": block_size,
                "count": count,
                "flags": {
                    "direct_io": direct,
                    "synchronized": sync
                }
            }
            
            # Add metrics - properly separated
            if metrics_summary:
                if 'system' in metrics_summary:
                    self.results[name]["system_metrics"] = metrics_summary['system']
                if 'nfs' in metrics_summary:
                    self.results[name]["nfs_metrics"] = metrics_summary['nfs']
            
            # Validate throughput
            validation = self._validate_throughput(throughput, "sequential")
            if validation.get('valid') is not None:
                self.results[name]["validation"] = validation
                
                severity = validation.get('severity', 'info')
                message = validation.get('message', '')
                
                if severity == 'error':
                    self.log(f"⚠️  {message}", "WARNING")
                elif severity == 'success':
                    self.log(f"✓ {message}", "SUCCESS")
                elif severity == 'warning':
                    self.log(f"⚠️  {message}", "WARNING")
            
            self.log(f"DD {name} completed: {throughput:.2f} MB/s in {duration:.2f}s", "SUCCESS")
            
        except subprocess.CalledProcessError as e:
            self._stop_metrics_collection()
            error_details = str(e)
            if e.stderr:
                error_details = e.stderr[:300]
            
            self.results[name] = {
                "status": "failed",
                "error": error_details
            }
            self.log(f"❌ DD {name} failed", "ERROR")
            self.log(f"  Error: {error_details}", "ERROR")
            self.log(f"  Troubleshooting:", "ERROR")
            self.log(f"  • Check available disk space: df -h {self.mount_path}", "ERROR")
            self.log(f"  • Verify write permissions: touch {self.mount_path}/test && rm {self.mount_path}/test", "ERROR")
            self.log(f"  • Check NFS mount status: mount | grep nfs", "ERROR")
            self.log(f"  • Review NFS server logs for errors", "ERROR")
    
    def _dd_read_test(self, name: str, filepath: Path, direct: bool = False):
        """
        Perform DD read test.
        
        Args:
            name: Test name
            filepath: Path to read file
            direct: Use direct I/O (bypasses cache)
        """
        self.log(f"Running DD read test (sanity): {name}...", "INFO")
        
        # Start metrics collection
        self._start_metrics_collection()
        
        # Get test configuration
        test_config = self.config.get(name, {})
        if not isinstance(test_config, dict):
            test_config = {}
        
        block_size = test_config.get('block_size', '1M')
        count = test_config.get('count', 100000)
        
        # Get flags from config
        flags_config = test_config.get('flags', {})
        if isinstance(flags_config, dict):
            direct = flags_config.get('direct', direct)
        
        # Build command
        cmd = [
            'dd',
            f'if={filepath}',
            'of=/dev/null',
            f'bs={block_size}',
            f'count={count}',
            'status=progress'
        ]
        
        if direct:
            cmd.append('iflag=direct')
        
        try:
            start = time.time()
            result = self.run_command_with_timeout(cmd, timeout=self.config.get('timeout', 600), check=True)
            duration = time.time() - start
            
            # Stop metrics and get summary
            metrics_summary = self._stop_metrics_collection()
            
            # Parse throughput
            throughput = self._parse_dd_output(result.stderr)
            
            # Calculate size in MB
            size_mb = count if 'M' in block_size.upper() else count * int(block_size.rstrip('KkMmGg')) // 1024
            
            # Store results
            self.results[name] = {
                "status": "passed",
                "duration_seconds": round(duration, 2),
                "throughput_mbps": throughput,
                "size_mb": size_mb,
                "block_size": block_size,
                "count": count,
                "flags": {
                    "direct_io": direct,
                    "cached": not direct
                }
            }
            
            # Add metrics - properly separated
            if metrics_summary:
                if 'system' in metrics_summary:
                    self.results[name]["system_metrics"] = metrics_summary['system']
                if 'nfs' in metrics_summary:
                    self.results[name]["nfs_metrics"] = metrics_summary['nfs']
            
            # Validate throughput
            validation = self._validate_throughput(throughput, "sequential")
            if validation.get('valid') is not None:
                self.results[name]["validation"] = validation
                
                severity = validation.get('severity', 'info')
                message = validation.get('message', '')
                
                if severity == 'error':
                    self.log(f"⚠️  {message}", "WARNING")
                elif severity == 'success':
                    self.log(f"✓ {message}", "SUCCESS")
                elif severity == 'warning':
                    self.log(f"⚠️  {message}", "WARNING")
            
            self.log(f"DD {name} completed: {throughput:.2f} MB/s in {duration:.2f}s", "SUCCESS")
            
        except subprocess.CalledProcessError as e:
            self._stop_metrics_collection()
            error_details = str(e)
            if e.stderr:
                error_details = e.stderr[:300]
            
            self.results[name] = {
                "status": "failed",
                "error": error_details
            }
            self.log(f"❌ DD {name} failed", "ERROR")
            self.log(f"  Error: {error_details}", "ERROR")
            self.log(f"  Troubleshooting:", "ERROR")
            self.log(f"  • Verify file exists: ls -la {filepath}", "ERROR")
            self.log(f"  • Check read permissions on file", "ERROR")
            self.log(f"  • Ensure NFS mount is still accessible", "ERROR")
            self.log(f"  • Check for stale file handles: dmesg | grep -i stale", "ERROR")
    
    def _dd_delete_test(self):
        """Delete DD test files."""
        self.log("Deleting DD test files...", "INFO")
        
        try:
            if self.file1.exists():
                self.file1.unlink()
            if self.file2.exists():
                self.file2.unlink()
            
            self.results["delete"] = {
                "status": "passed"
            }
            self.log("DD test files deleted successfully", "SUCCESS")
            
        except Exception as e:
            self.results["delete"] = {
                "status": "failed",
                "error": str(e)
            }
            self.log(f"❌ Failed to delete DD test files: {e}", "ERROR")
            self.log(f"  Files may still exist:", "ERROR")
            self.log(f"  • {self.file1}", "ERROR")
            self.log(f"  • {self.file2}", "ERROR")
            self.log(f"  Manual cleanup: rm -f {self.file1} {self.file2}", "ERROR")
    
    def _parse_dd_output(self, output: str) -> float:
        """
        Parse DD output to extract throughput.
        
        Args:
            output: DD command stderr output
            
        Returns:
            float: Throughput in MB/s
        """
        # Look for patterns like "1.2 GB/s" or "850 MB/s"
        match = re.search(r'([\d.]+)\s*(GB|MB)/s', output)
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            if unit == "GB":
                return value * 1024  # Convert to MB/s
            return value
        return 0.0

# Made with Bob
