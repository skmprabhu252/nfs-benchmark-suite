#!/usr/bin/env python3
"""
Bonnie++ Test Tool for NFS Benchmark Suite

This module implements the BonnieTestTool class for running Bonnie++
performance tests on NFS mounts. Bonnie++ is a comprehensive filesystem
benchmark that tests sequential I/O, random seeks, and file creation/deletion.
"""

import subprocess
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from .core import BaseTestTool


class BonnieTestTool(BaseTestTool):
    """
    Bonnie++ test tool implementation.
    
    Performs comprehensive filesystem I/O tests including:
    - Sequential output (character and block)
    - Sequential input (character and block)
    - Random seeks
    - Sequential create/delete operations
    - Random create/delete operations
    - Rewrite performance
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
        Initialize Bonnie++ test tool.
        
        Args:
            config: Bonnie++ test configuration
            mount_path: NFS mount path
            logger: Logger instance
            metrics_collector: Optional metrics collector
            nfs_metrics_collector: Optional NFS metrics collector
            network_intel: Optional network intelligence
        """
        super().__init__("bonnie++", config, mount_path, logger, metrics_collector, nfs_metrics_collector, network_intel)
        
        # Test directory
        self.test_dir = self.mount_path / "bonnie_test"
        
        # Results storage
        self.results = {}
    
    def validate_tool(self) -> bool:
        """
        Validate that bonnie++ command is available.
        
        Returns:
            bool: True if bonnie++ is available
        """
        if not self._check_command("bonnie++"):
            self.log("❌ bonnie++ command not found", "ERROR")
            self.log("  bonnie++ is required for file system benchmarking", "ERROR")
            self.log("", "ERROR")
            self.log("  Quick Fix:", "ERROR")
            self.log("  • Run: ./setup_and_verify.sh --auto", "ERROR")
            self.log("", "ERROR")
            self.log("  Manual Installation:", "ERROR")
            self.log("  • Ubuntu/Debian: sudo apt-get install bonnie++", "ERROR")
            self.log("  • RHEL/CentOS: sudo yum install bonnie++", "ERROR")
            self.log("  Verify installation: bonnie++ -v", "ERROR")
            return False
        return True
    
    def run_tests(self) -> Dict[str, Any]:
        """
        Run all Bonnie++ tests.
        
        Returns:
            dict: Test results for all Bonnie++ tests
        """
        self.log("=" * 60, "INFO")
        self.log("Starting Bonnie++ Tests", "INFO")
        self.log("=" * 60, "INFO")
        
        # Create test directory
        self.test_dir.mkdir(exist_ok=True)
        
        # Run Bonnie++ tests
        self._bonnie_comprehensive_test()
        self._bonnie_fast_test()
        self._bonnie_file_operations()
        
        return self.results
    
    def cleanup(self):
        """Clean up Bonnie++ test directory with verification."""
        self.log("Cleaning up Bonnie++ test directory...", "INFO")
        
        if self.test_dir.exists():
            if self._safe_remove_path(self.test_dir, is_directory=True):
                self.log("Bonnie++ cleanup completed successfully", "SUCCESS")
            else:
                self.log("Bonnie++ cleanup completed with warnings", "WARNING")
        else:
            self.log("Bonnie++ test directory does not exist (already cleaned)", "SUCCESS")
    
    def _build_bonnie_command(self, test_config: Dict[str, Any]) -> List[str]:
        """
        Build Bonnie++ command from configuration.
        
        Args:
            test_config: Test-specific configuration
            
        Returns:
            list: Bonnie++ command with parameters
        """
        import os
        
        cmd = ['bonnie++']
        
        # Directory for tests
        cmd.extend(['-d', str(self.test_dir)])
        
        # File size (in MB)
        if 'file_size' in test_config:
            cmd.extend(['-s', test_config['file_size']])
        
        # Number of files for file creation tests
        if 'num_files' in test_config:
            cmd.extend(['-n', test_config['num_files']])
        
        # RAM size (for determining file size)
        if 'ram_size' in test_config:
            cmd.extend(['-r', test_config['ram_size']])
        
        # User to run as (required when running as root)
        if 'user' in test_config:
            cmd.extend(['-u', test_config['user']])
        elif os.geteuid() == 0:
            # Running as root, use current user or nobody
            cmd.extend(['-u', 'root'])
        
        # Machine name for output
        if 'machine_name' in test_config:
            cmd.extend(['-m', test_config['machine_name']])
        
        # Number of processes for file operations
        if 'processes' in test_config:
            cmd.extend(['-p', str(test_config['processes'])])
        
        # Fast mode (skip per-char tests)
        if test_config.get('fast_mode', False):
            cmd.append('-f')
        
        # Quiet mode (machine-readable output)
        cmd.append('-q')
        
        return cmd
    
    def _bonnie_comprehensive_test(self):
        """
        Run comprehensive Bonnie++ test with all operations.
        
        This test includes:
        - Sequential output (character and block)
        - Sequential input (character and block)
        - Random seeks
        - File creation/deletion tests
        """
        test_name = "comprehensive_test"
        test_config_key = "comprehensive_test"
        
        # Check if test is enabled
        test_config = self.config.get(test_config_key, {})
        if not test_config.get('enabled', True):
            self.log(f"Skipping {test_name} (disabled in config)", "INFO")
            self.results[test_name] = {"status": "skipped", "reason": "disabled"}
            return
        
        self.log(f"\nRunning Bonnie++ {test_name}...", "INFO")
        
        try:
            # Start metrics collection
            self._start_metrics_collection()
            
            # Build command
            cmd = self._build_bonnie_command(test_config)
            
            self.log(f"Command: {' '.join(cmd)}", "DEBUG")
            
            # Run test
            start_time = time.time()
            result = self.run_command_with_timeout(
                cmd,
                timeout=test_config.get('timeout', 3600)
            )
            duration = time.time() - start_time
            
            # Stop metrics collection
            system_metrics = self._stop_metrics_collection()
            
            if result.returncode != 0:
                self.log(f"Bonnie++ {test_name} failed: {result.stderr}", "ERROR")
                self.results[test_name] = {
                    "status": "failed",
                    "error": result.stderr,
                    "duration_seconds": duration
                }
                return
            
            # Parse output
            metrics = self._parse_bonnie_output(result.stdout)
            
            if not metrics:
                self.log(f"Failed to parse Bonnie++ output", "ERROR")
                self.results[test_name] = {
                    "status": "failed",
                    "error": "Failed to parse output",
                    "duration_seconds": duration,
                    "raw_output": result.stdout
                }
                return
            
            # Store results
            self.results[test_name] = {
                "status": "passed",
                "duration_seconds": duration,
                **metrics,
                "system_metrics": system_metrics,
                "config": test_config
            }
            
            # Log summary
            self.log(f"✓ Bonnie++ {test_name} completed", "SUCCESS")
            self._log_bonnie_summary(metrics)
            
            # Validate throughput if network intelligence is available
            if self.network_intel and 'sequential_output_block_mbps' in metrics:
                validation = self._validate_throughput(
                    metrics['sequential_output_block_mbps'],
                    "sequential"
                )
                self.results[test_name]['network_validation'] = validation
            
        except subprocess.TimeoutExpired:
            self.log(f"Bonnie++ {test_name} timed out", "ERROR")
            self.results[test_name] = {
                "status": "failed",
                "error": "Test timed out",
                "duration_seconds": test_config.get('timeout', 3600)
            }
        except Exception as e:
            self.log(f"Bonnie++ {test_name} error: {e}", "ERROR")
            self.results[test_name] = {
                "status": "failed",
                "error": str(e)
            }
    
    def _bonnie_fast_test(self):
        """
        Run fast Bonnie++ test (skips per-character tests).
        
        This is a quicker version that focuses on block I/O and file operations.
        """
        test_name = "fast_test"
        test_config_key = "fast_test"
        
        # Check if test is enabled
        test_config = self.config.get(test_config_key, {})
        if not test_config.get('enabled', True):
            self.log(f"Skipping {test_name} (disabled in config)", "INFO")
            self.results[test_name] = {"status": "skipped", "reason": "disabled"}
            return
        
        self.log(f"\nRunning Bonnie++ {test_name}...", "INFO")
        
        try:
            # Start metrics collection
            self._start_metrics_collection()
            
            # Build command with fast mode
            test_config['fast_mode'] = True
            cmd = self._build_bonnie_command(test_config)
            
            self.log(f"Command: {' '.join(cmd)}", "DEBUG")
            
            # Run test
            start_time = time.time()
            result = self.run_command_with_timeout(
                cmd,
                timeout=test_config.get('timeout', 1800)
            )
            duration = time.time() - start_time
            
            # Stop metrics collection
            system_metrics = self._stop_metrics_collection()
            
            if result.returncode != 0:
                self.log(f"Bonnie++ {test_name} failed: {result.stderr}", "ERROR")
                self.results[test_name] = {
                    "status": "failed",
                    "error": result.stderr,
                    "duration_seconds": duration
                }
                return
            
            # Parse output
            metrics = self._parse_bonnie_output(result.stdout)
            
            if not metrics:
                self.log(f"Failed to parse Bonnie++ output", "ERROR")
                self.results[test_name] = {
                    "status": "failed",
                    "error": "Failed to parse output",
                    "duration_seconds": duration
                }
                return
            
            # Store results
            result_dict = {
                "status": "passed",
                "duration_seconds": duration,
                **metrics,
                "config": test_config
            }
            
            # Add metrics - properly separated
            if system_metrics:
                if 'system' in system_metrics:
                    result_dict["system_metrics"] = system_metrics['system']
                if 'nfs' in system_metrics:
                    result_dict["nfs_metrics"] = system_metrics['nfs']
            
            self.results[test_name] = result_dict
            
            self.log(f"✓ Bonnie++ {test_name} completed", "SUCCESS")
            self._log_bonnie_summary(metrics)
            
        except subprocess.TimeoutExpired:
            self.log(f"Bonnie++ {test_name} timed out", "ERROR")
            self.results[test_name] = {
                "status": "failed",
                "error": "Test timed out"
            }
        except Exception as e:
            self.log(f"Bonnie++ {test_name} error: {e}", "ERROR")
            self.results[test_name] = {
                "status": "failed",
                "error": str(e)
            }
    
    def _bonnie_file_operations(self):
        """
        Run Bonnie++ file operations test focusing on metadata operations.
        
        Tests file creation, stat, and deletion performance.
        """
        test_name = "file_operations"
        test_config_key = "file_operations"
        
        # Check if test is enabled
        test_config = self.config.get(test_config_key, {})
        if not test_config.get('enabled', True):
            self.log(f"Skipping {test_name} (disabled in config)", "INFO")
            self.results[test_name] = {"status": "skipped", "reason": "disabled"}
            return
        
        self.log(f"\nRunning Bonnie++ {test_name}...", "INFO")
        
        try:
            # Start metrics collection
            self._start_metrics_collection()
            
            # Build command focusing on file operations
            cmd = self._build_bonnie_command(test_config)
            
            self.log(f"Command: {' '.join(cmd)}", "DEBUG")
            
            # Run test
            start_time = time.time()
            result = self.run_command_with_timeout(
                cmd,
                timeout=test_config.get('timeout', 1800)
            )
            duration = time.time() - start_time
            
            # Stop metrics collection
            system_metrics = self._stop_metrics_collection()
            
            if result.returncode != 0:
                self.log(f"Bonnie++ {test_name} failed: {result.stderr}", "ERROR")
                self.results[test_name] = {
                    "status": "failed",
                    "error": result.stderr,
                    "duration_seconds": duration
                }
                return
            
            # Parse output
            metrics = self._parse_bonnie_output(result.stdout)
            
            if not metrics:
                self.log(f"Failed to parse Bonnie++ output", "ERROR")
                self.results[test_name] = {
                    "status": "failed",
                    "error": "Failed to parse output",
                    "duration_seconds": duration
                }
                return
            
            # Store results
            result_dict = {
                "status": "passed",
                "duration_seconds": duration,
                **metrics,
                "config": test_config
            }
            
            # Add metrics - properly separated
            if system_metrics:
                if 'system' in system_metrics:
                    result_dict["system_metrics"] = system_metrics['system']
                if 'nfs' in system_metrics:
                    result_dict["nfs_metrics"] = system_metrics['nfs']
            
            self.results[test_name] = result_dict
            
            self.log(f"✓ Bonnie++ {test_name} completed", "SUCCESS")
            self._log_bonnie_summary(metrics)
            
        except subprocess.TimeoutExpired:
            self.log(f"Bonnie++ {test_name} timed out", "ERROR")
            self.results[test_name] = {
                "status": "failed",
                "error": "Test timed out"
            }
        except Exception as e:
            self.log(f"Bonnie++ {test_name} error: {e}", "ERROR")
            self.results[test_name] = {
                "status": "failed",
                "error": str(e)
            }
    
    def _parse_bonnie_output(self, output: str) -> Optional[Dict[str, Any]]:
        """
        Parse Bonnie++ CSV output format.
        
        Bonnie++ outputs in CSV format with the following fields:
        name,sequential_output_char,sequential_output_block,sequential_output_rewrite,
        sequential_input_char,sequential_input_block,random_seeks,
        file_create_seq,file_stat_seq,file_delete_seq,
        file_create_random,file_stat_random,file_delete_random
        
        Args:
            output: Raw Bonnie++ output
            
        Returns:
            dict: Parsed metrics or None if parsing fails
        """
        try:
            # Find the CSV line (starts with hostname or machine name)
            lines = output.strip().split('\n')
            csv_line = None
            
            for line in lines:
                # Skip empty lines and headers
                if not line or line.startswith('version') or line.startswith('name'):
                    continue
                # CSV data line typically has many commas
                if line.count(',') > 10:
                    csv_line = line
                    break
            
            if not csv_line:
                self.log("Could not find CSV data in Bonnie++ output", "WARNING")
                return None
            
            # Split CSV line
            fields = csv_line.split(',')
            
            if len(fields) < 20:
                self.log(f"Unexpected number of fields in Bonnie++ output: {len(fields)}", "WARNING")
                return None
            
            # Parse metrics (converting K/sec to MB/s where appropriate)
            metrics = {}
            
            # Sequential output - character (K/sec)
            if fields[1] and fields[1] != '+++':
                metrics['sequential_output_char_kbps'] = self._parse_value(fields[1])
                metrics['sequential_output_char_mbps'] = metrics['sequential_output_char_kbps'] / 1024
            
            # Sequential output - block (K/sec)
            if fields[3] and fields[3] != '+++':
                metrics['sequential_output_block_kbps'] = self._parse_value(fields[3])
                metrics['sequential_output_block_mbps'] = metrics['sequential_output_block_kbps'] / 1024
            
            # Sequential output - rewrite (K/sec)
            if fields[5] and fields[5] != '+++':
                metrics['sequential_rewrite_kbps'] = self._parse_value(fields[5])
                metrics['sequential_rewrite_mbps'] = metrics['sequential_rewrite_kbps'] / 1024
            
            # Sequential input - character (K/sec)
            if fields[7] and fields[7] != '+++':
                metrics['sequential_input_char_kbps'] = self._parse_value(fields[7])
                metrics['sequential_input_char_mbps'] = metrics['sequential_input_char_kbps'] / 1024
            
            # Sequential input - block (K/sec)
            if fields[9] and fields[9] != '+++':
                metrics['sequential_input_block_kbps'] = self._parse_value(fields[9])
                metrics['sequential_input_block_mbps'] = metrics['sequential_input_block_kbps'] / 1024
            
            # Random seeks (seeks/sec)
            if fields[11] and fields[11] != '+++':
                metrics['random_seeks_per_sec'] = self._parse_value(fields[11])
            
            # File operations - sequential create (files/sec)
            if len(fields) > 13 and fields[13] and fields[13] != '+++':
                metrics['file_create_seq_per_sec'] = self._parse_value(fields[13])
            
            # File operations - sequential stat (files/sec)
            if len(fields) > 15 and fields[15] and fields[15] != '+++':
                metrics['file_stat_seq_per_sec'] = self._parse_value(fields[15])
            
            # File operations - sequential delete (files/sec)
            if len(fields) > 17 and fields[17] and fields[17] != '+++':
                metrics['file_delete_seq_per_sec'] = self._parse_value(fields[17])
            
            # File operations - random create (files/sec)
            if len(fields) > 19 and fields[19] and fields[19] != '+++':
                metrics['file_create_random_per_sec'] = self._parse_value(fields[19])
            
            # File operations - random stat (files/sec)
            if len(fields) > 21 and fields[21] and fields[21] != '+++':
                metrics['file_stat_random_per_sec'] = self._parse_value(fields[21])
            
            # File operations - random delete (files/sec)
            if len(fields) > 23 and fields[23] and fields[23] != '+++':
                metrics['file_delete_random_per_sec'] = self._parse_value(fields[23])
            
            return metrics
            
        except Exception as e:
            self.log(f"Error parsing Bonnie++ output: {e}", "ERROR")
            self.log(f"Output was: {output[:500]}", "DEBUG")
            return None
    
    def _parse_value(self, value: str) -> float:
        """
        Parse a numeric value from Bonnie++ output.
        
        Args:
            value: String value to parse
            
        Returns:
            float: Parsed value or 0.0 if parsing fails
        """
        try:
            # Remove any non-numeric characters except decimal point
            cleaned = re.sub(r'[^\d.]', '', value)
            return float(cleaned) if cleaned else 0.0
        except:
            return 0.0
    
    def _log_bonnie_summary(self, metrics: Dict[str, Any]):
        """
        Log a summary of Bonnie++ test results.
        
        Args:
            metrics: Parsed metrics dictionary
        """
        self.log("  Results:", "INFO")
        
        # Sequential output
        if 'sequential_output_block_mbps' in metrics:
            self.log(f"    Sequential Output (Block): {metrics['sequential_output_block_mbps']:.2f} MB/s", "INFO")
        if 'sequential_rewrite_mbps' in metrics:
            self.log(f"    Sequential Rewrite: {metrics['sequential_rewrite_mbps']:.2f} MB/s", "INFO")
        
        # Sequential input
        if 'sequential_input_block_mbps' in metrics:
            self.log(f"    Sequential Input (Block): {metrics['sequential_input_block_mbps']:.2f} MB/s", "INFO")
        
        # Random seeks
        if 'random_seeks_per_sec' in metrics:
            self.log(f"    Random Seeks: {metrics['random_seeks_per_sec']:.2f} seeks/sec", "INFO")
        
        # File operations
        if 'file_create_seq_per_sec' in metrics:
            self.log(f"    File Create (Sequential): {metrics['file_create_seq_per_sec']:.2f} files/sec", "INFO")
        if 'file_delete_seq_per_sec' in metrics:
            self.log(f"    File Delete (Sequential): {metrics['file_delete_seq_per_sec']:.2f} files/sec", "INFO")


# Made with Bob