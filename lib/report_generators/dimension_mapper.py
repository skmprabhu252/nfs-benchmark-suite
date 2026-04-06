#!/usr/bin/env python3
"""
Dimension Mapper for Performance Dimensions

Maps benchmark tests to the 6 performance dimensions defined in README.md:
1. Throughput (MB/s)
2. IOPS (Ops/sec)
3. Latency (ms)
4. Metadata Operations (ops/sec)
5. Cache Effects
6. Concurrency Scaling
"""

from typing import Dict, List, Any, Tuple


# Dimension definitions with descriptions
DIMENSIONS = {
    'throughput': {
        'name': 'Throughput (MB/s)',
        'description': 'Sequential data transfer rate for large files. Critical for bulk operations, backups, and media streaming.',
        'icon': '📊'
    },
    'iops': {
        'name': 'IOPS (Operations/sec)',
        'description': 'Random I/O performance with small blocks (4K). Essential for databases and VMs.',
        'icon': '⚡'
    },
    'latency': {
        'name': 'Latency (ms)',
        'description': 'Response time for I/O operations. Critical for interactive applications and real-time systems.',
        'icon': '⏱️'
    },
    'metadata': {
        'name': 'Metadata Operations (ops/sec)',
        'description': 'File creation, deletion, stat, rename operations. Important for build systems and applications with many small files.',
        'icon': '📁'
    },
    'cache_effects': {
        'name': 'Cache Effects',
        'description': 'Performance difference between cached and direct I/O. Helps understand and tune client-side caching.',
        'icon': '💾'
    },
    'concurrency': {
        'name': 'Concurrency Scaling',
        'description': 'Performance scaling with multiple concurrent clients. Essential for multi-user environments and capacity planning.',
        'icon': '👥'
    }
}


# Test-to-dimension mapping
DIMENSION_MAPPING = {
    'throughput': {
        'dd_tests': [
            'sequential_write_direct',
            'sequential_write_sync',
            'sequential_read_direct',
            'sequential_read_cached'
        ],
        'fio_tests': [
            'sequential_write',
            'sequential_read'
        ],
        'iozone_tests': [
            'baseline_throughput',
            'cache_behavior',
            'mixed_workload'
        ],
        'bonnie_tests': [
            'sequential_output_block_mbps',
            'sequential_input_block_mbps',
            'sequential_output_char_mbps',
            'sequential_input_char_mbps',
            'sequential_rewrite_mbps'
        ],
        'dbench_tests': 'all'  # All dbench tests measure throughput
    },
    'iops': {
        'fio_tests': [
            'random_read_4k',
            'random_write_4k',
            'mixed_randrw_70_30'
        ],
        'iozone_tests': [
            'random_io_4k'
        ]
    },
    'latency': {
        'fio_tests': [
            'latency_test'
        ],
        'dbench_tests': [
            'light_client_load',
            'latency_test'
        ]
    },
    'metadata': {
        'fio_tests': [
            'metadata_operations'
        ],
        'iozone_tests': [
            'metadata_operations'
        ],
        'bonnie_tests': [
            'file_create_seq_per_sec',
            'file_stat_seq_per_sec',
            'file_delete_seq_per_sec',
            'file_create_random_per_sec',
            'file_stat_random_per_sec',
            'file_delete_random_per_sec',
            'random_seeks_per_sec'
        ],
        'dbench_tests': [
            'metadata_intensive'
        ]
    },
    'cache_effects': {
        'dd_tests': [
            # Tuples of (cached, direct) for comparison
            ('sequential_read_cached', 'sequential_read_direct'),
            ('sequential_write_sync', 'sequential_write_direct')
        ],
        'iozone_tests': [
            'cache_behavior'
        ]
    },
    'concurrency': {
        'iozone_tests': [
            'concurrency_16_threads',
            'scaling_test'
        ],
        'dbench_tests': [
            'scalability_test',
            'light_client_load',
            'moderate_client_load',
            'heavy_client_load',
            'sustained_load'
        ]
    }
}


def get_dimension_info(dimension: str) -> Dict[str, str]:
    """
    Get information about a performance dimension.
    
    Args:
        dimension: Dimension key (e.g., 'throughput', 'iops')
        
    Returns:
        Dictionary with name, description, and icon
    """
    return DIMENSIONS.get(dimension, {
        'name': dimension.replace('_', ' ').title(),
        'description': 'Performance dimension',
        'icon': '📈'
    })


def get_tests_for_dimension(dimension: str, tool: str) -> List[str]:
    """
    Get list of tests for a specific dimension and tool.
    
    Args:
        dimension: Dimension key (e.g., 'throughput')
        tool: Tool name (e.g., 'dd_tests', 'fio_tests')
        
    Returns:
        List of test names for that dimension/tool combination
    """
    mapping = DIMENSION_MAPPING.get(dimension, {})
    tests = mapping.get(tool, [])
    
    if tests == 'all':
        return 'all'
    return tests if isinstance(tests, list) else []


def extract_dimension_data(results: Dict[str, Any], dimension: str) -> Dict[str, Any]:
    """
    Extract all test data relevant to a specific dimension.
    
    Args:
        results: Full test results dictionary
        dimension: Dimension key to extract
        
    Returns:
        Dictionary organized by tool with relevant test data
    """
    dimension_data = {}
    mapping = DIMENSION_MAPPING.get(dimension, {})
    
    for tool_key, test_list in mapping.items():
        tool_results = results.get(tool_key, {})
        
        if not tool_results:
            continue
            
        # Handle 'all' case (dbench)
        if test_list == 'all':
            dimension_data[tool_key] = tool_results
            continue
        
        # Extract specific tests
        tool_dimension_data = {}
        for test_name in test_list:
            # Handle cache_effects tuples
            if isinstance(test_name, tuple):
                cached_test, direct_test = test_name
                if cached_test in tool_results and direct_test in tool_results:
                    tool_dimension_data[f"{cached_test}_vs_{direct_test}"] = {
                        'cached': tool_results[cached_test],
                        'direct': tool_results[direct_test]
                    }
            else:
                # Regular test
                if test_name in tool_results:
                    tool_dimension_data[test_name] = tool_results[test_name]
                # For Bonnie++, check if it's a metric within a test
                else:
                    for bonnie_test_name, bonnie_test_data in tool_results.items():
                        if isinstance(bonnie_test_data, dict) and test_name in bonnie_test_data:
                            if tool_key not in dimension_data:
                                dimension_data[tool_key] = {}
                            if bonnie_test_name not in dimension_data[tool_key]:
                                dimension_data[tool_key][bonnie_test_name] = {}
                            dimension_data[tool_key][bonnie_test_name][test_name] = bonnie_test_data[test_name]
        
        if tool_dimension_data:
            dimension_data[tool_key] = tool_dimension_data
    
    return dimension_data


def get_all_dimensions() -> List[str]:
    """
    Get list of all dimension keys in order.
    
    Returns:
        List of dimension keys
    """
    return list(DIMENSIONS.keys())


def get_dimension_summary(results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Get summary of best performance in each dimension.
    
    Args:
        results: Full test results dictionary
        
    Returns:
        Dictionary with best value and source for each dimension
    """
    summary = {}
    
    for dimension in get_all_dimensions():
        dimension_data = extract_dimension_data(results, dimension)
        best_value = None
        best_source = None
        
        # Find best value for this dimension
        for tool_key, tool_data in dimension_data.items():
            for test_name, test_data in tool_data.items():
                if not isinstance(test_data, dict):
                    continue
                    
                # Extract relevant metric based on dimension
                value = None
                if dimension == 'throughput':
                    value = test_data.get('throughput_mbps') or test_data.get('write_bandwidth_mbps')
                elif dimension == 'iops':
                    value = test_data.get('write_iops') or test_data.get('read_iops')
                elif dimension == 'latency':
                    value = test_data.get('avg_latency_ms') or test_data.get('write_latency_ms')
                elif dimension == 'metadata':
                    # Look for any ops/sec metric
                    for key in test_data:
                        if 'per_sec' in key or 'ops' in key:
                            value = test_data[key]
                            break
                
                if value and (best_value is None or value > best_value):
                    best_value = value
                    best_source = f"{tool_key.replace('_tests', '').upper()}: {test_name.replace('_', ' ').title()}"
        
        if best_value:
            summary[dimension] = {
                'value': best_value,
                'source': best_source
            }
    
    return summary

# Made with Bob
