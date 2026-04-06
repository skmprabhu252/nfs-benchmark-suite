#!/usr/bin/env python3
"""
Data formatting utilities for HTML report generators

Provides functions for formatting benchmark data, converting units,
and extracting test information.
"""

from typing import Dict, Any, List, Tuple, Optional


def format_throughput(value: float, unit: str = "MB/s") -> str:
    """
    Format throughput value with appropriate precision.
    
    Args:
        value: Throughput value
        unit: Unit string (default: MB/s)
        
    Returns:
        Formatted string with value and unit
    """
    if value == 0:
        return f"0.00 {unit}"
    elif value < 1:
        return f"{value:.3f} {unit}"
    elif value < 10:
        return f"{value:.2f} {unit}"
    else:
        return f"{value:.2f} {unit}"


def format_latency(value: float, unit: str = "ms") -> str:
    """
    Format latency value with appropriate precision.
    
    Args:
        value: Latency value
        unit: Unit string (default: ms)
        
    Returns:
        Formatted string with value and unit
    """
    if value == 0:
        return f"0.00 {unit}"
    elif value < 1:
        return f"{value:.3f} {unit}"
    elif value < 10:
        return f"{value:.2f} {unit}"
    else:
        return f"{value:.1f} {unit}"


def format_iops(value: float) -> str:
    """
    Format IOPS value.
    
    Args:
        value: IOPS value
        
    Returns:
        Formatted string
    """
    if value >= 1000000:
        return f"{value/1000000:.2f}M IOPS"
    elif value >= 1000:
        return f"{value/1000:.2f}K IOPS"
    else:
        return f"{value:.0f} IOPS"


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_percentage(value: float) -> str:
    """
    Format percentage value.
    
    Args:
        value: Percentage value (0-100)
        
    Returns:
        Formatted percentage string
    """
    return f"{value:.1f}%"


def format_file_size(size_mb: float) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_mb: Size in megabytes
        
    Returns:
        Formatted size string
    """
    if size_mb < 1024:
        return f"{size_mb:.0f} MB"
    elif size_mb < 1024 * 1024:
        return f"{size_mb/1024:.1f} GB"
    else:
        return f"{size_mb/(1024*1024):.1f} TB"


def extract_test_results(results: Dict[str, Any]) -> Dict[str, Dict]:
    """
    Extract test results from results dictionary.
    
    Handles both old format (tests at top level) and new format
    (tests under 'results' key).
    
    Args:
        results: Results dictionary
        
    Returns:
        Dictionary with test results by category
    """
    # Check if results are nested under 'results' key
    if 'results' in results and isinstance(results['results'], dict):
        results_data = results['results']
    else:
        results_data = results
    
    # Get dd_tests and filter out 'delete' (cleanup operation, not a test)
    dd_tests = results_data.get('dd_tests') or {}
    if 'delete' in dd_tests:
        dd_tests = {k: v for k, v in dd_tests.items() if k != 'delete'}
    
    return {
        'test_run': results_data.get('test_run') or {},
        'dd_tests': dd_tests,
        'fio_tests': results_data.get('fio_tests') or {},
        'iozone_tests': results_data.get('iozone_tests') or {},
        'bonnie_tests': results_data.get('bonnie_tests') or {},
        'dbench_tests': results_data.get('dbench_tests') or {},
        'summary': results_data.get('summary') or {},
        'nfs_stats': results_data.get('nfs_stats') or {},
    }


def get_test_metadata(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract test metadata from results.
    
    Args:
        results: Results dictionary
        
    Returns:
        Metadata dictionary
    """
    metadata = results.get('test_metadata', {})
    
    # Also check for metadata in results.test_run
    if not metadata:
        test_run = results.get('results', {}).get('test_run', {})
        if test_run:
            metadata = {
                'server_ip': test_run.get('network_config', {}).get('nfs_server_ip'),
                'mount_path': test_run.get('mount_path'),
                'hostname': test_run.get('hostname'),
                'timestamp': test_run.get('timestamp'),
            }
    
    return metadata


def calculate_summary_stats(test_results: Dict[str, Dict]) -> Dict[str, Any]:
    """
    Calculate summary statistics from test results.
    
    Args:
        test_results: Dictionary of test results by category
        
    Returns:
        Summary statistics dictionary
    """
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for category, tests in test_results.items():
        if category in ['test_run', 'summary', 'nfs_stats']:
            continue
        
        if isinstance(tests, dict):
            for test_name, test_data in tests.items():
                if isinstance(test_data, dict):
                    total_tests += 1
                    status = test_data.get('status', 'unknown')
                    if status == 'passed':
                        passed_tests += 1
                    elif status == 'failed':
                        failed_tests += 1
    
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    return {
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'failed_tests': failed_tests,
        'pass_rate': pass_rate,
    }


def get_best_throughput(test_results: Dict[str, Dict]) -> Tuple[str, float, str]:
    """
    Find the best throughput across all tests.
    
    Args:
        test_results: Dictionary of test results by category
        
    Returns:
        Tuple of (tool_name, throughput_value, test_name)
    """
    best_throughput = 0
    best_tool = "N/A"
    best_test = "N/A"
    
    # Check DD tests
    for test_name, test_data in test_results.get('dd_tests', {}).items():
        if test_data.get('status') == 'passed':
            throughput = test_data.get('throughput_mbps', 0)
            if throughput > best_throughput:
                best_throughput = throughput
                best_tool = "DD"
                best_test = test_name
    
    # Check FIO tests
    for test_name, test_data in test_results.get('fio_tests', {}).items():
        if test_data.get('status') == 'passed':
            read_bw = test_data.get('read_bw_mbps', 0)
            write_bw = test_data.get('write_bw_mbps', 0)
            throughput = max(read_bw, write_bw)
            if throughput > best_throughput:
                best_throughput = throughput
                best_tool = "FIO"
                best_test = test_name
    
    # Check IOzone tests
    for test_name, test_data in test_results.get('iozone_tests', {}).items():
        if test_data.get('status') == 'passed':
            if test_name == 'scaling_test':
                scaling_results = test_data.get('scaling_results', {})
                for thread_name, thread_data in scaling_results.items():
                    read_tp = thread_data.get('read_throughput_mbps', 0)
                    write_tp = thread_data.get('write_throughput_mbps', 0)
                    throughput = max(read_tp, write_tp)
                    if throughput > best_throughput:
                        best_throughput = throughput
                        best_tool = "IOzone"
                        best_test = f"{test_name} ({thread_name})"
    
    return (best_tool, best_throughput, best_test)


def get_best_iops(test_results: Dict[str, Dict]) -> Tuple[str, float, str]:
    """
    Find the best IOPS across all tests.
    
    Args:
        test_results: Dictionary of test results by category
        
    Returns:
        Tuple of (tool_name, iops_value, test_name)
    """
    best_iops = 0
    best_tool = "N/A"
    best_test = "N/A"
    
    # Check FIO tests
    for test_name, test_data in test_results.get('fio_tests', {}).items():
        if test_data.get('status') == 'passed':
            read_iops = test_data.get('read_iops', 0)
            write_iops = test_data.get('write_iops', 0)
            iops = max(read_iops, write_iops)
            if iops > best_iops:
                best_iops = iops
                best_tool = "FIO"
                best_test = test_name
    
    return (best_tool, best_iops, best_test)


def get_best_latency(test_results: Dict[str, Dict]) -> Tuple[str, float, str]:
    """
    Find the best (lowest) latency across all tests.
    
    Args:
        test_results: Dictionary of test results by category
        
    Returns:
        Tuple of (tool_name, latency_value, test_name)
    """
    best_latency = float('inf')
    best_tool = "N/A"
    best_test = "N/A"
    
    # Check DBench tests
    for test_name, test_data in test_results.get('dbench_tests', {}).items():
        if test_data.get('status') == 'passed':
            avg_latency = test_data.get('avg_latency_ms')
            if avg_latency and avg_latency < best_latency:
                best_latency = avg_latency
                best_tool = "DBench"
                best_test = test_name
    
    # Check FIO tests
    for test_name, test_data in test_results.get('fio_tests', {}).items():
        if test_data.get('status') == 'passed':
            read_lat = test_data.get('read_lat_ms')
            write_lat = test_data.get('write_lat_ms')
            if read_lat and read_lat < best_latency:
                best_latency = read_lat
                best_tool = "FIO"
                best_test = f"{test_name} (read)"
            if write_lat and write_lat < best_latency:
                best_latency = write_lat
                best_tool = "FIO"
                best_test = f"{test_name} (write)"
    
    if best_latency == float('inf'):
        return ("N/A", 0, "N/A")
    
    return (best_tool, best_latency, best_test)

# Made with Bob
