#!/usr/bin/env python3
"""
Historical Comparison Module for NFS Benchmark Suite

This module manages historical test result storage, retrieval, and comparison.
It enables tracking performance trends over time and detecting regressions.

Author: NFS Benchmark Suite
Date: 2026-04-03
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import statistics


class HistoricalComparison:
    """Manages historical test result comparison and trend analysis."""
    
    def __init__(self, results_dir: str = 'results'):
        """
        Initialize historical comparison manager.
        
        Args:
            results_dir: Directory to store historical results
        """
        self.results_dir = Path(results_dir)
        self.history_file = self.results_dir / 'history.json'
        self._ensure_results_dir()
    
    def _ensure_results_dir(self) -> None:
        """Create results directory if it doesn't exist."""
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def save_result(self, result: Dict[str, Any]) -> str:
        """
        Save current test result to history.
        
        Args:
            result: Test result dictionary
            
        Returns:
            Timestamp string for the saved result
        """
        # Generate timestamp with microseconds to prevent collisions
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        
        # Extract key metrics for quick access
        key_metrics = self._extract_key_metrics(result)
        
        # Create history entry
        test_run = result.get('test_run', {})
        summary = result.get('summary', {})
        
        entry = {
            'timestamp': timestamp,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'mount_path': test_run.get('mount_path', 'unknown'),
            'config': test_run.get('config_file', 'unknown'),
            'summary': {
                'total_tests': summary.get('tests_passed', 0) + summary.get('tests_failed', 0),
                'passed': summary.get('tests_passed', 0),
                'failed': summary.get('tests_failed', 0)
            },
            'key_metrics': key_metrics
        }
        
        # Save full result to individual file
        result_file = self.results_dir / f'{timestamp}.json'
        try:
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Update history index
            self._update_history_index(entry)
            
            return timestamp
        except (IOError, OSError) as e:
            raise IOError(f"Failed to save result to {result_file}: {e}")
    
    def _extract_key_metrics(self, result: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract key metrics from test result for quick comparison.
        
        Args:
            result: Test result dictionary
            
        Returns:
            Dictionary of key metrics
        """
        key_metrics = {}
        
        # Extract DD metrics
        if 'dd_tests' in result:
            dd = result['dd_tests']
            if 'sequential_write' in dd:
                key_metrics['dd_seq_write_mbps'] = dd['sequential_write'].get('throughput_mbps', 0)
            if 'sequential_read' in dd:
                key_metrics['dd_seq_read_mbps'] = dd['sequential_read'].get('throughput_mbps', 0)
        
        # Extract FIO metrics
        if 'fio_tests' in result:
            fio = result['fio_tests']
            if 'sequential_read' in fio:
                key_metrics['fio_seq_read_mbps'] = fio['sequential_read'].get('throughput_mbps', 0)
                key_metrics['fio_seq_read_iops'] = fio['sequential_read'].get('iops', 0)
            if 'sequential_write' in fio:
                key_metrics['fio_seq_write_mbps'] = fio['sequential_write'].get('throughput_mbps', 0)
            if 'random_read' in fio:
                key_metrics['fio_rand_read_iops'] = fio['random_read'].get('iops', 0)
                key_metrics['fio_rand_read_lat_ms'] = fio['random_read'].get('avg_latency_ms', 0)
            if 'random_write' in fio:
                key_metrics['fio_rand_write_iops'] = fio['random_write'].get('iops', 0)
        
        # Extract IOzone metrics
        if 'iozone_tests' in result:
            iozone = result['iozone_tests']
            if 'write' in iozone:
                key_metrics['iozone_write_mbps'] = iozone['write'].get('throughput_mbps', 0)
            if 'read' in iozone:
                key_metrics['iozone_read_mbps'] = iozone['read'].get('throughput_mbps', 0)
        
        # Extract Bonnie++ metrics
        if 'bonnie_tests' in result:
            bonnie = result['bonnie_tests']
            if 'sequential_output' in bonnie:
                key_metrics['bonnie_seq_out_mbps'] = bonnie['sequential_output'].get('per_char', 0)
            if 'sequential_input' in bonnie:
                key_metrics['bonnie_seq_in_mbps'] = bonnie['sequential_input'].get('per_char', 0)
        
        # Extract Dbench metrics
        if 'dbench_tests' in result:
            dbench = result['dbench_tests']
            key_metrics['dbench_throughput_mbps'] = dbench.get('throughput_mbps', 0)
            key_metrics['dbench_ops_per_sec'] = dbench.get('operations_per_sec', 0)
            key_metrics['dbench_avg_latency_ms'] = dbench.get('avg_latency_ms', 0)
        
        # Extract average latency across all tests
        latencies = []
        if 'fio_rand_read_lat_ms' in key_metrics:
            latencies.append(key_metrics['fio_rand_read_lat_ms'])
        if 'dbench_avg_latency_ms' in key_metrics:
            latencies.append(key_metrics['dbench_avg_latency_ms'])
        if latencies:
            key_metrics['avg_latency_ms'] = statistics.mean(latencies)
        
        return key_metrics
    
    def _update_history_index(self, entry: Dict[str, Any]) -> None:
        """
        Update history index with new entry.
        
        Args:
            entry: History entry to add
        """
        # Load existing history
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                history = json.load(f)
        else:
            history = {'runs': []}
        
        # Add new entry
        history['runs'].append(entry)
        
        # Save updated history
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def load_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Load recent test results from history.
        
        Args:
            limit: Maximum number of results to load
            
        Returns:
            List of history entries (most recent first)
        """
        if not self.history_file.exists():
            return []
        
        with open(self.history_file, 'r') as f:
            history = json.load(f)
        
        # Return most recent entries
        runs = history.get('runs', [])
        return runs[-limit:][::-1]  # Reverse to get most recent first
    
    def load_result(self, timestamp: str) -> Optional[Dict[str, Any]]:
        """
        Load full result for a specific timestamp.
        
        Args:
            timestamp: Timestamp of the result to load
            
        Returns:
            Full result dictionary or None if not found
        """
        result_file = self.results_dir / f'{timestamp}.json'
        if not result_file.exists():
            return None
        
        with open(result_file, 'r') as f:
            return json.load(f)
    
    def compare_with_previous(self, current: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare current result with the most recent previous run.
        
        Args:
            current: Current test result
            
        Returns:
            Comparison dictionary with changes and trends
        """
        history = self.load_history(limit=1)
        if not history:
            return {
                'has_previous': False,
                'message': 'No previous results available for comparison'
            }
        
        previous = history[0]
        return self._compare_results(current, previous)
    
    def compare_with_baseline(self, current: Dict[str, Any], 
                             baseline_timestamp: str) -> Dict[str, Any]:
        """
        Compare current result with a specific baseline.
        
        Args:
            current: Current test result
            baseline_timestamp: Timestamp of baseline result
            
        Returns:
            Comparison dictionary with changes and trends
        """
        baseline_entry = None
        for entry in self.load_history(limit=100):
            if entry['timestamp'] == baseline_timestamp:
                baseline_entry = entry
                break
        
        if not baseline_entry:
            return {
                'has_baseline': False,
                'message': f'Baseline {baseline_timestamp} not found'
            }
        
        return self._compare_results(current, baseline_entry)
    
    def _compare_results(self, current: Dict[str, Any], 
                        previous: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two test results.
        
        Args:
            current: Current test result
            previous: Previous test result (history entry)
            
        Returns:
            Comparison dictionary
        """
        current_metrics = self._extract_key_metrics(current)
        previous_metrics = previous.get('key_metrics', {})
        
        comparisons = []
        regressions = []
        improvements = []
        warnings = []
        
        # Compare each metric
        for metric_name, current_value in current_metrics.items():
            if metric_name not in previous_metrics:
                continue
            
            previous_value = previous_metrics[metric_name]
            comparison = self._compare_metric(
                metric_name, current_value, previous_value
            )
            comparisons.append(comparison)
            
            # Categorize changes
            if comparison['severity'] == 'critical':
                regressions.append(comparison)
            elif comparison['severity'] == 'success':
                improvements.append(comparison)
            elif comparison['severity'] == 'warning':
                warnings.append(comparison)
        
        return {
            'has_previous': True,
            'previous_timestamp': previous['timestamp'],
            'previous_date': previous['date'],
            'comparisons': comparisons,
            'regressions': regressions,
            'improvements': improvements,
            'warnings': warnings,
            'summary': {
                'total_comparisons': len(comparisons),
                'regressions': len(regressions),
                'improvements': len(improvements),
                'warnings': len(warnings),
                'stable': len(comparisons) - len(regressions) - len(improvements) - len(warnings)
            }
        }
    
    def _compare_metric(self, name: str, current: float, 
                       previous: float) -> Dict[str, Any]:
        """
        Compare a single metric value.
        
        Args:
            name: Metric name
            current: Current value
            previous: Previous value
            
        Returns:
            Comparison dictionary
        """
        # Calculate changes
        change_abs = current - previous
        change_pct = (change_abs / previous * 100) if previous > 0 else 0
        
        # Determine if higher is better (for most metrics, yes; for latency, no)
        higher_is_better = 'latency' not in name.lower()
        
        # Determine trend and severity
        if abs(change_pct) < 5:
            trend = 'stable'
            severity = 'info'
            icon = '➡️'
        elif (change_pct > 0 and higher_is_better) or (change_pct < 0 and not higher_is_better):
            # Improvement
            if abs(change_pct) > 20:
                trend = 'significantly_improved'
                severity = 'success'
                icon = '⬆️'
            else:
                trend = 'improved'
                severity = 'success'
                icon = '↗️'
        else:
            # Degradation
            if abs(change_pct) > 20:
                trend = 'significantly_degraded'
                severity = 'critical'
                icon = '⬇️'
            elif abs(change_pct) > 10:
                trend = 'degraded'
                severity = 'critical'
                icon = '↘️'
            else:
                trend = 'slightly_degraded'
                severity = 'warning'
                icon = '⚠️'
        
        return {
            'metric': name,
            'current': round(current, 2),
            'previous': round(previous, 2),
            'change_absolute': round(change_abs, 2),
            'change_percent': round(change_pct, 2),
            'trend': trend,
            'severity': severity,
            'icon': icon,
            'higher_is_better': higher_is_better
        }
    
    def calculate_trends(self, metric_name: str, 
                        num_runs: int = 5) -> Dict[str, Any]:
        """
        Calculate trend for a specific metric over multiple runs.
        
        Args:
            metric_name: Name of the metric to analyze
            num_runs: Number of recent runs to analyze
            
        Returns:
            Trend analysis dictionary
        """
        history = self.load_history(limit=num_runs)
        if len(history) < 2:
            return {
                'trend_type': 'insufficient_data',
                'message': f'Need at least 2 runs for trend analysis (have {len(history)})'
            }
        
        # Extract metric values
        values = []
        for entry in reversed(history):  # Oldest to newest
            metrics = entry.get('key_metrics', {})
            if metric_name in metrics:
                values.append(metrics[metric_name])
        
        if len(values) < 2:
            return {
                'trend_type': 'insufficient_data',
                'message': f'Metric {metric_name} not found in enough runs'
            }
        
        return self._analyze_trend(values, metric_name)
    
    def _analyze_trend(self, values: List[float], 
                      metric_name: str) -> Dict[str, Any]:
        """
        Analyze trend from historical values.
        
        Args:
            values: List of metric values (oldest to newest)
            metric_name: Name of the metric
            
        Returns:
            Trend analysis dictionary
        """
        n = len(values)
        
        # Calculate linear regression slope
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0
        
        # Calculate volatility (coefficient of variation)
        std_dev = statistics.stdev(values) if n > 1 else 0
        volatility = std_dev / y_mean if y_mean != 0 else 0
        
        # Determine if higher is better
        higher_is_better = 'latency' not in metric_name.lower()
        
        # Determine trend type
        slope_threshold = y_mean * 0.01  # 1% change per run
        if abs(slope) < slope_threshold:
            trend_type = 'stable'
        elif (slope > 0 and higher_is_better) or (slope < 0 and not higher_is_better):
            trend_type = 'improving'
        else:
            trend_type = 'degrading'
        
        # Determine confidence based on volatility
        if volatility < 0.1:
            confidence = 'high'
        elif volatility < 0.3:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return {
            'metric': metric_name,
            'trend_type': trend_type,
            'slope': round(slope, 2),
            'volatility': round(volatility, 3),
            'confidence': confidence,
            'num_samples': n,
            'values': [round(v, 2) for v in values],
            'mean': round(y_mean, 2),
            'std_dev': round(std_dev, 2)
        }
    
    def get_all_trends(self, num_runs: int = 5) -> List[Dict[str, Any]]:
        """
        Calculate trends for all available metrics.
        
        Args:
            num_runs: Number of recent runs to analyze
            
        Returns:
            List of trend analysis dictionaries
        """
        history = self.load_history(limit=num_runs)
        if not history:
            return []
        
        # Get all metric names from most recent run
        all_metrics = set()
        for entry in history:
            all_metrics.update(entry.get('key_metrics', {}).keys())
        
        # Calculate trends for each metric
        trends = []
        for metric_name in sorted(all_metrics):
            trend = self.calculate_trends(metric_name, num_runs)
            if trend.get('trend_type') != 'insufficient_data':
                trends.append(trend)
        
        return trends
    
    def cleanup_old_results(self, keep_days: int = 90) -> int:
        """
        Remove results older than specified days.
        
        Args:
            keep_days: Number of days to keep
            
        Returns:
            Number of results removed
        """
        if not self.history_file.exists():
            return 0
        
        cutoff_date = datetime.now().timestamp() - (keep_days * 86400)
        removed_count = 0
        
        # Load history
        with open(self.history_file, 'r') as f:
            history = json.load(f)
        
        # Filter old entries
        new_runs = []
        for entry in history.get('runs', []):
            entry_date = datetime.strptime(entry['date'], '%Y-%m-%d %H:%M:%S')
            if entry_date.timestamp() >= cutoff_date:
                new_runs.append(entry)
            else:
                # Remove result file
                result_file = self.results_dir / f"{entry['timestamp']}.json"
                if result_file.exists():
                    result_file.unlink()
                    removed_count += 1
        
        # Update history
        history['runs'] = new_runs
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        return removed_count
    
    def get_storage_size(self) -> int:
        """
        Get total size of historical data in bytes.
        
        Returns:
            Total size in bytes
        """
        total_size = 0
        for file_path in self.results_dir.glob('*.json'):
            total_size += file_path.stat().st_size
        return total_size

# Made with Bob
