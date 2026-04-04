#!/usr/bin/env python3
"""
NFS Metrics Collector for NFS Performance Testing

This module provides comprehensive NFS-level metrics collection including:
- nfsstat: NFS operation statistics
- mountstats: Per-mount NFS statistics including transport (xprt) stats
- RPC metrics: Retransmissions, timeouts, latency
- Transport metrics: Connection stats, queue times, bad XIDs
- Network-level NFS behavior

These metrics are critical for diagnosing NFS performance issues and
understanding where bottlenecks occur.
"""

import subprocess
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from threading import Thread, Event

from .command_utils import run_command_with_timeout, check_command_exists


class NFSMetricsCollector:
    """
    Collects NFS-specific metrics during test execution.
    
    This class captures:
    - NFS operation counts and rates (via nfsstat)
    - RPC statistics including retransmissions and timeouts
    - Per-mount statistics (via mountstats)
    - Transport (xprt) statistics: connections, queue times, bad XIDs
    - NFS protocol-level latency
    
    Attributes:
        mount_path: NFS mount point to monitor
        logger: Logger instance for output
        collection_interval: Seconds between metric collections
        _collecting: Flag to control collection thread
        _thread: Background collection thread
        _start_metrics: Metrics at start of collection
        _end_metrics: Metrics at end of collection
        _samples: List of metric samples during collection
    """
    
    def __init__(self, mount_path: Path, logger, collection_interval: float = 1.0):
        """
        Initialize NFS metrics collector.
        
        Args:
            mount_path: Path to NFS mount point
            logger: Logger instance for output
            collection_interval: Seconds between collections (default: 1.0)
        """
        self.mount_path = mount_path
        self.logger = logger
        self.collection_interval = collection_interval
        
        self._collecting = Event()
        self._thread = None
        self._start_metrics = {}
        self._end_metrics = {}
        self._samples = []
        
        # Check if tools are available
        self._has_nfsstat = self._check_command('nfsstat')
        self._has_mountstats = self._check_mountstats()
        
        if not self._has_nfsstat:
            self.logger.warning("nfsstat command not available - NFS metrics will be limited")
        if not self._has_mountstats:
            self.logger.warning("mountstats not available - per-mount metrics will be limited")
    
    def _check_command(self, command: str) -> bool:
        """Check if a command is available."""
        return check_command_exists(command)
    
    def _check_mountstats(self) -> bool:
        """Check if mountstats is available."""
        # mountstats is typically in /proc/self/mountstats
        return Path('/proc/self/mountstats').exists()
    
    def start(self):
        """Start collecting NFS metrics in background."""
        if not self._has_nfsstat and not self._has_mountstats:
            self.logger.warning("No NFS metric tools available - skipping NFS metrics collection")
            return
        
        self._collecting.set()
        self._samples = []
        
        # Collect initial metrics
        self._start_metrics = self._collect_nfs_metrics()
        
        # Start background collection thread
        self._thread = Thread(target=self._collect_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop collecting NFS metrics."""
        if not self._collecting.is_set():
            return
        
        self._collecting.clear()
        
        if self._thread:
            self._thread.join(timeout=5.0)
        
        # Collect final metrics
        self._end_metrics = self._collect_nfs_metrics()
    
    def _collect_loop(self):
        """Background loop to collect periodic samples."""
        while self._collecting.is_set():
            try:
                sample = self._collect_nfs_metrics()
                sample['timestamp'] = time.time()
                self._samples.append(sample)
            except Exception as e:
                self.logger.debug(f"Error collecting NFS metrics sample: {e}")
            
            time.sleep(self.collection_interval)
    
    def _collect_nfs_metrics(self) -> Dict[str, Any]:
        """
        Collect current NFS metrics.
        
        Returns:
            dict: Current NFS metrics including operations, RPC stats, etc.
        """
        metrics = {}
        
        if self._has_nfsstat:
            metrics.update(self._collect_nfsstat())
        
        if self._has_mountstats:
            metrics.update(self._collect_mountstats())
        
        return metrics
    
    def _collect_nfsstat(self) -> Dict[str, Any]:
        """
        Collect NFS statistics using nfsstat command.
        
        Returns:
            dict: NFS operation statistics
        """
        metrics = {}
        
        try:
            # Get client statistics with retry for transient failures
            result = run_command_with_timeout(
                ['nfsstat', '-c'],
                timeout=5,
                capture_output=True,
                text=True,
                retry=True,
                max_retries=2,
                retry_delay=0.5,
                logger=self.logger
            )
            
            if result.returncode == 0:
                metrics['nfs_client'] = self._parse_nfsstat_client(result.stdout)
            
            # Get RPC statistics with retry for transient failures
            result = run_command_with_timeout(
                ['nfsstat', '-r'],
                timeout=5,
                capture_output=True,
                text=True,
                retry=True,
                max_retries=2,
                retry_delay=0.5,
                logger=self.logger
            )
            
            if result.returncode == 0:
                metrics['rpc'] = self._parse_nfsstat_rpc(result.stdout)
            
        except subprocess.TimeoutExpired:
            self.logger.debug("nfsstat command timed out")
        except Exception as e:
            self.logger.debug(f"Error collecting nfsstat: {e}")
        
        return metrics
    
    def _parse_nfsstat_client(self, output: str) -> Dict[str, Any]:
        """
        Parse nfsstat client output.
        
        Args:
            output: nfsstat -c output
            
        Returns:
            dict: Parsed NFS client statistics
        """
        stats = {
            'operations': {},
            'total_ops': 0
        }
        
        # Parse NFS operation counts
        # Example line: "read         write        create       remove"
        #               "12345        67890        111          222"
        
        lines = output.split('\n')
        for i, line in enumerate(lines):
            # Look for operation names
            if 'read' in line.lower() and 'write' in line.lower():
                op_names = line.split()
                if i + 1 < len(lines):
                    op_values = lines[i + 1].split()
                    for name, value in zip(op_names, op_values):
                        try:
                            stats['operations'][name] = int(value)
                            stats['total_ops'] += int(value)
                        except ValueError:
                            continue
        
        return stats
    
    def _parse_nfsstat_rpc(self, output: str) -> Dict[str, Any]:
        """
        Parse nfsstat RPC output.
        
        Args:
            output: nfsstat -r output
            
        Returns:
            dict: Parsed RPC statistics including retransmissions
        """
        stats = {
            'calls': 0,
            'retransmissions': 0,
            'timeouts': 0,
            'invalid_replies': 0,
            'retrans_percent': 0.0
        }
        
        # Parse RPC statistics
        # Example: "12345 calls, 123 retrans (1%), 5 timeouts"
        
        for line in output.split('\n'):
            # Total calls
            match = re.search(r'(\d+)\s+calls', line)
            if match:
                stats['calls'] = int(match.group(1))
            
            # Retransmissions
            match = re.search(r'(\d+)\s+retrans', line)
            if match:
                stats['retransmissions'] = int(match.group(1))
            
            # Retransmission percentage
            match = re.search(r'retrans.*?\((\d+(?:\.\d+)?)\%\)', line)
            if match:
                stats['retrans_percent'] = float(match.group(1))
            
            # Timeouts
            match = re.search(r'(\d+)\s+timeouts', line)
            if match:
                stats['timeouts'] = int(match.group(1))
            
            # Invalid replies
            match = re.search(r'(\d+)\s+invalid', line)
            if match:
                stats['invalid_replies'] = int(match.group(1))
        
        return stats
    
    def _collect_mountstats(self) -> Dict[str, Any]:
        """
        Collect per-mount NFS statistics from /proc/self/mountstats.
        
        Returns:
            dict: Per-mount NFS statistics
        """
        metrics = {}
        
        try:
            with open('/proc/self/mountstats', 'r') as f:
                content = f.read()
            
            # Find our mount point
            mount_stats = self._parse_mountstats(content)
            if mount_stats:
                metrics['mountstats'] = mount_stats
        
        except Exception as e:
            self.logger.debug(f"Error collecting mountstats: {e}")
        
        return metrics
    
    def _parse_mountstats(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse mountstats content for our mount point.
        
        Args:
            content: Content of /proc/self/mountstats
            
        Returns:
            dict: Parsed mount statistics or None
        """
        stats = None
        mount_path_str = str(self.mount_path)
        
        # Split into mount sections
        sections = content.split('device ')
        
        for section in sections:
            if mount_path_str in section:
                stats = self._parse_mount_section(section)
                break
        
        return stats
    
    def _parse_mount_section(self, section: str) -> Dict[str, Any]:
        """
        Parse a single mount section from mountstats.
        
        Args:
            section: Mount section text
            
        Returns:
            dict: Parsed statistics for this mount
        """
        stats = {
            'bytes_read': 0,
            'bytes_written': 0,
            'read_ops': 0,
            'write_ops': 0,
            'rpc_backlog': 0,
            'rpc_ops': {},
            'rpc_latency': {},
            'xprt': {}
        }
        
        lines = section.split('\n')
        
        for line in lines:
            # Bytes read/written
            if 'bytes:' in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'read:' and i + 1 < len(parts):
                        try:
                            stats['bytes_read'] = int(parts[i + 1])
                        except ValueError:
                            pass
                    elif part == 'write:' and i + 1 < len(parts):
                        try:
                            stats['bytes_written'] = int(parts[i + 1])
                        except ValueError:
                            pass
            
            # Transport statistics (xprt:)
            # Format: xprt: tcp srcport bind_count connect_count connect_time idle_time sends recvs bad_xids req_u resp_u max_slots sending_queue pending_queue
            if line.strip().startswith('xprt:'):
                parts = line.split()
                if len(parts) >= 14:
                    try:
                        stats['xprt'] = {
                            'protocol': parts[1],  # tcp or udp
                            'srcport': int(parts[2]),
                            'bind_count': int(parts[3]),
                            'connect_count': int(parts[4]),
                            'connect_time': int(parts[5]),
                            'idle_time': int(parts[6]),
                            'sends': int(parts[7]),
                            'recvs': int(parts[8]),
                            'bad_xids': int(parts[9]),  # Bad transaction IDs
                            'req_queue_time': int(parts[10]),  # Cumulative request queue time
                            'resp_queue_time': int(parts[11]),  # Cumulative response queue time
                            'max_slots': int(parts[12]),
                            'sending_queue': int(parts[13]),
                            'pending_queue': int(parts[14]) if len(parts) > 14 else 0
                        }
                    except (ValueError, IndexError) as e:
                        self.logger.debug(f"Error parsing xprt line: {e}")
            
            # Per-operation statistics
            # Format: "OP: ops trans timeouts bytes_sent bytes_recv queue_time_ms rtt_ms execute_time_ms errors"
            # Example: "READ: 90 90 0 20880 13882632 20 18374 18406 0"
            if line.strip().startswith(('READ:', 'WRITE:', 'GETATTR:', 'LOOKUP:', 'ACCESS:',
                                       'COMMIT:', 'OPEN:', 'CLOSE:', 'SETATTR:', 'FSINFO:',
                                       'READDIR:', 'SERVER_CAPS:', 'DELEGRETURN:', 'GETACL:',
                                       'SETACL:', 'EXCHANGE_ID:', 'CREATE_SESSION:', 'SEQUENCE:')):
                parts = line.split()
                if len(parts) >= 2:
                    op_name = parts[0].rstrip(':')
                    try:
                        ops_count = int(parts[1])
                        
                        # Initialize operation stats
                        stats['rpc_ops'][op_name] = {
                            'ops': ops_count,
                            'trans': int(parts[2]) if len(parts) > 2 else 0,
                            'timeouts': int(parts[3]) if len(parts) > 3 else 0,
                            'bytes_sent': int(parts[4]) if len(parts) > 4 else 0,
                            'bytes_recv': int(parts[5]) if len(parts) > 5 else 0,
                            'queue_time_ms': int(parts[6]) if len(parts) > 6 else 0,
                            'rtt_ms': int(parts[7]) if len(parts) > 7 else 0,
                            'execute_time_ms': int(parts[8]) if len(parts) > 8 else 0,
                            'errors': int(parts[9]) if len(parts) > 9 else 0
                        }
                        
                        # Calculate average times if ops > 0
                        if ops_count > 0:
                            stats['rpc_ops'][op_name]['avg_queue_ms'] = round(
                                stats['rpc_ops'][op_name]['queue_time_ms'] / ops_count, 3
                            )
                            stats['rpc_ops'][op_name]['avg_rtt_ms'] = round(
                                stats['rpc_ops'][op_name]['rtt_ms'] / ops_count, 3
                            )
                            stats['rpc_ops'][op_name]['avg_exe_ms'] = round(
                                stats['rpc_ops'][op_name]['execute_time_ms'] / ops_count, 3
                            )
                        
                        # Track read/write ops
                        if op_name == 'READ':
                            stats['read_ops'] = ops_count
                        elif op_name == 'WRITE':
                            stats['write_ops'] = ops_count
                    except (ValueError, IndexError):
                        pass
            
            # RPC backlog
            if 'backlog' in line:
                match = re.search(r'backlog:\s*(\d+)', line)
                if match:
                    stats['rpc_backlog'] = int(match.group(1))
        
        return stats
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of NFS metrics collected during the test.
        
        Returns:
            dict: Summary including deltas, rates, and key metrics
        """
        if not self._start_metrics and not self._end_metrics:
            return {}
        
        summary = {
            'collection_available': True,
            'start_metrics': self._start_metrics,
            'end_metrics': self._end_metrics,
            'deltas': {},
            'rates': {},
            'issues': []
        }
        
        # Calculate deltas and rates
        if self._start_metrics and self._end_metrics:
            summary['deltas'] = self._calculate_deltas(
                self._start_metrics,
                self._end_metrics
            )
            
            # Calculate rates if we have samples
            if len(self._samples) >= 2:
                duration = self._samples[-1]['timestamp'] - self._samples[0]['timestamp']
                if duration > 0:
                    summary['rates'] = self._calculate_rates(
                        summary['deltas'],
                        duration
                    )
        
        # Analyze for issues
        summary['issues'] = self._analyze_issues(summary)
        
        # Add sample statistics
        if self._samples:
            summary['sample_count'] = len(self._samples)
            summary['collection_duration'] = (
                self._samples[-1]['timestamp'] - self._samples[0]['timestamp']
            )
        
        return summary
    
    def _calculate_deltas(self, start: Dict[str, Any], end: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate deltas between start and end metrics.
        
        Args:
            start: Starting metrics
            end: Ending metrics
            
        Returns:
            dict: Delta values
        """
        deltas = {}
        
        # RPC deltas
        if 'rpc' in start and 'rpc' in end:
            deltas['rpc'] = {}
            for key in ['calls', 'retransmissions', 'timeouts', 'invalid_replies']:
                if key in start['rpc'] and key in end['rpc']:
                    deltas['rpc'][key] = end['rpc'][key] - start['rpc'][key]
        
        # Mountstats deltas
        if 'mountstats' in start and 'mountstats' in end:
            deltas['mountstats'] = {}
            for key in ['bytes_read', 'bytes_written', 'read_ops', 'write_ops']:
                if key in start['mountstats'] and key in end['mountstats']:
                    deltas['mountstats'][key] = (
                        end['mountstats'][key] - start['mountstats'][key]
                    )
            
            # Transport (xprt) deltas
            if 'xprt' in start['mountstats'] and 'xprt' in end['mountstats']:
                deltas['xprt'] = {}
                start_xprt = start['mountstats']['xprt']
                end_xprt = end['mountstats']['xprt']
                
                for key in ['bind_count', 'connect_count', 'connect_time', 'idle_time',
                           'sends', 'recvs', 'bad_xids', 'req_queue_time', 'resp_queue_time',
                           'sending_queue', 'pending_queue']:
                    if key in start_xprt and key in end_xprt:
                        deltas['xprt'][key] = end_xprt[key] - start_xprt[key]
                
                # Copy non-delta fields
                if 'protocol' in end_xprt:
                    deltas['xprt']['protocol'] = end_xprt['protocol']
                if 'max_slots' in end_xprt:
                    deltas['xprt']['max_slots'] = end_xprt['max_slots']
            
            # Per-operation timing deltas (from mountstats rpc_ops)
            if 'rpc_ops' in start['mountstats'] and 'rpc_ops' in end['mountstats']:
                deltas['per_op_stats'] = {}
                start_rpc_ops = start['mountstats']['rpc_ops']
                end_rpc_ops = end['mountstats']['rpc_ops']
                
                # Get all operations that occurred
                all_ops = set(start_rpc_ops.keys()) | set(end_rpc_ops.keys())
                
                for op_name in all_ops:
                    start_op = start_rpc_ops.get(op_name, {})
                    end_op = end_rpc_ops.get(op_name, {})
                    
                    # Calculate deltas for this operation
                    ops_delta = end_op.get('ops', 0) - start_op.get('ops', 0)
                    
                    if ops_delta > 0:  # Only include ops that actually occurred
                        deltas['per_op_stats'][op_name] = {
                            'ops': ops_delta,
                            'timeouts': end_op.get('timeouts', 0) - start_op.get('timeouts', 0),
                            'bytes_sent': end_op.get('bytes_sent', 0) - start_op.get('bytes_sent', 0),
                            'bytes_recv': end_op.get('bytes_recv', 0) - start_op.get('bytes_recv', 0),
                            'queue_time_ms': end_op.get('queue_time_ms', 0) - start_op.get('queue_time_ms', 0),
                            'rtt_ms': end_op.get('rtt_ms', 0) - start_op.get('rtt_ms', 0),
                            'execute_time_ms': end_op.get('execute_time_ms', 0) - start_op.get('execute_time_ms', 0),
                            'errors': end_op.get('errors', 0) - start_op.get('errors', 0)
                        }
                        
                        # Calculate averages for this delta period
                        deltas['per_op_stats'][op_name]['avg_queue_ms'] = round(
                            deltas['per_op_stats'][op_name]['queue_time_ms'] / ops_delta, 3
                        )
                        deltas['per_op_stats'][op_name]['avg_rtt_ms'] = round(
                            deltas['per_op_stats'][op_name]['rtt_ms'] / ops_delta, 3
                        )
                        deltas['per_op_stats'][op_name]['avg_exe_ms'] = round(
                            deltas['per_op_stats'][op_name]['execute_time_ms'] / ops_delta, 3
                        )
                        
                        # Calculate total latency (queue + RTT + execute)
                        deltas['per_op_stats'][op_name]['avg_total_latency_ms'] = round(
                            deltas['per_op_stats'][op_name]['avg_queue_ms'] +
                            deltas['per_op_stats'][op_name]['avg_rtt_ms'] +
                            deltas['per_op_stats'][op_name]['avg_exe_ms'], 3
                        )
        
        # NFS client operation deltas
        if 'nfs_client' in start and 'nfs_client' in end:
            deltas['nfs_operations'] = {}
            start_ops = start['nfs_client'].get('operations', {})
            end_ops = end['nfs_client'].get('operations', {})
            
            for op_name in set(start_ops.keys()) | set(end_ops.keys()):
                start_val = start_ops.get(op_name, 0)
                end_val = end_ops.get(op_name, 0)
                deltas['nfs_operations'][op_name] = end_val - start_val
        
        return deltas
    
    def _calculate_rates(self, deltas: Dict[str, Any], duration: float) -> Dict[str, Any]:
        """
        Calculate rates from deltas.
        
        Args:
            deltas: Delta values
            duration: Duration in seconds
            
        Returns:
            dict: Rate values (per second)
        """
        rates = {}
        
        if duration <= 0:
            return rates
        
        # RPC rates
        if 'rpc' in deltas:
            rates['rpc'] = {}
            for key, value in deltas['rpc'].items():
                rates['rpc'][f'{key}_per_sec'] = round(value / duration, 2)
            
            # Calculate retransmission rate
            if 'calls' in deltas['rpc'] and deltas['rpc']['calls'] > 0:
                retrans = deltas['rpc'].get('retransmissions', 0)
                rates['rpc']['retrans_percent'] = round(
                    (retrans / deltas['rpc']['calls']) * 100, 2
                )
        
        # Throughput rates
        if 'mountstats' in deltas:
            rates['throughput'] = {}
            if 'bytes_read' in deltas['mountstats']:
                mb_read = deltas['mountstats']['bytes_read'] / (1024 * 1024)
                rates['throughput']['read_mbps'] = round(mb_read / duration, 2)
            
            if 'bytes_written' in deltas['mountstats']:
                mb_written = deltas['mountstats']['bytes_written'] / (1024 * 1024)
                rates['throughput']['write_mbps'] = round(mb_written / duration, 2)
            
            # IOPS
            if 'read_ops' in deltas['mountstats']:
                rates['throughput']['read_iops'] = round(
                    deltas['mountstats']['read_ops'] / duration, 2
                )
            
            if 'write_ops' in deltas['mountstats']:
                rates['throughput']['write_iops'] = round(
                    deltas['mountstats']['write_ops'] / duration, 2
                )
        
        # Transport (xprt) rates
        if 'xprt' in deltas:
            rates['xprt'] = {}
            
            # Connection rates
            if 'connect_count' in deltas['xprt']:
                rates['xprt']['connects_per_sec'] = round(
                    deltas['xprt']['connect_count'] / duration, 2
                )
            
            # Send/Receive rates
            if 'sends' in deltas['xprt']:
                rates['xprt']['sends_per_sec'] = round(
                    deltas['xprt']['sends'] / duration, 2
                )
            
            if 'recvs' in deltas['xprt']:
                rates['xprt']['recvs_per_sec'] = round(
                    deltas['xprt']['recvs'] / duration, 2
                )
            
            # Bad XIDs rate (transaction ID mismatches)
            if 'bad_xids' in deltas['xprt']:
                rates['xprt']['bad_xids_per_sec'] = round(
                    deltas['xprt']['bad_xids'] / duration, 2
                )
            
            # Average queue times (microseconds)
            if 'req_queue_time' in deltas['xprt'] and 'sends' in deltas['xprt']:
                if deltas['xprt']['sends'] > 0:
                    rates['xprt']['avg_req_queue_time_us'] = round(
                        deltas['xprt']['req_queue_time'] / deltas['xprt']['sends'], 2
                    )
            
            if 'resp_queue_time' in deltas['xprt'] and 'recvs' in deltas['xprt']:
                if deltas['xprt']['recvs'] > 0:
                    rates['xprt']['avg_resp_queue_time_us'] = round(
                        deltas['xprt']['resp_queue_time'] / deltas['xprt']['recvs'], 2
                    )
            
            # Copy non-rate fields
            if 'protocol' in deltas['xprt']:
                rates['xprt']['protocol'] = deltas['xprt']['protocol']
            if 'max_slots' in deltas['xprt']:
                rates['xprt']['max_slots'] = deltas['xprt']['max_slots']
            if 'sending_queue' in deltas['xprt']:
                rates['xprt']['sending_queue'] = deltas['xprt']['sending_queue']
            if 'pending_queue' in deltas['xprt']:
                rates['xprt']['pending_queue'] = deltas['xprt']['pending_queue']
        
        return rates
    
    def _analyze_issues(self, summary: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Analyze metrics for potential issues.
        
        Args:
            summary: Metrics summary
            
        Returns:
            list: List of detected issues with severity and description
        """
        issues = []
        
        # Check retransmission rate
        rates = summary.get('rates', {})
        rpc_rates = rates.get('rpc', {})
        
        retrans_percent = rpc_rates.get('retrans_percent', 0)
        if retrans_percent > 5:
            issues.append({
                'severity': 'critical',
                'category': 'retransmissions',
                'message': f'High retransmission rate: {retrans_percent:.2f}% (threshold: 5%)',
                'impact': 'Indicates network issues or server overload'
            })
        elif retrans_percent > 1:
            issues.append({
                'severity': 'warning',
                'category': 'retransmissions',
                'message': f'Elevated retransmission rate: {retrans_percent:.2f}% (threshold: 1%)',
                'impact': 'May indicate intermittent network issues'
            })
        
        # Check timeouts
        deltas = summary.get('deltas', {})
        rpc_deltas = deltas.get('rpc', {})
        
        timeouts = rpc_deltas.get('timeouts', 0)
        if timeouts > 0:
            issues.append({
                'severity': 'critical',
                'category': 'timeouts',
                'message': f'{timeouts} RPC timeouts detected',
                'impact': 'Severe network or server issues causing request failures'
            })
        
        # Check invalid replies
        invalid = rpc_deltas.get('invalid_replies', 0)
        if invalid > 0:
            issues.append({
                'severity': 'warning',
                'category': 'protocol',
                'message': f'{invalid} invalid RPC replies',
                'impact': 'Protocol errors or version mismatches'
            })
        
        # Check transport (xprt) issues
        xprt_deltas = deltas.get('xprt', {})
        xprt_rates = rates.get('xprt', {})
        
        # Check for bad transaction IDs
        bad_xids = xprt_deltas.get('bad_xids', 0)
        if bad_xids > 0:
            issues.append({
                'severity': 'critical',
                'category': 'transport',
                'message': f'{bad_xids} bad transaction IDs (XIDs) detected',
                'impact': 'Indicates duplicate replies, network issues, or server problems'
            })
        
        # Check for excessive reconnections
        connects = xprt_deltas.get('connect_count', 0)
        if connects > 10:
            issues.append({
                'severity': 'warning',
                'category': 'transport',
                'message': f'{connects} connection attempts during test',
                'impact': 'Frequent reconnections indicate network instability or server issues'
            })
        
        # Check for high queue times (> 1ms average)
        avg_req_queue = xprt_rates.get('avg_req_queue_time_us', 0)
        if avg_req_queue > 1000:
            issues.append({
                'severity': 'warning',
                'category': 'transport',
                'message': f'High average request queue time: {avg_req_queue:.2f}μs',
                'impact': 'Requests waiting too long before being sent - possible congestion'
            })
        
        avg_resp_queue = xprt_rates.get('avg_resp_queue_time_us', 0)
        if avg_resp_queue > 1000:
            issues.append({
                'severity': 'warning',
                'category': 'transport',
                'message': f'High average response queue time: {avg_resp_queue:.2f}μs',
                'impact': 'Responses waiting too long to be processed - possible client overload'
            })
        
        # Check for pending/sending queue buildup
        sending_queue = xprt_rates.get('sending_queue', 0)
        pending_queue = xprt_rates.get('pending_queue', 0)
        
        if sending_queue > 10:
            issues.append({
                'severity': 'warning',
                'category': 'transport',
                'message': f'High sending queue depth: {sending_queue}',
                'impact': 'Requests backing up before transmission - network congestion'
            })
        
        if pending_queue > 10:
            issues.append({
                'severity': 'warning',
                'category': 'transport',
                'message': f'High pending queue depth: {pending_queue}',
                'impact': 'Requests waiting for responses - server may be slow or overloaded'
            })
        
        # Analyze per-operation timing to identify bottlenecks
        per_op_stats = deltas.get('per_op_stats', {})
        if per_op_stats:
            # Categorize operations
            metadata_ops = ['GETATTR', 'LOOKUP', 'ACCESS', 'READDIR', 'FSINFO', 'PATHCONF']
            data_ops = ['READ', 'WRITE']
            
            # Find operations with high latency
            high_latency_ops = []
            high_queue_ops = []
            high_rtt_ops = []
            high_exe_ops = []
            ops_with_errors = []
            ops_with_timeouts = []
            metadata_issues = []
            
            for op_name, op_data in per_op_stats.items():
                avg_total = op_data.get('avg_total_latency_ms', 0)
                avg_queue = op_data.get('avg_queue_ms', 0)
                avg_rtt = op_data.get('avg_rtt_ms', 0)
                avg_exe = op_data.get('avg_exe_ms', 0)
                errors = op_data.get('errors', 0)
                timeouts = op_data.get('timeouts', 0)
                ops_count = op_data.get('ops', 0)
                
                # Check for metadata-specific issues
                if op_name in metadata_ops and avg_total > 50:
                    metadata_issues.append((op_name, avg_total, avg_queue, avg_rtt, avg_exe, ops_count))
                
                # High total latency (>100ms)
                if avg_total > 100:
                    high_latency_ops.append((op_name, avg_total, avg_queue, avg_rtt, avg_exe))
                
                # High queue time (>10ms) - client-side bottleneck
                if avg_queue > 10:
                    high_queue_ops.append((op_name, avg_queue, ops_count))
                
                # High RTT (>50ms) - network latency
                if avg_rtt > 50:
                    high_rtt_ops.append((op_name, avg_rtt, ops_count))
                
                # High execution time (>50ms) - server-side bottleneck
                if avg_exe > 50:
                    high_exe_ops.append((op_name, avg_exe, ops_count))
                
                # Operations with errors
                if errors > 0:
                    ops_with_errors.append((op_name, errors, ops_count))
                
                # Operations with timeouts
                if timeouts > 0:
                    ops_with_timeouts.append((op_name, timeouts, ops_count))
            
            # Root cause analysis with priority: RTT > Server Exec > Metadata > Client Queue
            root_cause_identified = False
            
            # Priority 1: Check for high RTT (network issues)
            if high_rtt_ops:
                high_rtt_ops.sort(key=lambda x: x[1], reverse=True)
                top_rtt_op = high_rtt_ops[0]
                op_name, rtt_time, ops_count = top_rtt_op
                
                issues.append({
                    'severity': 'critical',
                    'category': 'root_cause_network',
                    'message': f'ROOT CAUSE: High network RTT detected - {op_name}: {rtt_time:.1f}ms avg RTT ({ops_count} ops)',
                    'impact': 'Network latency is the primary bottleneck. Check network path, reduce hops, verify no packet loss, check for network congestion.'
                })
                root_cause_identified = True
            
            # Priority 2: Check for high server execution time
            elif high_exe_ops:
                high_exe_ops.sort(key=lambda x: x[1], reverse=True)
                top_exe_op = high_exe_ops[0]
                op_name, exe_time, ops_count = top_exe_op
                
                issues.append({
                    'severity': 'critical',
                    'category': 'root_cause_server',
                    'message': f'ROOT CAUSE: High server execution time - {op_name}: {exe_time:.1f}ms avg execution ({ops_count} ops)',
                    'impact': 'Server processing is the primary bottleneck. Check server CPU/memory load, storage performance (IOPS/latency), and server-side caching.'
                })
                root_cause_identified = True
            
            # Priority 3: Check for metadata bottlenecks
            elif metadata_issues:
                metadata_issues.sort(key=lambda x: x[1], reverse=True)
                top_meta = metadata_issues[0]
                op_name, total_lat, queue_lat, rtt_lat, exe_lat, ops_count = top_meta
                
                issues.append({
                    'severity': 'warning',
                    'category': 'root_cause_metadata',
                    'message': f'ROOT CAUSE: Metadata operation bottleneck - {op_name}: {total_lat:.1f}ms avg ({ops_count} ops)',
                    'impact': f'Metadata operations are slow (queue:{queue_lat:.1f}ms, rtt:{rtt_lat:.1f}ms, exe:{exe_lat:.1f}ms). Check server metadata performance, inode cache, and directory structure complexity.'
                })
                root_cause_identified = True
            
            # Priority 4: Check for client-side queuing issues
            elif high_queue_ops:
                high_queue_ops.sort(key=lambda x: x[1], reverse=True)
                top_queue_op = high_queue_ops[0]
                op_name, queue_time, ops_count = top_queue_op
                
                issues.append({
                    'severity': 'warning',
                    'category': 'root_cause_client',
                    'message': f'ROOT CAUSE: Client-side queuing bottleneck - {op_name}: {queue_time:.1f}ms avg queue time ({ops_count} ops)',
                    'impact': 'Client cannot send requests fast enough. Check client CPU usage, reduce concurrent operations, or increase client resources.'
                })
                root_cause_identified = True
            
            # If root cause identified, add detailed breakdown for all high latency ops
            if root_cause_identified and high_latency_ops:
                high_latency_ops.sort(key=lambda x: x[1], reverse=True)
                for op_name, total_lat, queue_lat, rtt_lat, exe_lat in high_latency_ops[:5]:  # Top 5
                    issues.append({
                        'severity': 'info',
                        'category': 'latency_breakdown',
                        'message': f'{op_name}: {total_lat:.1f}ms total (Q:{queue_lat:.1f}ms + RTT:{rtt_lat:.1f}ms + Exe:{exe_lat:.1f}ms)',
                        'impact': 'Detailed timing breakdown for analysis'
                    })
            
            # Report operations with errors (always critical)
            if ops_with_errors:
                for op_name, error_count, ops_count in ops_with_errors:
                    error_rate = (error_count / ops_count * 100) if ops_count > 0 else 0
                    issues.append({
                        'severity': 'critical',
                        'category': 'operation_errors',
                        'message': f'{op_name}: {error_count} errors out of {ops_count} ops ({error_rate:.1f}%)',
                        'impact': 'Operation failures - check server logs and permissions'
                    })
            
            # Report operations with timeouts
            if ops_with_timeouts:
                for op_name, timeout_count, ops_count in ops_with_timeouts:
                    timeout_rate = (timeout_count / ops_count * 100) if ops_count > 0 else 0
                    issues.append({
                        'severity': 'critical',
                        'category': 'operation_timeouts',
                        'message': f'{op_name}: {timeout_count} timeouts out of {ops_count} ops ({timeout_rate:.1f}%)',
                        'impact': 'Operations timing out - server not responding or network issues'
                    })
        
        return issues


# Made with Bob