#!/usr/bin/env python3
"""
Performance Analyzer for NFS Test Results

This module analyzes test results and provides actionable insights,
root cause analysis, and recommendations for performance issues.
"""

from typing import Dict, Any, List, Tuple


class PerformanceAnalyzer:
    """Analyzes NFS performance test results and provides insights."""
    
    def __init__(self, results: Dict[str, Any]):
        """
        Initialize analyzer with test results.
        
        Supports both single-version and multi-version result formats.
        
        Args:
            results: Complete test results dictionary
        """
        self.results = results
        self.insights = []
        self.recommendations = []
        self.severity_counts = {'critical': 0, 'warning': 0, 'info': 0}
        
        # Detect result format
        self.is_multi_version = 'test_metadata' in results and 'results_by_version' in results
        
        # For multi-version, we'll analyze each version separately
        if self.is_multi_version:
            self.metadata = results.get('test_metadata', {})
            self.versions = results.get('results_by_version', {})
        else:
            self.metadata = None
            self.versions = None
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of test results.
        
        Supports both single-version and multi-version formats.
        
        Returns:
            dict: Analysis summary with insights and recommendations
        """
        if self.is_multi_version:
            return self._analyze_multi_version()
        else:
            return self._analyze_single_version()
    
    def _analyze_multi_version(self) -> Dict[str, Any]:
        """Analyze multi-version test results."""
        # Add multi-version specific insights
        self._add_insight('info', 'Multi-Version Test',
                        f"Tested {len(self.versions)} NFS version(s): {', '.join(self.versions.keys())}",
                        f"Transport: {self.metadata.get('transport', 'tcp').upper()}")
        
        # Analyze each version
        version_analyses = {}
        for version_key, version_results in self.versions.items():
            # Temporarily set results to this version for analysis
            original_results = self.results
            self.results = version_results
            self.is_multi_version = False  # Temporarily treat as single version
            
            try:
                version_analysis = self._analyze_single_version()
                version_analyses[version_key] = version_analysis
            except Exception as e:
                self._add_insight('warning', f'Analysis Error - {version_key}',
                                f'Failed to analyze {version_key}: {str(e)}',
                                'Check test results format.')
            
            # Restore
            self.results = original_results
            self.is_multi_version = True
        
        # Compare versions
        try:
            self._compare_versions()
        except Exception as e:
            self._add_insight('warning', 'Version Comparison Error',
                            f'Failed to compare versions: {str(e)}',
                            'Check test results format.')
        
        return {
            'insights': self.insights,
            'recommendations': self.recommendations,
            'severity_counts': self.severity_counts,
            'overall_health': self._calculate_health_score(),
            'version_analyses': version_analyses,
            'is_multi_version': True
        }
    
    def _analyze_single_version(self) -> Dict[str, Any]:
        """Analyze single-version test results."""
        # Analyze different aspects with error handling
        try:
            self._analyze_overall_performance()
        except Exception as e:
            self._add_insight('warning', 'Analysis Error',
                            f'Failed to analyze overall performance: {str(e)}',
                            'Check test results format.')
        
        try:
            self._analyze_nfs_metrics()
        except Exception as e:
            self._add_insight('warning', 'Analysis Error',
                            f'Failed to analyze NFS metrics: {str(e)}',
                            'Check NFS metrics format.')
        
        try:
            self._analyze_bottlenecks()
        except Exception as e:
            self._add_insight('warning', 'Analysis Error',
                            f'Failed to analyze bottlenecks: {str(e)}',
                            'Check test results format.')
        
        try:
            self._analyze_consistency()
        except Exception as e:
            self._add_insight('warning', 'Analysis Error',
                            f'Failed to analyze consistency: {str(e)}',
                            'Check test results format.')
        
        try:
            self._detect_saturation()
        except Exception as e:
            self._add_insight('warning', 'Analysis Error',
                            f'Failed to detect saturation: {str(e)}',
                            'Check scalability test results.')
        
        try:
            self._analyze_historical_comparison()
        except Exception as e:
            self._add_insight('warning', 'Analysis Error',
                            f'Failed to analyze historical comparison: {str(e)}',
                            'Check historical data availability.')
        
        try:
            self._generate_recommendations()
        except Exception as e:
            self._add_insight('warning', 'Analysis Error',
                            f'Failed to generate recommendations: {str(e)}',
                            'Review analysis results manually.')
        
        return {
            'insights': self.insights,
            'recommendations': self.recommendations,
            'severity_counts': self.severity_counts,
            'overall_health': self._calculate_health_score(),
            'is_multi_version': False
        }
    
    def _compare_versions(self):
        """Compare performance across NFS versions and transports."""
        if not self.versions or len(self.versions) < 2:
            return
        
        # Extract key metrics from each version
        version_metrics = {}
        for version_key, version_results in self.versions.items():
            metrics = {}
            
            # Extract throughput metrics
            if 'dd_tests' in version_results:
                dd = version_results['dd_tests']
                if 'sequential_write' in dd:
                    metrics['write_mbps'] = dd['sequential_write'].get('throughput_mbps', 0)
                if 'sequential_read' in dd:
                    metrics['read_mbps'] = dd['sequential_read'].get('throughput_mbps', 0)
            
            # Extract IOPS metrics
            if 'fio_tests' in version_results:
                fio = version_results['fio_tests']
                if 'random_read' in fio:
                    metrics['rand_read_iops'] = fio['random_read'].get('iops', 0)
                if 'random_write' in fio:
                    metrics['rand_write_iops'] = fio['random_write'].get('iops', 0)
                    
            # Extract latency metrics
            if 'fio_tests' in version_results:
                fio = version_results['fio_tests']
                if 'random_read' in fio:
                    metrics['latency_ms'] = fio['random_read'].get('avg_latency_ms', 0)
            
            version_metrics[version_key] = metrics
        
        # Parse version keys to separate NFS version and transport
        # Format: nfsv{version}_{transport}
        version_transport_map = {}
        for version_key in version_metrics.keys():
            parts = version_key.split('_')
            if len(parts) >= 2:
                nfs_version = parts[0]  # e.g., nfsv3, nfsv4.2
                transport = parts[1]     # e.g., tcp, rdma
                version_transport_map[version_key] = {'version': nfs_version, 'transport': transport}
        
        # Compare NFS versions (same transport)
        self._compare_by_nfs_version(version_metrics, version_transport_map)
        
        # Compare transports (same NFS version)
        self._compare_by_transport(version_metrics, version_transport_map)
        
        # Find overall best performer
        self._find_overall_best(version_metrics)
    
    def _compare_by_nfs_version(self, version_metrics, version_transport_map):
        """Compare performance across different NFS versions with same transport."""
        # Group by transport
        by_transport = {}
        for version_key, vt_info in version_transport_map.items():
            transport = vt_info['transport']
            if transport not in by_transport:
                by_transport[transport] = {}
            by_transport[transport][version_key] = version_metrics[version_key]
        
        # Compare within each transport group
        for transport, versions in by_transport.items():
            if len(versions) < 2:
                continue
                
            for metric_name in ['write_mbps', 'read_mbps', 'rand_read_iops', 'rand_write_iops']:
                values = {v: m.get(metric_name, 0) for v, m in versions.items() if m.get(metric_name, 0) > 0}
                if len(values) >= 2:
                    best_version = max(values, key=lambda k: values[k])
                    best_value = values[best_version]
                    worst_version = min(values, key=lambda k: values[k])
                    worst_value = values[worst_version]
                    
                    if best_value > worst_value * 1.1:  # At least 10% difference
                        improvement = ((best_value - worst_value) / worst_value) * 100
                        self._add_insight('info', f'NFS Version Comparison ({transport.upper()}) - {metric_name}',
                                        f'{best_version} performs {improvement:.1f}% better than {worst_version}',
                                        f'Best: {best_value:.1f}, Worst: {worst_value:.1f}')
    
    def _compare_by_transport(self, version_metrics, version_transport_map):
        """Compare performance across different transports with same NFS version."""
        # Group by NFS version
        by_nfs_version = {}
        for version_key, vt_info in version_transport_map.items():
            nfs_version = vt_info['version']
            if nfs_version not in by_nfs_version:
                by_nfs_version[nfs_version] = {}
            by_nfs_version[nfs_version][version_key] = version_metrics[version_key]
        
        # Compare within each NFS version group
        for nfs_version, transports in by_nfs_version.items():
            if len(transports) < 2:
                continue
            
            for metric_name in ['write_mbps', 'read_mbps', 'rand_read_iops', 'rand_write_iops', 'latency_ms']:
                values = {v: m.get(metric_name, 0) for v, m in transports.items() if m.get(metric_name, 0) > 0}
                if len(values) >= 2:
                    if metric_name == 'latency_ms':
                        # Lower is better for latency
                        best_transport = min(values, key=lambda k: values[k])
                        best_value = values[best_transport]
                        worst_transport = max(values, key=lambda k: values[k])
                        worst_value = values[worst_transport]
                        
                        if worst_value > best_value * 1.1:  # At least 10% difference
                            improvement = ((worst_value - best_value) / worst_value) * 100
                            transport_name = version_transport_map[best_transport]['transport'].upper()
                            self._add_insight('info', f'Transport Comparison ({nfs_version}) - {metric_name}',
                                            f'{transport_name} has {improvement:.1f}% lower latency',
                                            f'Best: {best_value:.2f}ms, Worst: {worst_value:.2f}ms')
                    else:
                        # Higher is better for throughput/IOPS
                        best_transport = max(values, key=lambda k: values[k])
                        best_value = values[best_transport]
                        worst_transport = min(values, key=lambda k: values[k])
                        worst_value = values[worst_transport]
                        
                        if best_value > worst_value * 1.1:  # At least 10% difference
                            improvement = ((best_value - worst_value) / worst_value) * 100
                            transport_name = version_transport_map[best_transport]['transport'].upper()
                            self._add_insight('info', f'Transport Comparison ({nfs_version}) - {metric_name}',
                                            f'{transport_name} performs {improvement:.1f}% better',
                                            f'Best: {best_value:.1f}, Worst: {worst_value:.1f}')
    
    def _find_overall_best(self, version_metrics):
        """Find overall best performing configuration."""
        # Calculate aggregate score for each configuration
        scores = {}
        for version_key, metrics in version_metrics.items():
            score = 0
            # Weight different metrics
            score += metrics.get('write_mbps', 0) * 1.0
            score += metrics.get('read_mbps', 0) * 1.0
            score += metrics.get('rand_read_iops', 0) * 0.01  # Scale down IOPS
            score += metrics.get('rand_write_iops', 0) * 0.01
            # Penalize high latency
            latency = metrics.get('latency_ms', 0)
            if latency > 0:
                score -= latency * 10
            scores[version_key] = score
        
        if scores:
            best_config = max(scores, key=lambda k: scores[k])
            self._add_insight('info', 'Overall Best Configuration',
                            f'{best_config} provides the best overall performance',
                            f'Consider using this configuration for production workloads')
    
    def _analyze_overall_performance(self):
        """Analyze overall test performance."""
        summary = self.results.get('summary', {})
        
        # Check test success rate
        total_tests = summary.get('tests_passed', 0) + summary.get('tests_failed', 0)
        if total_tests > 0:
            pass_rate = (summary.get('tests_passed', 0) / total_tests) * 100
            
            if pass_rate < 80:
                self._add_insight(
                    'critical',
                    'Low Test Success Rate',
                    f'Only {pass_rate:.1f}% of tests passed. This indicates significant stability issues.',
                    'Investigate failed tests and check NFS server health.'
                )
            elif pass_rate < 95:
                self._add_insight(
                    'warning',
                    'Moderate Test Success Rate',
                    f'{pass_rate:.1f}% of tests passed. Some tests are failing intermittently.',
                    'Review failed test logs for patterns.'
                )
    
    def _analyze_nfs_metrics(self):
        """Analyze NFS-specific metrics across all tests with deep RPC and transport analysis."""
        # Collect all NFS metrics from tests
        all_nfs_metrics = []
        
        for test_type in ['dd_tests', 'fio_tests', 'iozone_tests', 'bonnie_tests', 'dbench_tests']:
            tests = self.results.get(test_type, {})
            for test_name, test_data in tests.items():
                if isinstance(test_data, dict) and 'nfs_metrics' in test_data:
                    all_nfs_metrics.append({
                        'test_type': test_type,
                        'test_name': test_name,
                        'metrics': test_data['nfs_metrics'],
                        'throughput_mbps': test_data.get('throughput_mbps') or test_data.get('write_bandwidth_mbps', 0)
                    })
        
        if not all_nfs_metrics:
            self._add_insight(
                'warning',
                'No NFS Metrics Collected',
                'NFS-specific metrics were not collected during tests.',
                'Ensure NFS metrics collection is enabled and nfsstat is available.'
            )
            return
        
        # Enhanced NFS metrics analysis
        self._analyze_rpc_statistics(all_nfs_metrics)
        self._analyze_transport_layer(all_nfs_metrics)
        self._analyze_xprt_stats(all_nfs_metrics)
        self._analyze_operation_performance(all_nfs_metrics)
        self._check_nfs_issues(all_nfs_metrics)
        self._correlate_metrics_with_performance(all_nfs_metrics)
    
    def _analyze_rpc_statistics(self, all_nfs_metrics: List[Dict]):
        """
        Deep analysis of RPC statistics to identify protocol-level issues.
        
        Analyzes:
        - Retransmission rates and patterns
        - Timeout occurrences
        - Invalid replies (protocol errors)
        - RPC call efficiency
        """
        total_retrans = 0
        total_calls = 0
        total_timeouts = 0
        total_invalid = 0
        high_retrans_tests = []
        timeout_tests = []
        
        for metric_data in all_nfs_metrics:
            metrics = metric_data['metrics']
            
            # Get RPC statistics from rates or deltas
            rpc_rates = metrics.get('rates', {}).get('rpc', {})
            rpc_deltas = metrics.get('deltas', {}).get('rpc', {})
            
            # Extract RPC metrics
            retrans = rpc_deltas.get('retransmissions', 0)
            calls = rpc_deltas.get('calls', 0)
            timeouts = rpc_deltas.get('timeouts', 0)
            invalid = rpc_deltas.get('invalid_replies', 0)
            
            total_retrans += retrans
            total_calls += calls
            total_timeouts += timeouts
            total_invalid += invalid
            
            # Calculate retransmission percentage for this test
            if calls > 0:
                retrans_pct = (retrans / calls) * 100
                if retrans_pct > 1.0:  # More than 1% retransmissions
                    high_retrans_tests.append({
                        'test': metric_data['test_name'],
                        'retrans_pct': retrans_pct,
                        'retrans': retrans,
                        'calls': calls
                    })
            
            # Check for timeouts
            if timeouts > 0:
                timeout_rate = (timeouts / calls * 100) if calls > 0 else 0
                timeout_tests.append({
                    'test': metric_data['test_name'],
                    'timeouts': timeouts,
                    'timeout_rate': timeout_rate
                })
        
        # Analyze overall RPC health
        if total_calls > 0:
            overall_retrans_pct = (total_retrans / total_calls) * 100
            overall_timeout_pct = (total_timeouts / total_calls) * 100
            
            # Critical: High retransmission rate
            if overall_retrans_pct > 5.0:
                self._add_insight(
                    'critical',
                    'High RPC Retransmission Rate',
                    f'RPC retransmission rate is {overall_retrans_pct:.2f}% ({total_retrans:,} retransmissions out of {total_calls:,} calls). '
                    'This indicates severe network instability or packet loss.',
                    'Immediate action: 1) Check network for packet loss (ping, mtr), '
                    '2) Verify network equipment (switches, routers), '
                    '3) Check for network congestion, '
                    '4) Consider increasing timeo mount option, '
                    '5) Verify MTU settings match across network path.'
                )
            elif overall_retrans_pct > 1.0:
                self._add_insight(
                    'warning',
                    'Elevated RPC Retransmission Rate',
                    f'RPC retransmission rate is {overall_retrans_pct:.2f}% ({total_retrans:,} retransmissions out of {total_calls:,} calls). '
                    'This suggests network reliability issues.',
                    'Recommended: 1) Monitor network quality, '
                    '2) Check for intermittent connectivity issues, '
                    '3) Review network path for bottlenecks, '
                    '4) Consider tuning timeo/retrans mount options.'
                )
            elif overall_retrans_pct > 0.1:
                self._add_insight(
                    'info',
                    'Low RPC Retransmission Rate',
                    f'RPC retransmission rate is {overall_retrans_pct:.2f}% ({total_retrans:,} retransmissions out of {total_calls:,} calls). '
                    'Network reliability is acceptable but could be improved.',
                    'Monitor network quality and consider optimizations if performance is critical.'
                )
            
            # Critical: Timeouts detected
            if overall_timeout_pct > 1.0:
                self._add_insight(
                    'critical',
                    'RPC Timeouts Detected',
                    f'RPC timeout rate is {overall_timeout_pct:.2f}% ({total_timeouts:,} timeouts out of {total_calls:,} calls). '
                    'This indicates NFS server unresponsiveness or extreme network latency.',
                    'Immediate action: 1) Check NFS server load and responsiveness, '
                    '2) Verify server is not overloaded (CPU, memory, I/O), '
                    '3) Check network latency (ping times), '
                    '4) Review NFS server logs for errors, '
                    '5) Consider increasing nfsd thread count on server.'
                )
            elif overall_timeout_pct > 0.1:
                self._add_insight(
                    'warning',
                    'Occasional RPC Timeouts',
                    f'RPC timeout rate is {overall_timeout_pct:.2f}% ({total_timeouts:,} timeouts out of {total_calls:,} calls). '
                    'Server occasionally fails to respond in time.',
                    'Recommended: 1) Monitor NFS server performance, '
                    '2) Check for load spikes, '
                    '3) Review timeo mount option (current timeout threshold).'
                )
        
        # Check for invalid replies (protocol errors)
        if total_invalid > 0:
            invalid_rate = (total_invalid / total_calls * 100) if total_calls > 0 else 0
            self._add_insight(
                'critical',
                'Invalid RPC Replies Detected',
                f'Detected {total_invalid:,} invalid RPC replies ({invalid_rate:.2f}% of calls). '
                'This indicates protocol errors, corruption, or version mismatches.',
                'Immediate action: 1) Verify NFS version compatibility between client and server, '
                '2) Check for network corruption (bad cables, faulty NICs), '
                '3) Review NFS server logs for protocol errors, '
                '4) Ensure consistent NFS version across all mounts.'
            )
        
        # Report per-test high retransmission rates
        if high_retrans_tests:
            worst_test = max(high_retrans_tests, key=lambda x: x['retrans_pct'])
            self._add_insight(
                'warning',
                'Test-Specific Retransmission Issues',
                f"Test '{worst_test['test']}' had highest retransmission rate: {worst_test['retrans_pct']:.2f}% "
                f"({worst_test['retrans']:,} retransmissions). "
                f"{len(high_retrans_tests)} test(s) exceeded 1% retransmission threshold.",
                'Correlate high retransmission tests with workload patterns to identify triggers.'
            )
    
    def _analyze_transport_layer(self, all_nfs_metrics: List[Dict]):
        """
        Analyze transport layer (xprt) statistics for connection and queue health.
        
        Analyzes:
        - Send/Receive balance
        - Queue depths and bottlenecks
        - Connection stability
        - Bad transaction IDs
        """
        connection_issues = []
        queue_issues = []
        bad_xid_tests = []
        
        for metric_data in all_nfs_metrics:
            metrics = metric_data['metrics']
            test_name = metric_data['test_name']
            
            # Get transport statistics
            end_xprt = metrics.get('end_metrics', {}).get('mountstats', {}).get('xprt', {})
            start_xprt = metrics.get('start_metrics', {}).get('mountstats', {}).get('xprt', {})
            
            # Calculate deltas
            sends = end_xprt.get('sends', 0) - start_xprt.get('sends', 0)
            recvs = end_xprt.get('recvs', 0) - start_xprt.get('recvs', 0)
            bad_xids = end_xprt.get('bad_xids', 0) - start_xprt.get('bad_xids', 0)
            connects = end_xprt.get('connect_count', 0) - start_xprt.get('connect_count', 0)
            
            # Queue depths
            sending_queue = end_xprt.get('sending_queue', 0)
            pending_queue = end_xprt.get('pending_queue', 0)
            
            # Analyze send/receive balance
            if sends > 100 and recvs > 100:  # Only analyze if significant traffic
                ratio = sends / recvs if recvs > 0 else 0
                if ratio > 1.15 or ratio < 0.85:
                    imbalance_pct = abs((ratio - 1.0) * 100)
                    connection_issues.append({
                        'test': test_name,
                        'sends': sends,
                        'recvs': recvs,
                        'ratio': ratio,
                        'imbalance_pct': imbalance_pct
                    })
            
            # Check for bad XIDs
            if bad_xids > 0:
                bad_xid_tests.append({
                    'test': test_name,
                    'bad_xids': bad_xids
                })
            
            # Analyze queue depths
            if sending_queue > 0 or pending_queue > 0:
                if sending_queue > pending_queue * 2:
                    queue_issues.append({
                        'test': test_name,
                        'type': 'client_queuing',
                        'sending': sending_queue,
                        'pending': pending_queue
                    })
                elif pending_queue > sending_queue * 2:
                    queue_issues.append({
                        'test': test_name,
                        'type': 'server_delay',
                        'sending': sending_queue,
                        'pending': pending_queue
                    })
            
            # Check connection stability
            if connects > 5:
                connection_issues.append({
                    'test': test_name,
                    'reconnects': connects,
                    'type': 'instability'
                })
        
        # Report send/receive imbalance
        if connection_issues:
            imbalance_issues = [c for c in connection_issues if 'ratio' in c]
            if imbalance_issues:
                worst = max(imbalance_issues, key=lambda x: x['imbalance_pct'])
                self._add_insight(
                    'warning',
                    'RPC Send/Receive Imbalance',
                    f"Test '{worst['test']}' shows {worst['imbalance_pct']:.1f}% imbalance "
                    f"(sends: {worst['sends']:,}, recvs: {worst['recvs']:,}, ratio: {worst['ratio']:.2f}). "
                    'This may indicate packet loss or retransmissions.',
                    'Check network for: 1) Packet loss, 2) Asymmetric routing, '
                    '3) Firewall issues, 4) Network congestion.'
                )
            
            # Report connection instability
            reconnect_issues = [c for c in connection_issues if c.get('type') == 'instability']
            if reconnect_issues:
                worst = max(reconnect_issues, key=lambda x: x['reconnects'])
                self._add_insight(
                    'warning',
                    'Frequent NFS Reconnections',
                    f"Test '{worst['test']}' had {worst['reconnects']} reconnections. "
                    'Frequent reconnections indicate network instability.',
                    'Investigate: 1) Network connectivity issues, 2) Firewall timeouts, '
                    '3) NFS server restarts, 4) Network equipment problems.'
                )
        
        # Report bad XIDs
        if bad_xid_tests:
            total_bad_xids = sum(t['bad_xids'] for t in bad_xid_tests)
            self._add_insight(
                'critical',
                'Bad Transaction IDs Detected',
                f'Detected {total_bad_xids} bad transaction IDs across {len(bad_xid_tests)} test(s). '
                'This indicates RPC transaction ID mismatches, possibly due to network issues or server problems.',
                'Immediate action: 1) Check network stability and packet ordering, '
                '2) Verify NFS server is not overloaded, '
                '3) Check for duplicate IP addresses, '
                '4) Review firewall/NAT configuration.'
            )
        
        # Report queue issues
        if queue_issues:
            client_queue_issues = [q for q in queue_issues if q['type'] == 'client_queuing']
            server_delay_issues = [q for q in queue_issues if q['type'] == 'server_delay']
            
            if client_queue_issues:
                worst = max(client_queue_issues, key=lambda x: x['sending'])
                self._add_insight(
                    'warning',
                    'Client-Side RPC Queuing',
                    f"Test '{worst['test']}' shows high client-side queue depth "
                    f"(sending: {worst['sending']:,}, pending: {worst['pending']:,}). "
                    'Client is generating requests faster than they can be sent.',
                    'Consider: 1) Reducing client-side parallelism, '
                    '2) Checking network bandwidth, '
                    '3) Tuning TCP send buffer sizes.'
                )
            
            if server_delay_issues:
                worst = max(server_delay_issues, key=lambda x: x['pending'])
                self._add_insight(
                    'warning',
                    'Server Response Delays',
                    f"Test '{worst['test']}' shows high pending queue depth "
                    f"(sending: {worst['sending']:,}, pending: {worst['pending']:,}). "
                    'Server is slow to respond to RPC requests.',
                    'Check: 1) NFS server load (CPU, I/O), '
                    '2) Server-side queue depths, '
                    '3) Storage backend performance, '
                    '4) Increase nfsd thread count if needed.'
                )
    
    def _correlate_metrics_with_performance(self, all_nfs_metrics: List[Dict]):
        """
        Correlate NFS metrics with performance to identify root causes.
        
        Identifies patterns like:
        - Low throughput + high retransmissions = network issue
        - Low throughput + high latency = server issue
        - Low throughput + normal metrics = client bottleneck
        """
        # Collect performance and metrics data
        perf_data = []
        for metric_data in all_nfs_metrics:
            throughput = metric_data.get('throughput_mbps', 0)
            if throughput == 0:
                continue
            
            metrics = metric_data['metrics']
            rpc_deltas = metrics.get('deltas', {}).get('rpc', {})
            
            retrans = rpc_deltas.get('retransmissions', 0)
            calls = rpc_deltas.get('calls', 0)
            retrans_pct = (retrans / calls * 100) if calls > 0 else 0
            
            # Get latency if available
            rates = metrics.get('rates', {})
            xprt_rates = rates.get('xprt', {})
            
            perf_data.append({
                'test': metric_data['test_name'],
                'throughput': throughput,
                'retrans_pct': retrans_pct,
                'retrans': retrans,
                'calls': calls
            })
        
        if not perf_data:
            return
        
        # Calculate average throughput
        avg_throughput = sum(p['throughput'] for p in perf_data) / len(perf_data)
        
        # Find low-performing tests
        low_perf_tests = [p for p in perf_data if p['throughput'] < avg_throughput * 0.7]
        
        for test in low_perf_tests:
            # Correlate with retransmissions
            if test['retrans_pct'] > 2.0:
                self._add_insight(
                    'warning',
                    f"Performance Issue Root Cause: {test['test']}",
                    f"Low throughput ({test['throughput']:.1f} MB/s) correlates with high retransmissions ({test['retrans_pct']:.2f}%). "
                    'Network reliability is likely the bottleneck.',
                    'Priority: Fix network issues first. Check for packet loss, congestion, or faulty equipment.'
                )
            elif test['retrans_pct'] < 0.5:
                self._add_insight(
                    'info',
                    f"Performance Analysis: {test['test']}",
                    f"Low throughput ({test['throughput']:.1f} MB/s) with minimal retransmissions ({test['retrans_pct']:.2f}%). "
                    'Network is healthy; bottleneck is likely server-side or client-side.',
                    'Investigate: 1) NFS server performance (CPU, I/O), '
                    '2) Client-side limitations, '
                    '3) Storage backend performance, '
                    '4) NFS mount options (rsize/wsize).'
                )
    
    def _analyze_xprt_stats(self, all_nfs_metrics: List[Dict]):
        """Analyze transport layer statistics."""
        bad_xids_found = False
        high_retrans = False
        
        for metric_data in all_nfs_metrics:
            xprt = metric_data['metrics'].get('xprt', {})
            
            # Check for bad XIDs
            bad_xids = xprt.get('bad_xids', 0)
            if bad_xids > 0:
                bad_xids_found = True
                self._add_insight(
                    'critical',
                    'Bad Transaction IDs Detected',
                    f"Found {bad_xids} bad XIDs in {metric_data['test_name']}. "
                    "This indicates RPC transaction ID mismatches.",
                    'Check network stability, NFS server load, and firewall rules.'
                )
            
            # Check send/receive balance
            sends = xprt.get('sends', 0)
            recvs = xprt.get('recvs', 0)
            if sends > 0 and recvs > 0:
                ratio = sends / recvs
                if ratio > 1.1 or ratio < 0.9:
                    self._add_insight(
                        'warning',
                        'Imbalanced RPC Traffic',
                        f"Send/Receive ratio is {ratio:.2f} in {metric_data['test_name']}. "
                        "This may indicate retransmissions or lost responses.",
                        'Monitor network packet loss and NFS server responsiveness.'
                    )
    
    def _analyze_operation_performance(self, all_nfs_metrics: List[Dict]):
        """Analyze per-operation performance metrics."""
        slow_operations = []
        
        for metric_data in all_nfs_metrics:
            per_op_stats = metric_data['metrics'].get('per_op_stats', {})
            
            for op_name, op_stats in per_op_stats.items():
                avg_total = op_stats.get('avg_total_latency_ms', 0)
                
                # Define thresholds
                if op_name in ['READ', 'WRITE']:
                    threshold = 50  # ms
                else:  # Metadata operations
                    threshold = 20  # ms
                
                if avg_total > threshold:
                    slow_operations.append({
                        'test': metric_data['test_name'],
                        'operation': op_name,
                        'latency': avg_total,
                        'threshold': threshold
                    })
        
        if slow_operations:
            # Group by operation type
            op_summary = {}
            for op in slow_operations:
                op_name = op['operation']
                if op_name not in op_summary:
                    op_summary[op_name] = []
                op_summary[op_name].append(op)
            
            for op_name, ops in op_summary.items():
                avg_latency = sum(o['latency'] for o in ops) / len(ops)
                self._add_insight(
                    'warning',
                    f'Slow {op_name} Operations',
                    f'Average {op_name} latency is {avg_latency:.1f}ms across {len(ops)} test(s). '
                    f'This exceeds the recommended threshold.',
                    self._get_operation_recommendation(op_name, avg_latency)
                )
    
    def _check_nfs_issues(self, all_nfs_metrics: List[Dict]):
        """Check for identified NFS issues."""
        for metric_data in all_nfs_metrics:
            issues = metric_data['metrics'].get('issues', [])
            
            for issue in issues:
                severity = issue.get('severity', 'info')
                issue_type = issue.get('type', 'Unknown')
                message = issue.get('message', '')
                
                self._add_insight(
                    severity,
                    f'NFS Issue: {issue_type}',
                    f"{message} (in {metric_data['test_name']})",
                    issue.get('recommendation', 'Review NFS configuration.')
                )
    
    def _analyze_bottlenecks(self):
        """Identify performance bottlenecks."""
        # Analyze throughput across tests
        throughputs = []
        
        for test_type in ['dd_tests', 'fio_tests', 'iozone_tests']:
            tests = self.results.get(test_type, {})
            for test_name, test_data in tests.items():
                if isinstance(test_data, dict):
                    tp = test_data.get('throughput_mbps') or test_data.get('read_bandwidth_mbps', 0)
                    if tp > 0:
                        throughputs.append({
                            'test': test_name,
                            'throughput': tp,
                            'type': test_type
                        })
        
        if throughputs:
            avg_throughput = sum(t['throughput'] for t in throughputs) / len(throughputs)
            max_throughput = max(t['throughput'] for t in throughputs)
            min_throughput = min(t['throughput'] for t in throughputs)
            
            # Check for high variance
            if max_throughput > min_throughput * 3:
                self._add_insight(
                    'warning',
                    'Inconsistent Performance',
                    f'Throughput varies significantly: {min_throughput:.1f} - {max_throughput:.1f} MB/s. '
                    'This indicates inconsistent performance across different workloads.',
                    'Investigate caching effects, network congestion, or server load variations.'
                )
            
            # Check if performance is below expectations
            if avg_throughput < 50:  # Assuming 1Gbps network minimum
                self._add_insight(
                    'warning',
                    'Low Average Throughput',
                    f'Average throughput is {avg_throughput:.1f} MB/s, which is below typical expectations.',
                    'Check network bandwidth, NFS mount options (rsize/wsize), and server performance.'
                )
    
    def _analyze_consistency(self):
        """Analyze performance consistency."""
        # Check for timeouts or errors
        has_timeouts = False
        
        for test_type in ['dd_tests', 'fio_tests', 'iozone_tests', 'bonnie_tests', 'dbench_tests']:
            tests = self.results.get(test_type, {})
            for test_name, test_data in tests.items():
                if isinstance(test_data, dict):
                    if test_data.get('status') == 'failed':
                        error = test_data.get('error', '')
                        if 'timeout' in error.lower():
                            has_timeouts = True
                            self._add_insight(
                                'critical',
                                'Test Timeout Detected',
                                f'{test_name} timed out. This indicates NFS hang or extreme slowness.',
                                'Check NFS server responsiveness, network connectivity, and mount options.'
                            )
    
    def _detect_saturation(self):
        """
        Detect system saturation points in scalability and stress tests.
        
        Identifies when:
        - Throughput plateaus despite increasing load
        - Latency increases sharply under load
        - Metadata operations show contention
        - Parallel I/O shows diminishing returns
        """
        # 1. Analyze IOzone scaling tests for throughput saturation
        iozone_tests = self.results.get('iozone_tests', {})
        for test_name, test_data in iozone_tests.items():
            if test_name == 'scaling_test' and isinstance(test_data, dict):
                scaling_results = test_data.get('scaling_results', {})
                if scaling_results:
                    self._analyze_scaling_saturation(scaling_results, 'IOzone', 'threads')
        
        # 2. Analyze DBench scalability tests for client saturation
        dbench_tests = self.results.get('dbench_tests', {})
        for test_name, test_data in dbench_tests.items():
            if test_name == 'scalability_test' and isinstance(test_data, dict):
                client_results = test_data.get('client_results', [])
                if client_results:
                    self._analyze_client_saturation(client_results)
        
        # 3. Analyze metadata operation saturation (Bonnie++)
        bonnie_tests = self.results.get('bonnie_tests', {})
        for test_name, test_data in bonnie_tests.items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                self._analyze_metadata_saturation(test_name, test_data)
        
        # 4. Analyze latency degradation under load (FIO)
        fio_tests = self.results.get('fio_tests', {})
        for test_name, test_data in fio_tests.items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                self._analyze_latency_degradation(test_name, test_data)
    
    def _analyze_scaling_saturation(self, scaling_results: Dict, tool_name: str, scale_unit: str):
        """Detect throughput saturation in scaling tests."""
        # Extract data points
        data_points = []
        for thread_name, thread_data in sorted(scaling_results.items()):
            try:
                # Extract thread count from name like "4_threads"
                thread_count = int(thread_name.split('_')[0])
                read_tp = thread_data.get('read_throughput_mbps', 0)
                write_tp = thread_data.get('write_throughput_mbps', 0)
                data_points.append({
                    'scale': thread_count,
                    'read_mbps': read_tp,
                    'write_mbps': write_tp,
                    'total_mbps': read_tp + write_tp
                })
            except (ValueError, IndexError):
                continue
        
        if len(data_points) < 3:
            return  # Need at least 3 points to detect saturation
        
        # Check for throughput plateau (less than 10% improvement with 2x load)
        for i in range(len(data_points) - 1):
            current = data_points[i]
            next_point = data_points[i + 1]
            
            scale_increase = next_point['scale'] / current['scale']
            throughput_increase = next_point['total_mbps'] / current['total_mbps'] if current['total_mbps'] > 0 else 0
            
            # If we double the load but throughput increases less than 10%, we've hit saturation
            if scale_increase >= 1.8 and throughput_increase < 1.1:
                saturation_point = current['scale']
                self._add_insight(
                    'warning',
                    f'{tool_name} Saturation Detected',
                    f'Throughput plateaus at {saturation_point} {scale_unit}. '
                    f'Increasing from {current["scale"]} to {next_point["scale"]} {scale_unit} '
                    f'only improved throughput by {(throughput_increase - 1) * 100:.1f}%. '
                    f'Current: {current["total_mbps"]:.1f} MB/s, Next: {next_point["total_mbps"]:.1f} MB/s.',
                    'System has reached maximum throughput. Consider: '
                    '1) Increasing network bandwidth, '
                    '2) Optimizing NFS server (more threads, faster storage), '
                    '3) Using multiple NFS servers with load balancing.'
                )
                break
    
    def _analyze_client_saturation(self, client_results: List[Dict]):
        """Detect saturation in DBench client scalability tests."""
        if len(client_results) < 3:
            return
        
        # Sort by number of clients
        sorted_results = sorted(client_results, key=lambda x: x.get('num_clients', 0))
        
        for i in range(len(sorted_results) - 1):
            current = sorted_results[i]
            next_point = sorted_results[i + 1]
            
            curr_clients = current.get('num_clients', 0)
            next_clients = next_point.get('num_clients', 0)
            curr_tp = current.get('throughput_mbps', 0)
            next_tp = next_point.get('throughput_mbps', 0)
            curr_ops = current.get('operations_per_sec', 0)
            next_ops = next_point.get('operations_per_sec', 0)
            
            if curr_clients == 0 or curr_tp == 0:
                continue
            
            client_increase = next_clients / curr_clients
            tp_increase = next_tp / curr_tp if curr_tp > 0 else 0
            ops_increase = next_ops / curr_ops if curr_ops > 0 else 0
            
            # Detect saturation: 2x clients but less than 20% improvement
            if client_increase >= 1.8 and tp_increase < 1.2:
                self._add_insight(
                    'warning',
                    'Client Scalability Saturation',
                    f'Throughput saturates at {curr_clients} clients. '
                    f'Increasing from {curr_clients} to {next_clients} clients '
                    f'only improved throughput by {(tp_increase - 1) * 100:.1f}% '
                    f'({curr_tp:.1f} → {next_tp:.1f} MB/s).',
                    'NFS server or network is saturated. Consider: '
                    '1) Increasing server resources (CPU, memory, network), '
                    '2) Tuning nfsd thread count, '
                    '3) Checking for lock contention.'
                )
                break
            
            # Also check operations per second for metadata-heavy workloads
            if ops_increase > 0 and client_increase >= 1.8 and ops_increase < 1.2:
                self._add_insight(
                    'warning',
                    'Metadata Operation Saturation',
                    f'Operations/sec saturates at {curr_clients} clients. '
                    f'Increasing from {curr_clients} to {next_clients} clients '
                    f'only improved ops/sec by {(ops_increase - 1) * 100:.1f}% '
                    f'({curr_ops:.1f} → {next_ops:.1f} ops/sec).',
                    'Metadata operations are bottlenecked. Consider: '
                    '1) Enabling attribute caching (ac, actimeo), '
                    '2) Increasing server metadata performance (faster storage for metadata), '
                    '3) Reducing synchronous operations.'
                )
                break
    
    def _analyze_metadata_saturation(self, test_name: str, test_data: Dict):
        """Detect metadata operation saturation in Bonnie++ tests."""
        # Compare sequential vs random file operations
        seq_create = test_data.get('file_create_seq_per_sec', 0)
        seq_delete = test_data.get('file_delete_seq_per_sec', 0)
        rand_create = test_data.get('file_create_random_per_sec', 0)
        rand_delete = test_data.get('file_delete_random_per_sec', 0)
        
        # If random operations are significantly slower than sequential (>3x), indicates contention
        if seq_create > 0 and rand_create > 0:
            ratio = seq_create / rand_create
            if ratio > 3:
                self._add_insight(
                    'warning',
                    'Metadata Contention Detected',
                    f'Random file creates are {ratio:.1f}x slower than sequential '
                    f'({rand_create:.1f} vs {seq_create:.1f} ops/sec). '
                    'This indicates metadata lock contention or directory lookup overhead.',
                    'Optimize metadata operations: '
                    '1) Use attribute caching (noac=0, actimeo=60), '
                    '2) Distribute files across multiple directories, '
                    '3) Consider using lookupcache=positive mount option.'
                )
        
        # Check if metadata operations are extremely slow (< 100 ops/sec)
        avg_metadata_ops = (seq_create + seq_delete + rand_create + rand_delete) / 4 if all([seq_create, seq_delete, rand_create, rand_delete]) else 0
        if 0 < avg_metadata_ops < 100:
            self._add_insight(
                'critical',
                'Severe Metadata Performance Degradation',
                f'Average metadata operations are only {avg_metadata_ops:.1f} ops/sec. '
                'This is extremely slow and indicates a serious bottleneck.',
                'Immediate action required: '
                '1) Check NFS server load and metadata storage performance, '
                '2) Verify network latency is acceptable, '
                '3) Review NFS server configuration (nfsd threads, export options), '
                '4) Consider using NFSv4 with delegations for better metadata caching.'
            )
    
    def _analyze_latency_degradation(self, test_name: str, test_data: Dict):
        """Detect latency degradation under load in FIO tests."""
        read_lat = test_data.get('read_latency_ms', 0)
        write_lat = test_data.get('write_latency_ms', 0)
        read_p99 = test_data.get('read_latency_p99_ms', 0)
        write_p99 = test_data.get('write_latency_p99_ms', 0)
        
        # Check if p99 latency is much higher than average (>5x indicates tail latency issues)
        if read_lat > 0 and read_p99 > 0:
            ratio = read_p99 / read_lat
            if ratio > 5:
                self._add_insight(
                    'warning',
                    'Read Latency Tail Detected',
                    f'P99 read latency ({read_p99:.1f}ms) is {ratio:.1f}x higher than average ({read_lat:.1f}ms) in {test_name}. '
                    'This indicates inconsistent performance with occasional severe slowdowns.',
                    'Address tail latency: '
                    '1) Check for network packet loss or retransmissions, '
                    '2) Monitor NFS server for load spikes or resource contention, '
                    '3) Review storage backend performance (check for slow disks), '
                    '4) Consider using async mount option if data safety allows.'
                )
        
        if write_lat > 0 and write_p99 > 0:
            ratio = write_p99 / write_lat
            if ratio > 5:
                self._add_insight(
                    'warning',
                    'Write Latency Tail Detected',
                    f'P99 write latency ({write_p99:.1f}ms) is {ratio:.1f}x higher than average ({write_lat:.1f}ms) in {test_name}. '
                    'This indicates write operations occasionally experience severe delays.',
                    'Address write latency: '
                    '1) Check NFS server write cache and commit behavior, '
                    '2) Monitor storage backend write performance, '
                    '3) Review sync vs async mount options, '
                    '4) Check for network congestion during write bursts.'
                )
    
    def _generate_recommendations(self):
        """Generate actionable recommendations based on analysis."""
        # Based on insights, generate recommendations
        if self.severity_counts['critical'] > 0:
            self.recommendations.append({
                'priority': 'high',
                'title': 'Critical Issues Require Immediate Attention',
                'description': f'Found {self.severity_counts["critical"]} critical issue(s) that need immediate investigation.',
                'actions': [
                    'Review all critical insights above',
                    'Check NFS server health and logs',
                    'Verify network connectivity and stability',
                    'Consider temporarily reducing client load'
                ]
            })
        
        if self.severity_counts['warning'] > 2:
            self.recommendations.append({
                'priority': 'medium',
                'title': 'Performance Optimization Needed',
                'description': f'Found {self.severity_counts["warning"]} warning(s) indicating suboptimal performance.',
                'actions': [
                    'Review NFS mount options (rsize, wsize, async)',
                    'Check server-side tuning parameters',
                    'Monitor network utilization',
                    'Consider enabling NFS caching'
                ]
            })
        
        # Always add general recommendations
        self.recommendations.append({
            'priority': 'low',
            'title': 'General Best Practices',
            'description': 'Follow these practices for optimal NFS performance.',
            'actions': [
                'Use NFSv4 or later for better performance',
                'Enable async mount option for write-heavy workloads',
                'Tune rsize/wsize to match network MTU',
                'Monitor NFS metrics regularly',
                'Keep NFS client and server software updated'
            ]
        })
    
    def _add_insight(self, severity: str, title: str, description: str, recommendation: str):
        """Add an insight to the analysis."""
        self.insights.append({
            'severity': severity,
            'title': title,
            'description': description,
            'recommendation': recommendation
        })
        self.severity_counts[severity] = self.severity_counts.get(severity, 0) + 1
    
    def _get_operation_recommendation(self, op_name: str, latency: float) -> str:
        """Get recommendation for slow operation."""
        if op_name in ['READ', 'WRITE']:
            return (
                f'For slow {op_name} operations: '
                'Check network bandwidth, increase rsize/wsize, '
                'verify server disk performance, consider async mount option.'
            )
        else:
            return (
                f'For slow {op_name} (metadata) operations: '
                'Check server metadata performance, reduce file count, '
                'consider using actimeo mount option to cache attributes longer.'
            )
    
    def _calculate_health_score(self) -> Dict[str, Any]:
        """Calculate overall health score."""
        # Simple scoring: 100 - (critical*20 + warning*5)
        score = 100 - (self.severity_counts['critical'] * 20 + self.severity_counts['warning'] * 5)
        score = max(0, min(100, score))
        
        if score >= 90:
            status = 'excellent'
            color = 'green'
        elif score >= 75:
            status = 'good'
            color = 'lightgreen'
        elif score >= 60:
            status = 'fair'
            color = 'yellow'
        elif score >= 40:
            status = 'poor'
            color = 'orange'
        else:
            status = 'critical'
            color = 'red'
        
        return {
            'score': score,
            'status': status,
            'color': color
        }
    
    def _analyze_historical_comparison(self):
        """Analyze results against historical data."""
        if 'historical_comparison' not in self.results:
            return
        
        comparison = self.results['historical_comparison']
        
        # Check if we have previous data
        if not comparison.get('has_previous', False):
            self._add_insight(
                'info',
                'No Historical Data',
                'This is the first test run or no previous results available',
                'Run more tests to enable trend analysis and regression detection'
            )
            return
        
        # Analyze regressions
        regressions = comparison.get('regressions', [])
        if regressions:
            for reg in regressions:
                metric_name = self._format_metric_name(reg['metric'])
                change_pct = abs(reg['change_percent'])
                
                # Determine possible causes based on metric type
                possible_causes = self._get_regression_causes(reg['metric'])
                
                self._add_insight(
                    'critical',
                    f'Performance Regression: {metric_name}',
                    f"{metric_name} decreased by {change_pct:.1f}% "
                    f"(from {reg['previous']} to {reg['current']})",
                    f"Investigate: {possible_causes}"
                )
        
        # Analyze improvements
        improvements = comparison.get('improvements', [])
        if improvements:
            significant_improvements = [imp for imp in improvements 
                                       if abs(imp['change_percent']) > 10]
            if significant_improvements:
                for imp in significant_improvements:
                    metric_name = self._format_metric_name(imp['metric'])
                    change_pct = abs(imp['change_percent'])
                    
                    self._add_insight(
                        'info',
                        f'Performance Improvement: {metric_name}',
                        f"{metric_name} improved by {change_pct:.1f}% "
                        f"(from {imp['previous']} to {imp['current']})",
                        'Document what changed to maintain this improvement'
                    )
        
        # Analyze warnings
        warnings = comparison.get('warnings', [])
        if warnings:
            for warn in warnings:
                metric_name = self._format_metric_name(warn['metric'])
                change_pct = abs(warn['change_percent'])
                
                self._add_insight(
                    'warning',
                    f'Performance Warning: {metric_name}',
                    f"{metric_name} changed by {change_pct:.1f}% "
                    f"(from {warn['previous']} to {warn['current']})",
                    'Monitor this metric in future runs'
                )
        
        # Add summary insight
        summary = comparison.get('summary', {})
        if summary:
            total = summary.get('total_comparisons', 0)
            reg_count = summary.get('regressions', 0)
            imp_count = summary.get('improvements', 0)
            warn_count = summary.get('warnings', 0)
            stable_count = summary.get('stable', 0)
            
            summary_text = (
                f"Compared {total} metrics with previous run: "
                f"{imp_count} improved, {reg_count} regressed, "
                f"{warn_count} warnings, {stable_count} stable"
            )
            
            if reg_count > 0:
                severity = 'critical'
                recommendation = 'Address regressions before deploying to production'
            elif warn_count > 0:
                severity = 'warning'
                recommendation = 'Monitor warned metrics closely'
            else:
                severity = 'info'
                recommendation = 'Performance is stable or improving'
            
            self._add_insight(
                severity,
                'Historical Comparison Summary',
                summary_text,
                recommendation
            )
    
    def _format_metric_name(self, metric: str) -> str:
        """Format metric name for display."""
        # Convert snake_case to Title Case
        parts = metric.split('_')
        formatted = ' '.join(word.capitalize() for word in parts)
        return formatted
    
    def _get_regression_causes(self, metric: str) -> str:
        """Get possible causes for metric regression."""
        metric_lower = metric.lower()
        
        if 'throughput' in metric_lower or 'mbps' in metric_lower:
            return 'Network congestion, server load, storage bottleneck, or NFS configuration changes'
        elif 'iops' in metric_lower:
            return 'Storage performance degradation, increased queue depth, or I/O scheduler changes'
        elif 'latency' in metric_lower:
            return 'Network latency increase, server overload, or storage response time issues'
        elif 'ops' in metric_lower:
            return 'Server CPU saturation, memory pressure, or application-level bottlenecks'
        else:
            return 'System configuration changes, resource contention, or environmental factors'


def analyze_performance(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to analyze performance results.
    
    Args:
        results: Complete test results dictionary
        
    Returns:
        dict: Analysis summary
    """
    analyzer = PerformanceAnalyzer(results)
    return analyzer.analyze()

# Made with Bob
