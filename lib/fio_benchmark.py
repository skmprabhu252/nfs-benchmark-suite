#!/usr/bin/env python3
"""
FIO Test Tool for NFS Performance Testing

This module implements the FIOTestTool class for running FIO (Flexible I/O Tester)
performance tests on NFS mounts.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List

from .core import BaseTestTool


class FIOTestTool(BaseTestTool):
    """
    FIO (Flexible I/O Tester) test tool implementation.
    
    Performs comprehensive I/O tests including sequential, random,
    mixed workloads, metadata operations, and latency tests.
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
        Initialize FIO test tool.
        
        Args:
            config: FIO test configuration
            mount_path: NFS mount path
            logger: Logger instance
            metrics_collector: Optional metrics collector
            nfs_metrics_collector: Optional NFS metrics collector
            network_intel: Optional network intelligence
        """
        super().__init__("fio", config, mount_path, logger, metrics_collector, nfs_metrics_collector, network_intel)
        
        # Test directory
        self.test_dir = self.mount_path / "cthon"
        
        # Results storage
        self.results = {}
    
    def validate_tool(self) -> bool:
        """
        Validate that fio command is available.
        
        Returns:
            bool: True if fio is available
        """
        if not self._check_command("fio"):
            self.log("❌ fio command not found", "ERROR")
            self.log("  fio (Flexible I/O Tester) is required for comprehensive I/O testing", "ERROR")
            self.log("", "ERROR")
            self.log("  Quick Fix:", "ERROR")
            self.log("  • Run: ./setup_and_verify.sh --auto", "ERROR")
            self.log("", "ERROR")
            self.log("  Manual Installation:", "ERROR")
            self.log("  • Ubuntu/Debian: sudo apt-get install fio", "ERROR")
            self.log("  • RHEL/CentOS: sudo yum install fio", "ERROR")
            self.log("  • macOS: brew install fio", "ERROR")
            self.log("  Verify installation: fio --version", "ERROR")
            return False
        return True
    
    def run_tests(self) -> Dict[str, Any]:
        """
        Run all FIO tests.
        
        Returns:
            dict: Test results for all FIO tests
        """
        self.log("=" * 60, "INFO")
        self.log("Starting FIO Tests", "INFO")
        self.log("=" * 60, "INFO")
        
        # Create test directory
        self.test_dir.mkdir(exist_ok=True)
        
        # Run all FIO tests
        self._fio_sequential_write()
        self._fio_sequential_read()
        self._fio_random_read()
        self._fio_random_write()
        self._fio_mixed_randrw()
        self._fio_metadata_ops()
        self._fio_latency_test()
        
        return self.results
    
    def cleanup(self):
        """Clean up FIO test directory with verification."""
        self.log("Cleaning up FIO test directory...", "INFO")
        
        if self.test_dir.exists():
            if self._safe_remove_path(self.test_dir, is_directory=True):
                self.log("FIO cleanup completed successfully", "SUCCESS")
            else:
                self.log("FIO cleanup completed with warnings", "WARNING")
        else:
            self.log("FIO test directory does not exist (already cleaned)", "SUCCESS")
    
    def _build_fio_command(self, test_name: str, config_key: str) -> List[str]:
        """
        Build FIO command from configuration.
        
        Args:
            test_name: Name for the FIO test
            config_key: Key in fio_tests config
            
        Returns:
            list: FIO command with parameters
        """
        # Get test configuration
        test_config = self.config.get(config_key, {})
        if not isinstance(test_config, dict):
            test_config = {}
        
        # Get common config
        common_config = self.config.get('common', {})
        if not isinstance(common_config, dict):
            common_config = {}
        
        # Build base command
        cmd = [
            'fio',
            f'--name={test_name}',
            f'--directory={self.test_dir}'
        ]
        
        # Add test-specific parameters
        param_map = {
            'rw': '--rw',
            'rwmixread': '--rwmixread',
            'bs': '--bs',
            'size': '--size',
            'filesize': '--filesize',
            'nrfiles': '--nrfiles',
            'numjobs': '--numjobs',
            'ioengine': '--ioengine',
            'iodepth': '--iodepth',
            'direct': '--direct',
            'runtime': '--runtime',
            'randrepeat': '--randrepeat',
            'create_on_open': '--create_on_open',
            'lat_percentiles': '--lat_percentiles'
        }
        
        for key, flag in param_map.items():
            if key in test_config:
                cmd.append(f'{flag}={test_config[key]}')
        
        # Add common parameters
        if common_config.get('time_based', True):
            cmd.append('--time_based')
        if common_config.get('group_reporting', True):
            cmd.append('--group_reporting')
        
        output_format = common_config.get('output_format', 'json')
        cmd.append(f'--output-format={output_format}')
        
        return cmd
    
    def _fio_sequential_write(self):
        """FIO sequential write test."""
        self.log("Running FIO sequential write test...", "INFO")
        cmd = self._build_fio_command('seq_write', 'sequential_write')
        self._run_fio_test("sequential_write", cmd)
    
    def _fio_sequential_read(self):
        """FIO sequential read test."""
        self.log("Running FIO sequential read test...", "INFO")
        cmd = self._build_fio_command('seq_read', 'sequential_read')
        self._run_fio_test("sequential_read", cmd)
    
    def _fio_random_read(self):
        """FIO random read test."""
        self.log("Running FIO random read test...", "INFO")
        cmd = self._build_fio_command('rand_read_4k', 'random_read_4k')
        self._run_fio_test("random_read_4k", cmd)
    
    def _fio_random_write(self):
        """FIO random write test."""
        self.log("Running FIO random write test...", "INFO")
        cmd = self._build_fio_command('rand_write_4k', 'random_write_4k')
        self._run_fio_test("random_write_4k", cmd)
    
    def _fio_mixed_randrw(self):
        """FIO mixed random read/write test."""
        self.log("Running FIO mixed random read/write test...", "INFO")
        cmd = self._build_fio_command('mixed_randrw', 'mixed_randrw_70_30')
        self._run_fio_test("mixed_randrw_70_30", cmd)
    
    def _fio_metadata_ops(self):
        """FIO metadata operations test."""
        self.log("Running FIO metadata operations test...", "INFO")
        cmd = self._build_fio_command('metadata_ops', 'metadata_operations')
        self._run_fio_test("metadata_operations", cmd)
    
    def _fio_latency_test(self):
        """FIO latency test."""
        self.log("Running FIO latency test...", "INFO")
        cmd = self._build_fio_command('latency_test', 'latency_test')
        self._run_fio_test("latency_test", cmd)
    
    def _run_fio_test(self, test_name: str, cmd: List[str]):
        """
        Run a FIO test and parse results.
        
        Args:
            test_name: Name of the test
            cmd: FIO command to execute
        """
        # Start metrics collection
        self._start_metrics_collection()
        
        try:
            result = self.run_command_with_timeout(cmd, timeout=self.config.get('timeout', 900), check=True)
            
            # Stop metrics and get summary
            metrics_summary = self._stop_metrics_collection()
            
            # Parse JSON output
            fio_data = json.loads(result.stdout)
            
            # Extract metrics
            jobs = fio_data.get('jobs', [])
            if jobs:
                job = jobs[0]
                
                read_data = job.get('read', {})
                write_data = job.get('write', {})
                
                metrics = {
                    "status": "passed",
                    "read_iops": round(read_data.get('iops', 0), 2),
                    "write_iops": round(write_data.get('iops', 0), 2),
                    "read_bandwidth_mbps": round(read_data.get('bw', 0) / 1024, 2),
                    "write_bandwidth_mbps": round(write_data.get('bw', 0) / 1024, 2),
                    "read_latency_ms": round(read_data.get('lat_ns', {}).get('mean', 0) / 1000000, 2),
                    "write_latency_ms": round(write_data.get('lat_ns', {}).get('mean', 0) / 1000000, 2)
                }
                
                # Add metrics - properly separated
                if metrics_summary:
                    if 'system' in metrics_summary:
                        metrics["system_metrics"] = metrics_summary['system']
                    if 'nfs' in metrics_summary:
                        metrics["nfs_metrics"] = metrics_summary['nfs']
                
                self.results[test_name] = metrics
                self.log(f"FIO {test_name} completed successfully", "SUCCESS")
            else:
                self.log("❌ No job data found in FIO output", "ERROR")
                self.log("  This usually indicates:", "ERROR")
                self.log("  • FIO command completed but produced no results", "ERROR")
                self.log("  • Invalid FIO configuration parameters", "ERROR")
                self.log("  • FIO version incompatibility", "ERROR")
                self.log("  Check FIO version: fio --version (requires 3.0+)", "ERROR")
                raise ValueError("No job data in FIO output")
                
        except subprocess.CalledProcessError as e:
            self._stop_metrics_collection()
            error_details = str(e)
            if e.stderr:
                error_details = e.stderr[:300]
            
            self.results[test_name] = {
                "status": "failed",
                "error": error_details
            }
            self.log(f"❌ FIO {test_name} failed", "ERROR")
            self.log(f"  Error: {error_details}", "ERROR")
            self.log(f"  Troubleshooting:", "ERROR")
            self.log(f"  • Check FIO configuration in config file", "ERROR")
            self.log(f"  • Verify test directory exists: ls -la {self.test_dir}", "ERROR")
            self.log(f"  • Check available disk space: df -h {self.mount_path}", "ERROR")
            self.log(f"  • Review FIO parameters for compatibility", "ERROR")
        except Exception as e:
            self._stop_metrics_collection()
            self.results[test_name] = {
                "status": "failed",
                "error": str(e)
            }
            self.log(f"❌ FIO {test_name} parsing failed: {e}", "ERROR")
            self.log(f"  Error type: {type(e).__name__}", "ERROR")
            self.log(f"  This may indicate:", "ERROR")
            self.log(f"  • Invalid JSON output from FIO", "ERROR")
            self.log(f"  • FIO version incompatibility", "ERROR")
            self.log(f"  • Unexpected output format", "ERROR")
            self.log(f"  Try running FIO manually to verify: fio --version", "ERROR")

# Made with Bob
