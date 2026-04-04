#!/usr/bin/env python3
"""
dbench Test Tool for NFS Benchmark Suite

This module implements the DBenchTestTool class for running dbench
performance tests on NFS mounts. dbench simulates realistic client/server
workloads using NetBench traces, making it ideal for testing NFS performance
under concurrent client scenarios.
"""

import subprocess
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from .core import BaseTestTool


class DBenchTestTool(BaseTestTool):
    """
    dbench test tool implementation.
    
    Performs client/server simulation tests including:
    - Light client load (baseline)
    - Moderate client load (typical office)
    - Heavy client load (stress test)
    - Scalability analysis (progressive load)
    - Latency-focused testing
    - Sustained load testing
    - Rate-limited testing
    - Metadata-intensive operations
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
        Initialize dbench test tool.
        
        Args:
            config: dbench test configuration
            mount_path: NFS mount path
            logger: Logger instance
            metrics_collector: Optional metrics collector
            nfs_metrics_collector: Optional NFS metrics collector
            network_intel: Optional network intelligence
        """
        super().__init__("dbench", config, mount_path, logger, metrics_collector, nfs_metrics_collector, network_intel)
        
        # Get common config
        common_config = self.config.get('common', {})
        
        # Test directory
        test_dir_name = common_config.get('directory', 'dbench_test')
        self.test_dir = self.mount_path / test_dir_name
        
        # Results storage
        self.results = {}
    
    def validate_tool(self) -> bool:
        """
        Validate that dbench command is available.
        
        Returns:
            bool: True if dbench is available
        """
        if not self._check_command("dbench"):
            self.log("❌ dbench command not found", "ERROR")
            self.log("  dbench is required for client load simulation", "ERROR")
            self.log("", "ERROR")
            self.log("  Quick Fix:", "ERROR")
            self.log("  • Run: ./setup_and_verify.sh --auto", "ERROR")
            self.log("", "ERROR")
            self.log("  Manual Installation:", "ERROR")
            self.log("  • Ubuntu/Debian: sudo apt-get install dbench", "ERROR")
            self.log("  • RHEL/CentOS: sudo yum install dbench", "ERROR")
            self.log("  Verify installation: dbench --version", "ERROR")
            return False
        return True
    
    def run_tests(self) -> Dict[str, Any]:
        """
        Run all dbench tests.
        
        Returns:
            dict: Test results for all dbench tests
        """
        self.log("=" * 60, "INFO")
        self.log("Starting dbench Tests", "INFO")
        self.log("=" * 60, "INFO")
        
        # Create test directory
        self.test_dir.mkdir(exist_ok=True)
        
        # Run all configured dbench tests
        self._dbench_light_client_load()
        self._dbench_moderate_client_load()
        self._dbench_heavy_client_load()
        self._dbench_scalability_test()
        self._dbench_latency_test()
        self._dbench_sustained_load()
        self._dbench_rate_limited_test()
        self._dbench_metadata_intensive()
        
        return self.results
    
    def cleanup(self):
        """Clean up dbench test directory with verification."""
        self.log("Cleaning up dbench test directory...", "INFO")
        
        if self.test_dir.exists():
            if self._safe_remove_path(self.test_dir, is_directory=True):
                self.log("dbench cleanup completed successfully", "SUCCESS")
            else:
                self.log("dbench cleanup completed with warnings", "WARNING")
        else:
            self.log("dbench test directory does not exist (already cleaned)", "SUCCESS")
    def _validate_config(self, test_config: Dict[str, Any]) -> bool:
        """
        Validate test configuration parameters.
        
        Args:
            test_config: Test-specific configuration
            
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Check required keys
        required_keys = ['num_clients', 'duration']
        for key in required_keys:
            if key not in test_config:
                self.log(f"Missing required config key: {key}", "ERROR")
                return False
        
        # Type validation for num_clients
        num_clients = test_config['num_clients']
        if not isinstance(num_clients, int):
            self.log(f"num_clients must be int, got {type(num_clients).__name__}", "ERROR")
            return False
        
        # Range validation for num_clients
        if num_clients < 1:
            self.log(f"num_clients must be >= 1, got {num_clients}", "ERROR")
            return False
        
        if num_clients > 256:
            self.log(f"num_clients exceeds maximum (256), got {num_clients}", "WARNING")
            self.log("  High client counts may cause system instability", "WARNING")
        
        # Type validation for duration
        duration = test_config['duration']
        if not isinstance(duration, (int, float)):
            self.log(f"duration must be numeric, got {type(duration).__name__}", "ERROR")
            return False
        
        # Range validation for duration
        if duration < 1:
            self.log(f"duration must be >= 1 second, got {duration}", "ERROR")
            return False
        
        if duration > 7200:  # 2 hours
            self.log(f"duration is very long ({duration}s), test may take significant time", "WARNING")
        
        # Validate target_rate if present
        if 'target_rate' in test_config:
            target_rate = test_config['target_rate']
            if not isinstance(target_rate, (int, float)):
                self.log(f"target_rate must be numeric, got {type(target_rate).__name__}", "ERROR")
                return False
            
            if target_rate < 0:
                self.log(f"target_rate must be >= 0, got {target_rate}", "ERROR")
                return False
        
        # Validate warmup if present
        if 'warmup' in test_config:
            warmup = test_config['warmup']
            if not isinstance(warmup, (int, float)):
                self.log(f"warmup must be numeric, got {type(warmup).__name__}", "ERROR")
                return False
            
            if warmup < 0:
                self.log(f"warmup must be >= 0, got {warmup}", "ERROR")
                return False
        
        # Validate boolean flags
        for flag in ['fsync', 'sync_dirs']:
            if flag in test_config and not isinstance(test_config[flag], bool):
                self.log(f"{flag} must be boolean, got {type(test_config[flag]).__name__}", "ERROR")
                return False
        
        # Validate loadfile if present
        if 'loadfile' in test_config:
            loadfile = test_config['loadfile']
            if not isinstance(loadfile, str):
                self.log(f"loadfile must be string, got {type(loadfile).__name__}", "ERROR")
                return False
            
            # Check if loadfile exists (info only, we have fallback)
            possible_paths = [
                Path(loadfile),
                Path(__file__).parent.parent / 'config' / loadfile,
                Path(f'/usr/share/dbench/{loadfile}'),
                Path(f'/usr/local/share/dbench/{loadfile}')
            ]
            
            if not any(p.exists() for p in possible_paths):
                self.log(f"loadfile '{loadfile}' not found in standard locations, will use default", "INFO")
        
        return True
    
    def _check_dbench_option(self, option: str) -> bool:
        """
        Check if dbench supports a specific option.
        
        Args:
            option: The option to check (e.g., '--fsync')
            
        Returns:
            bool: True if option is supported
        """
        try:
            result = subprocess.run(
                ['dbench', '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return option in result.stdout or option in result.stderr
        except Exception:
            return False
    
    def _build_dbench_command(self, test_config: Dict[str, Any]) -> List[str]:
        """
        Build dbench command from configuration.
        
        Args:
            test_config: Test-specific configuration
            
        Returns:
            list: dbench command with parameters
        """
        # Validate configuration before building command
        if not self._validate_config(test_config):
            raise ValueError("Invalid test configuration")
        
        cmd = ['dbench']
        
        # Backend specification (required for dbench 5.0+)
        # Use fileio backend for filesystem/NFS testing
        backend = test_config.get('backend', 'fileio')
        cmd.extend(['-B', backend])
        
        # Number of clients (required)
        num_clients = test_config.get('num_clients', 1)
        
        # Directory for tests
        cmd.extend(['-D', str(self.test_dir)])
        
        # Duration (in seconds)
        if 'duration' in test_config:
            cmd.extend(['-t', str(test_config['duration'])])
        
        # Loadfile (workload definition) - REQUIRED for dbench 5.0+
        loadfile = test_config.get('loadfile', 'client.txt')
        loadfile_path = None
        
        # Check multiple locations for the loadfile
        possible_paths = [
            Path(loadfile),  # Absolute or relative path
            Path(__file__).parent.parent / 'config' / loadfile,  # Suite's config directory
            Path(f'/usr/share/dbench/{loadfile}'),  # System default location
            Path(f'/usr/local/share/dbench/{loadfile}')  # Local installation
        ]
        
        for path in possible_paths:
            if path.exists():
                loadfile_path = str(path)
                break
        
        if loadfile_path:
            cmd.extend(['-c', loadfile_path])
            self.log(f"Using loadfile: {loadfile_path}", "DEBUG")
            # Log loadfile content
            try:
                with open(loadfile_path, 'r') as f:
                    content = f.read()
                self.log(f"Loadfile content:\n{content}", "DEBUG")
            except Exception as e:
                self.log(f"Could not read loadfile content: {e}", "WARNING")
        else:
            # If no loadfile found, use the suite's default
            default_loadfile = Path(__file__).parent.parent / 'config' / 'client.txt'
            if default_loadfile.exists():
                cmd.extend(['-c', str(default_loadfile)])
                self.log(f"Using default loadfile: {default_loadfile}", "DEBUG")
                # Log loadfile content
                try:
                    with open(default_loadfile, 'r') as f:
                        content = f.read()
                    self.log(f"Loadfile content:\n{content}", "DEBUG")
                except Exception as e:
                    self.log(f"Could not read loadfile content: {e}", "WARNING")
            else:
                self.log(f"Warning: No loadfile found, dbench may fail", "WARNING")
        
        # Warmup period
        common_config = self.config.get('common', {})
        warmup = test_config.get('warmup', common_config.get('warmup', 0))
        if warmup > 0:
            cmd.extend(['--warmup', str(warmup)])
        
        # Target rate (MB/s) - 0 means no limit
        if 'target_rate' in test_config and test_config['target_rate'] > 0:
            cmd.extend(['--target-rate', str(test_config['target_rate'])])
        
        # Fsync option (check if supported)
        if test_config.get('fsync', False):
            if self._check_dbench_option('--fsync'):
                cmd.append('--fsync')
            else:
                self.log("Warning: --fsync not supported by this dbench version", "WARNING")
        
        # Sync directories (check if supported)
        if test_config.get('sync_dirs', False):
            if self._check_dbench_option('--sync-dirs'):
                cmd.append('--sync-dirs')
            else:
                self.log("Warning: --sync-dirs not supported by this dbench version", "WARNING")
        
        # Machine-readable output (check if supported)
        if common_config.get('machine_readable', True):
            if self._check_dbench_option('--machine-readable'):
                cmd.append('--machine-readable')
        
        # Skip cleanup (check if supported)
        if common_config.get('skip_cleanup', False):
            if self._check_dbench_option('--skip-cleanup'):
                cmd.append('--skip-cleanup')
        
        # Number of clients (last argument)
        cmd.append(str(num_clients))
        
        return cmd
    
    def _dbench_light_client_load(self):
        """
        Run light client load test (baseline).
        
        Tests with minimal client count to establish baseline performance.
        """
        test_name = "light_client_load"
        test_config = self.config.get(test_name, {})
        
        if not test_config.get('enabled', True):
            self.log(f"Skipping {test_name} (disabled in config)", "INFO")
            self.results[test_name] = {"status": "skipped", "reason": "disabled"}
            return
        
        self.log(f"\nRunning dbench {test_name}...", "INFO")
        self._run_dbench_test(test_name, test_config)
    
    def _dbench_moderate_client_load(self):
        """
        Run moderate client load test (typical office scenario).
        
        Simulates typical office workload with moderate concurrency.
        """
        test_name = "moderate_client_load"
        test_config = self.config.get(test_name, {})
        
        if not test_config.get('enabled', True):
            self.log(f"Skipping {test_name} (disabled in config)", "INFO")
            self.results[test_name] = {"status": "skipped", "reason": "disabled"}
            return
        
        self.log(f"\nRunning dbench {test_name}...", "INFO")
        self._run_dbench_test(test_name, test_config)
    
    def _dbench_heavy_client_load(self):
        """
        Run heavy client load test (stress test).
        
        Tests with high client count to stress the NFS server.
        """
        test_name = "heavy_client_load"
        test_config = self.config.get(test_name, {})
        
        if not test_config.get('enabled', True):
            self.log(f"Skipping {test_name} (disabled in config)", "INFO")
            self.results[test_name] = {"status": "skipped", "reason": "disabled"}
            return
        
        self.log(f"\nRunning dbench {test_name}...", "INFO")
        self._run_dbench_test(test_name, test_config)
    
    def _dbench_scalability_test(self):
        """
        Run scalability test with progressive client counts.
        
        Tests performance across different client counts to analyze scaling.
        """
        test_name = "scalability_test"
        test_config = self.config.get(test_name, {})
        
        if not test_config.get('enabled', True):
            self.log(f"Skipping {test_name} (disabled in config)", "INFO")
            self.results[test_name] = {"status": "skipped", "reason": "disabled"}
            return
        
        self.log(f"\nRunning dbench {test_name}...", "INFO")
        
        # Get client counts to test
        client_counts = test_config.get('client_counts', [1, 2, 4, 8, 16])
        duration_per_count = test_config.get('duration_per_count', 120)
        
        # Store results for each client count
        scalability_results = {
            "status": "passed",
            "client_counts": client_counts,
            "results": {}
        }
        
        for num_clients in client_counts:
            self.log(f"  Testing with {num_clients} client(s)...", "INFO")
            
            # Create modified config for this client count
            modified_config = test_config.copy()
            modified_config['num_clients'] = num_clients
            modified_config['duration'] = duration_per_count
            
            # Run test
            sub_test_name = f"{test_name}_{num_clients}_clients"
            result = self._run_dbench_test_internal(sub_test_name, modified_config)
            
            if result:
                scalability_results["results"][num_clients] = result
            else:
                scalability_results["status"] = "partial"
        
        self.results[test_name] = scalability_results
        
        # Log summary
        if scalability_results["status"] != "failed":
            self.log(f"✓ dbench {test_name} completed", "SUCCESS")
            self._log_scalability_summary(scalability_results)
    
    def _dbench_latency_test(self):
        """
        Run latency-focused test with single client.
        
        Single-client test with fsync enabled for accurate latency measurement.
        """
        test_name = "latency_test"
        test_config = self.config.get(test_name, {})
        
        if not test_config.get('enabled', True):
            self.log(f"Skipping {test_name} (disabled in config)", "INFO")
            self.results[test_name] = {"status": "skipped", "reason": "disabled"}
            return
        
        self.log(f"\nRunning dbench {test_name}...", "INFO")
        self._run_dbench_test(test_name, test_config)
    
    def _dbench_sustained_load(self):
        """
        Run sustained load test for stability.
        
        Long-running test to verify consistent performance over time.
        """
        test_name = "sustained_load"
        test_config = self.config.get(test_name, {})
        
        if not test_config.get('enabled', True):
            self.log(f"Skipping {test_name} (disabled in config)", "INFO")
            self.results[test_name] = {"status": "skipped", "reason": "disabled"}
            return
        
        self.log(f"\nRunning dbench {test_name}...", "INFO")
        self._run_dbench_test(test_name, test_config)
    
    def _dbench_rate_limited_test(self):
        """
        Run rate-limited test with controlled throughput.
        
        Tests performance under rate limiting to simulate bandwidth constraints.
        """
        test_name = "rate_limited_test"
        test_config = self.config.get(test_name, {})
        
        if not test_config.get('enabled', True):
            self.log(f"Skipping {test_name} (disabled in config)", "INFO")
            self.results[test_name] = {"status": "skipped", "reason": "disabled"}
            return
        
        self.log(f"\nRunning dbench {test_name}...", "INFO")
        self._run_dbench_test(test_name, test_config)
    
    def _dbench_metadata_intensive(self):
        """
        Run metadata-intensive test with small files.
        
        Focuses on metadata operations using small file workload.
        """
        test_name = "metadata_intensive"
        test_config = self.config.get(test_name, {})
        
        if not test_config.get('enabled', True):
            self.log(f"Skipping {test_name} (disabled in config)", "INFO")
            self.results[test_name] = {"status": "skipped", "reason": "disabled"}
            return
        
        self.log(f"\nRunning dbench {test_name}...", "INFO")
        self._run_dbench_test(test_name, test_config)
    
    def _run_dbench_test(self, test_name: str, test_config: Dict[str, Any]):
        """
        Run a dbench test and store results.
        
        Args:
            test_name: Name of the test
            test_config: Test configuration
        """
        result = self._run_dbench_test_internal(test_name, test_config)
        if result:
            self.results[test_name] = result
    
    def _run_dbench_test_internal(
        self,
        test_name: str,
        test_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Internal method to run a dbench test and parse results.
        
        Args:
            test_name: Name of the test
            test_config: Test configuration
            
        Returns:
            dict: Test results or None if failed
        """
        try:
            # Ensure test directory exists
            self.test_dir.mkdir(parents=True, exist_ok=True)
            
            # Start metrics collection
            self._start_metrics_collection()
            
            # Build command
            cmd = self._build_dbench_command(test_config)
            
            self.log(f"Command: {' '.join(cmd)}", "DEBUG")
            
            # Run test
            start_time = time.time()
            result = self.run_command_with_timeout(
                cmd,
                timeout=test_config.get('duration', 300) + 120  # Add 2 min buffer
            )
            duration = time.time() - start_time
            
            # Stop metrics collection
            system_metrics = self._stop_metrics_collection()
            
            if result.returncode != 0:
                self.log(f"dbench {test_name} failed: {result.stderr}", "ERROR")
                return {
                    "status": "failed",
                    "error": result.stderr,
                    "duration_seconds": duration
                }
            
            # Parse output
            metrics = self._parse_dbench_output(result.stdout)
            
            if not metrics:
                self.log(f"Failed to parse dbench output", "ERROR")
                return {
                    "status": "failed",
                    "error": "Failed to parse output",
                    "duration_seconds": duration,
                    "raw_output": result.stdout[:500]
                }
            
            # Add test configuration info
            metrics["status"] = "passed"
            metrics["duration_seconds"] = duration
            metrics["num_clients"] = test_config.get('num_clients', 1)
            metrics["config"] = {
                "duration": test_config.get('duration'),
                "loadfile": test_config.get('loadfile'),
                "target_rate": test_config.get('target_rate', 0),
                "fsync": test_config.get('fsync', False)
            }
            
            # Add metrics - properly separated
            if system_metrics:
                if 'system' in system_metrics:
                    metrics["system_metrics"] = system_metrics['system']
                if 'nfs' in system_metrics:
                    metrics["nfs_metrics"] = system_metrics['nfs']
            
            # Validate throughput if network intelligence is available
            if self.network_intel and 'throughput_mbps' in metrics:
                validation = self._validate_throughput(
                    metrics['throughput_mbps'],
                    "sequential"
                )
                metrics['network_validation'] = validation
            
            # Log success
            self.log(f"✓ dbench {test_name} completed", "SUCCESS")
            self._log_dbench_summary(metrics)
            
            return metrics
            
        except subprocess.TimeoutExpired:
            self._stop_metrics_collection()
            self.log(f"dbench {test_name} timed out", "ERROR")
            return {
                "status": "failed",
                "error": "Test timed out"
            }
        except Exception as e:
            self._stop_metrics_collection()
            self.log(f"dbench {test_name} error: {e}", "ERROR")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _parse_dbench_output(self, output: str) -> Optional[Dict[str, Any]]:
        """
        Parse dbench output to extract metrics.
        
        dbench output format (machine-readable):
        Throughput 856.234 MB/sec  8 clients  8 procs  max_latency=45.123 ms
        
        Or detailed format:
        Operation      Count    AvgLat    MaxLat
        NTCreateX      45000     0.123     12.456
        Close          45000     0.089      8.234
        ...
        
        Args:
            output: Raw dbench output
            
        Returns:
            dict: Parsed metrics or None if parsing fails
        """
        try:
            metrics = {}
            parse_warnings = []
            
            # Parse throughput line
            throughput_pattern = r'Throughput\s+([\d.]+)\s+MB/sec\s+(\d+)\s+clients?\s+(\d+)\s+procs?\s+max_latency=([\d.]+)\s+ms'
            match = re.search(throughput_pattern, output)
            
            if match:
                try:
                    metrics['throughput_mbps'] = float(match.group(1))
                except (ValueError, AttributeError) as e:
                    parse_warnings.append(f"Failed to parse throughput: {e}")
                
                try:
                    metrics['num_clients'] = int(match.group(2))
                except (ValueError, AttributeError) as e:
                    parse_warnings.append(f"Failed to parse num_clients: {e}")
                
                try:
                    metrics['num_procs'] = int(match.group(3))
                except (ValueError, AttributeError) as e:
                    parse_warnings.append(f"Failed to parse num_procs: {e}")
                
                try:
                    metrics['max_latency_ms'] = float(match.group(4))
                except (ValueError, AttributeError) as e:
                    parse_warnings.append(f"Failed to parse max_latency: {e}")
            else:
                # Try alternative format
                alt_pattern = r'Throughput\s+([\d.]+)\s+MB/sec'
                match = re.search(alt_pattern, output)
                if match:
                    try:
                        metrics['throughput_mbps'] = float(match.group(1))
                    except (ValueError, AttributeError) as e:
                        parse_warnings.append(f"Failed to parse throughput (alt format): {e}")
            
            # Parse operation statistics if available
            operations = {}
            op_pattern = r'(\w+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)'
            
            for line in output.split('\n'):
                match = re.match(op_pattern, line.strip())
                if match:
                    try:
                        op_name = match.group(1).lower()
                        count = int(match.group(2))
                        avg_lat = float(match.group(3))
                        max_lat = float(match.group(4))
                        
                        operations[op_name] = {
                            "count": count,
                            "avg_latency_ms": avg_lat,
                            "max_latency_ms": max_lat
                        }
                    except (ValueError, AttributeError, IndexError) as e:
                        parse_warnings.append(f"Failed to parse operation line '{line.strip()}': {e}")
                        continue
            
            if operations:
                metrics['operations'] = operations
                
                try:
                    # Calculate total operations
                    total_ops = sum(op['count'] for op in operations.values())
                    metrics['total_operations'] = total_ops
                    
                    # Calculate average latency across all operations
                    if total_ops > 0:
                        weighted_latency = sum(
                            op['count'] * op['avg_latency_ms']
                            for op in operations.values()
                        )
                        metrics['avg_latency_ms'] = weighted_latency / total_ops
                except (KeyError, TypeError, ZeroDivisionError) as e:
                    parse_warnings.append(f"Failed to calculate aggregate metrics: {e}")
            
            # Log any parsing warnings
            if parse_warnings:
                self.log(f"Parsing warnings ({len(parse_warnings)} issues):", "WARNING")
                for warning in parse_warnings[:5]:  # Limit to first 5 warnings
                    self.log(f"  - {warning}", "WARNING")
                if len(parse_warnings) > 5:
                    self.log(f"  ... and {len(parse_warnings) - 5} more", "WARNING")
            
            # Return metrics if we got at least throughput
            if 'throughput_mbps' in metrics:
                return metrics
            else:
                self.log("No throughput data found in output", "ERROR")
                return None
            
        except Exception as e:
            self.log(f"Error parsing dbench output: {e}", "ERROR")
            self.log(f"Output was: {output[:500]}", "DEBUG")
            return None
    
    def _log_dbench_summary(self, metrics: Dict[str, Any]):
        """
        Log a summary of dbench test results.
        
        Args:
            metrics: Parsed metrics dictionary
        """
        self.log("  Results:", "INFO")
        
        if 'throughput_mbps' in metrics:
            self.log(f"    Throughput: {metrics['throughput_mbps']:.2f} MB/s", "INFO")
        
        if 'num_clients' in metrics:
            self.log(f"    Clients: {metrics['num_clients']}", "INFO")
        
        if 'avg_latency_ms' in metrics:
            self.log(f"    Avg Latency: {metrics['avg_latency_ms']:.2f} ms", "INFO")
        
        if 'max_latency_ms' in metrics:
            self.log(f"    Max Latency: {metrics['max_latency_ms']:.2f} ms", "INFO")
        
        if 'total_operations' in metrics:
            duration = metrics.get('duration_seconds', 0)
            if duration > 0:
                ops_per_sec = metrics['total_operations'] / duration
                self.log(f"    Operations/sec: {ops_per_sec:.2f}", "INFO")
    
    def _log_scalability_summary(self, results: Dict[str, Any]):
        """
        Log a summary of scalability test results.
        
        Args:
            results: Scalability test results
        """
        self.log("  Scalability Results:", "INFO")
        
        for num_clients, metrics in results.get('results', {}).items():
            throughput = metrics.get('throughput_mbps', 0)
            self.log(f"    {num_clients} clients: {throughput:.2f} MB/s", "INFO")


# Made with Bob