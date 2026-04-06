#!/usr/bin/env python3
"""
HTML template management for report generators

Provides reusable HTML templates and styling for all report types.
Includes dimension-based templates for organizing results by performance dimensions.
"""

from typing import Dict, Any, List
from . import dimension_mapper


def get_base_styles() -> str:
    """
    Get base CSS styles for all reports.
    
    Returns:
        CSS style string
    """
    return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        .metric-card h3 {
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .metric-card .value {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }
        
        .metric-card .unit {
            font-size: 0.9em;
            color: #666;
            margin-left: 5px;
        }
        
        .section {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .section h2 {
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }
        
        .test-result {
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }
        
        .test-result.passed {
            border-left-color: #10b981;
        }
        
        .test-result.failed {
            border-left-color: #ef4444;
        }
        
        .test-result h4 {
            color: #333;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .status-badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-badge.passed {
            background: #d1fae5;
            color: #065f46;
        }
        
        .status-badge.failed {
            background: #fee2e2;
            color: #991b1b;
        }
        
        .test-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
        }
        
        .test-metric {
            display: flex;
            justify-content: space-between;
            padding: 8px;
            background: white;
            border-radius: 4px;
        }
        
        .test-metric .label {
            color: #666;
            font-size: 0.9em;
        }
        
        .test-metric .value {
            font-weight: bold;
            color: #333;
        }
        
        .chart-container {
            margin: 20px 0;
            background: white;
            padding: 20px;
            border-radius: 8px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        table thead {
            background: #667eea;
            color: white;
        }
        
        table th {
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        
        table td {
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        table tbody tr:hover {
            background: #f9fafb;
        }
        
        table tr.success {
            background: #d1fae5;
        }
        
        table tr.warning {
            background: #fef3c7;
        }
        
        table tr.critical {
            background: #fee2e2;
        }
        
        .version-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .version-card {
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .version-card h3 {
            color: #667eea;
            margin-bottom: 10px;
        }
    """


def get_base_template(title: str, content: str) -> str:
    """
    Get base HTML template with content.
    
    Args:
        title: Page title
        content: HTML content to insert
        
    Returns:
        Complete HTML document
    """
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {get_base_styles()}
    </style>
</head>
<body>
    {content}
</body>
</html>
"""


def get_header_html(title: str, subtitle: str, metadata: Dict[str, Any] = None) -> str:
    """
    Generate header HTML.
    
    Args:
        title: Main title
        subtitle: Subtitle text
        metadata: Optional metadata to display
        
    Returns:
        Header HTML string
    """
    metadata_html = ""
    if metadata:
        meta_items = []
        if 'test_id' in metadata:
            meta_items.append(f"Test ID: {metadata['test_id']}")
        if 'server_ip' in metadata:
            meta_items.append(f"Server: {metadata['server_ip']}")
        if 'versions' in metadata:
            meta_items.append(f"Versions: {metadata['versions']}")
        if 'timestamp' in metadata:
            meta_items.append(f"Generated: {metadata['timestamp']}")
        
        if meta_items:
            metadata_html = f"<p>{' | '.join(meta_items)}</p>"
    
    return f"""
    <div class="header">
        <h1>🚀 {title}</h1>
        <p>{subtitle}</p>
        {metadata_html}
    </div>
    """


def get_metric_card_html(title: str, value: str, unit: str = "", description: str = "") -> str:
    """
    Generate metric card HTML.
    
    Args:
        title: Card title
        value: Metric value
        unit: Optional unit string
        description: Optional description text
        
    Returns:
        Metric card HTML
    """
    unit_html = f'<span class="unit">{unit}</span>' if unit else ''
    desc_html = f'<p style="font-size: 0.9em; color: #666; margin-top: 10px;">{description}</p>' if description else ''
    
    return f"""
    <div class="metric-card">
        <h3>{title}</h3>
        <div class="value">{value}{unit_html}</div>
        {desc_html}
    </div>
    """


def get_section_html(title: str, content: str) -> str:
    """
    Generate section HTML.
    
    Args:
        title: Section title
        content: Section content HTML
        
    Returns:
        Section HTML
    """
    return f"""
    <div class="section">
        <h2>{title}</h2>
        {content}
    </div>
    """


def get_test_result_html(test_name: str, status: str, metrics: Dict[str, Any]) -> str:
    """
    Generate test result HTML.
    
    Args:
        test_name: Name of the test
        status: Test status (passed/failed)
        metrics: Dictionary of metrics to display
        
    Returns:
        Test result HTML
    """
    status_class = 'passed' if status == 'passed' else 'failed'
    
    metrics_html = '<div class="test-metrics">'
    for label, value in metrics.items():
        metrics_html += f"""
        <div class="test-metric">
            <span class="label">{label}:</span>
            <span class="value">{value}</span>
        </div>
        """
    metrics_html += '</div>'
    
    return f"""
    <div class="test-result {status_class}">
        <h4>
            {test_name.replace('_', ' ').title()}
            <span class="status-badge {status_class}">{status}</span>
        </h4>
        {metrics_html}
    </div>
    """


def get_table_html(headers: List[str], rows: List[List[str]], row_classes: List[str] = None) -> str:
    """
    Generate table HTML.
    
    Args:
        headers: List of header strings
        rows: List of row data (each row is a list of cell values)
        row_classes: Optional list of CSS classes for each row
        
    Returns:
        Table HTML
    """
    header_html = '<tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr>'
    
    rows_html = ''
    for i, row in enumerate(rows):
        row_class = row_classes[i] if row_classes and i < len(row_classes) else ''
        rows_html += f'<tr class="{row_class}">'
        rows_html += ''.join(f'<td>{cell}</td>' for cell in row)
        rows_html += '</tr>'
    
    return f"""
    <table>
        <thead>{header_html}</thead>
        <tbody>{rows_html}</tbody>
    </table>
    """


def get_version_card_html(version: str, metadata: Dict[str, Any]) -> str:
    """
    Generate version card HTML for multi-version reports.
    
    Args:
        version: Version identifier (e.g., "NFSv3 TCP")
        metadata: Version metadata
        
    Returns:
        Version card HTML
    """
    meta_items = []
    if 'tests_passed' in metadata:
        meta_items.append(f"<p><strong>Tests Passed:</strong> {metadata['tests_passed']}</p>")
    if 'tests_failed' in metadata:
        meta_items.append(f"<p><strong>Tests Failed:</strong> {metadata['tests_failed']}</p>")
    if 'duration' in metadata:
        meta_items.append(f"<p><strong>Duration:</strong> {metadata['duration']}</p>")
    
    meta_html = ''.join(meta_items)
    
    return f"""
    <div class="version-card">
        <h3>{version}</h3>
        {meta_html}
    </div>
    """


def get_comparison_grid_html(test_id_1: str, test_id_2: str, 
                             metadata_1: Dict[str, Any], 
                             metadata_2: Dict[str, Any]) -> str:
    """
    Generate comparison grid HTML for test-ID comparison.
    
    Args:
        test_id_1: First test ID
        test_id_2: Second test ID
        metadata_1: Metadata for first test
        metadata_2: Metadata for second test
        
    Returns:
        Comparison grid HTML
    """
    card1 = get_version_card_html(test_id_1, metadata_1)
    card2 = get_version_card_html(test_id_2, metadata_2)
    
    return f"""
    <div class="version-grid">
        {card1}
        {card2}
    </div>
    """


def get_no_data_html(message: str = "No data available") -> str:
    """
    Generate HTML for no data scenarios.
    
    Args:
        message: Message to display
        
    Returns:
        No data HTML
    """
    return f'<p style="color: #666; font-style: italic;">{message}</p>'


def get_error_html(error_message: str) -> str:
    """
    Generate error message HTML.
    
    Args:
        error_message: Error message to display
        
    Returns:
        Error HTML
    """
    return f"""
    <div style="background: #fee2e2; color: #991b1b; padding: 20px; border-radius: 8px; border-left: 4px solid #ef4444;">
        <h4 style="margin-bottom: 10px;">⚠️ Error</h4>
        <p>{error_message}</p>
    </div>
    """


# ========== Dimension-Based Template Functions ==========

def get_dimension_header_html(dimension_key: str) -> str:
    """
    Generate dimension section header with icon and description.
    
    Args:
        dimension_key: Dimension key (e.g., 'throughput', 'iops')
        
    Returns:
        Dimension header HTML
    """
    dim_info = dimension_mapper.get_dimension_info(dimension_key)
    
    return f"""
    <div style="margin-bottom: 20px;">
        <h3 style="color: #667eea; font-size: 1.5em; margin-bottom: 10px;">
            {dim_info['icon']} {dim_info['name']}
        </h3>
        <p style="color: #666; font-size: 1em; line-height: 1.6;">
            {dim_info['description']}
        </p>
    </div>
    """


def get_dimension_test_result_html(tool_name: str, test_name: str,
                                   status: str, metrics: Dict[str, Any]) -> str:
    """
    Generate test result HTML for dimension-based reports.
    
    Similar to get_test_result_html but includes tool name prefix.
    
    Args:
        tool_name: Name of the tool (e.g., 'DD', 'FIO')
        test_name: Name of the test
        status: Test status (passed/failed)
        metrics: Dictionary of metrics to display
        
    Returns:
        Test result HTML
    """
    status_class = 'passed' if status == 'passed' else 'failed'
    
    metrics_html = '<div class="test-metrics">'
    for label, value in metrics.items():
        metrics_html += f"""
        <div class="test-metric">
            <span class="label">{label}:</span>
            <span class="value">{value}</span>
        </div>
        """
    metrics_html += '</div>'
    
    return f"""
    <div class="test-result {status_class}">
        <h4>
            <span style="color: #667eea; font-weight: normal;">{tool_name}:</span> {test_name.replace('_', ' ').title()}
            <span class="status-badge {status_class}">{status}</span>
        </h4>
        {metrics_html}
    </div>
    """


def get_dimension_summary_card_html(dimension_key: str, best_value: float,
                                   source: str, unit: str = "") -> str:
    """
    Generate summary card for a dimension showing best performance.
    
    Args:
        dimension_key: Dimension key
        best_value: Best performance value
        source: Source of best performance (tool and test)
        unit: Unit string
        
    Returns:
        Dimension summary card HTML
    """
    dim_info = dimension_mapper.get_dimension_info(dimension_key)
    
    # Format value based on magnitude
    if best_value >= 1000:
        formatted_value = f"{best_value:,.0f}"
    elif best_value >= 10:
        formatted_value = f"{best_value:.1f}"
    else:
        formatted_value = f"{best_value:.2f}"
    
    return f"""
    <div class="metric-card">
        <h3>{dim_info['icon']} {dim_info['name']}</h3>
        <div class="value">{formatted_value}<span class="unit">{unit}</span></div>
        <p style="font-size: 0.85em; color: #666; margin-top: 10px;">
            <strong>Best:</strong> {source}
        </p>
    </div>
    """


def get_dimension_section_html(dimension_key: str, dimension_data: Dict[str, Any],
                               chart_html: str = "") -> str:
    """
    Generate complete dimension section with header, chart, and test results.
    
    Args:
        dimension_key: Dimension key
        dimension_data: Extracted dimension data from dimension_mapper
        chart_html: Optional chart HTML
        
    Returns:
        Complete dimension section HTML
    """
    content = get_dimension_header_html(dimension_key)
    
    # Add chart if provided
    if chart_html:
        content += f'<div class="chart-container">{chart_html}</div>'
    
    # Add test results organized by tool
    tool_names = {
        'dd_tests': 'DD',
        'fio_tests': 'FIO',
        'iozone_tests': 'IOzone',
        'bonnie_tests': 'Bonnie++',
        'dbench_tests': 'DBench'
    }
    
    for tool_key, tool_data in dimension_data.items():
        if not tool_data:
            continue
        
        tool_name = tool_names.get(tool_key, tool_key.replace('_tests', '').upper())
        
        # Add tool subsection
        content += f'<h4 style="color: #667eea; margin-top: 20px; margin-bottom: 10px;">{tool_name} Tests</h4>'
        
        for test_name, test_data in tool_data.items():
            if not isinstance(test_data, dict):
                continue
            
            status = test_data.get('status', 'unknown')
            
            # Extract relevant metrics based on dimension
            metrics = {}
            if dimension_key == 'throughput':
                if 'throughput_mbps' in test_data:
                    metrics['Throughput'] = f"{test_data['throughput_mbps']:.2f} MB/s"
                if 'write_bandwidth_mbps' in test_data:
                    metrics['Write Bandwidth'] = f"{test_data['write_bandwidth_mbps']:.2f} MB/s"
                if 'read_bandwidth_mbps' in test_data:
                    metrics['Read Bandwidth'] = f"{test_data['read_bandwidth_mbps']:.2f} MB/s"
            
            elif dimension_key == 'iops':
                if 'read_iops' in test_data:
                    metrics['Read IOPS'] = f"{test_data['read_iops']:,.0f}"
                if 'write_iops' in test_data:
                    metrics['Write IOPS'] = f"{test_data['write_iops']:,.0f}"
            
            elif dimension_key == 'latency':
                if 'avg_latency_ms' in test_data:
                    metrics['Avg Latency'] = f"{test_data['avg_latency_ms']:.2f} ms"
                if 'read_latency_ms' in test_data:
                    metrics['Read Latency'] = f"{test_data['read_latency_ms']:.2f} ms"
                if 'write_latency_ms' in test_data:
                    metrics['Write Latency'] = f"{test_data['write_latency_ms']:.2f} ms"
            
            elif dimension_key == 'metadata':
                # Look for any ops/sec metrics
                for key, value in test_data.items():
                    if ('per_sec' in key or 'ops' in key) and isinstance(value, (int, float)):
                        label = key.replace('_', ' ').replace('per sec', '/sec').title()
                        metrics[label] = f"{value:,.0f}"
            
            elif dimension_key == 'cache_effects':
                # Handle cache comparison data
                if 'cached' in test_data and 'direct' in test_data:
                    cached = test_data['cached']
                    direct = test_data['direct']
                    if isinstance(cached, dict) and isinstance(direct, dict):
                        cached_tp = cached.get('throughput_mbps', 0)
                        direct_tp = direct.get('throughput_mbps', 0)
                        if cached_tp > 0 and direct_tp > 0:
                            metrics['Cached I/O'] = f"{cached_tp:.2f} MB/s"
                            metrics['Direct I/O'] = f"{direct_tp:.2f} MB/s"
                            improvement = ((cached_tp - direct_tp) / direct_tp) * 100
                            metrics['Cache Benefit'] = f"{improvement:.1f}%"
            
            elif dimension_key == 'concurrency':
                if 'num_clients' in test_data:
                    metrics['Clients'] = str(test_data['num_clients'])
                if 'num_threads' in test_data:
                    metrics['Threads'] = str(test_data['num_threads'])
                if 'throughput_mbps' in test_data:
                    metrics['Throughput'] = f"{test_data['throughput_mbps']:.2f} MB/s"
            
            # Add duration if available
            if 'duration' in test_data:
                metrics['Duration'] = test_data['duration']
            
            if metrics:
                content += get_dimension_test_result_html(tool_name, test_name, status, metrics)
    
    return get_section_html(f"{dimension_mapper.get_dimension_info(dimension_key)['icon']} {dimension_mapper.get_dimension_info(dimension_key)['name']}", content)


def get_dimension_overview_html(test_results: Dict[str, Any]) -> str:
    """
    Generate dimension overview section with summary cards for all dimensions.
    
    Args:
        test_results: Full test results dictionary
        
    Returns:
        Dimension overview HTML
    """
    summary = dimension_mapper.get_dimension_summary(test_results)
    
    if not summary:
        return get_no_data_html("No dimension summary available")
    
    cards_html = '<div class="summary-grid">'
    
    # Define units for each dimension
    units = {
        'throughput': 'MB/s',
        'iops': 'ops/sec',
        'latency': 'ms',
        'metadata': 'ops/sec',
        'cache_effects': 'MB/s',
        'concurrency': 'MB/s'
    }
    
    for dimension_key in dimension_mapper.get_all_dimensions():
        if dimension_key in summary:
            dim_summary = summary[dimension_key]
            cards_html += get_dimension_summary_card_html(
                dimension_key,
                dim_summary['value'],
                dim_summary['source'],
                units.get(dimension_key, '')
            )
    
    cards_html += '</div>'
    
    return get_section_html("📊 Performance Dimensions Overview", cards_html)

# Made with Bob

    # ========== Multi-Version Dimension-Based Template Functions ==========
    
    def get_multi_version_dimension_section_html(dimension_key: str, 
                                                 results_by_version: Dict[str, Dict],
                                                 chart_html: str = "") -> str:
        """
        Generate dimension section for multi-version report.
        
        Shows one dimension across all NFS versions with comparison.
        
        Args:
            dimension_key: Dimension key (e.g., 'throughput')
            results_by_version: Results organized by NFS version
            chart_html: Optional chart HTML
            
        Returns:
            Complete dimension section HTML
        """
        dim_info = dimension_mapper.get_dimension_info(dimension_key)
        
        content = f"""
        <div style="margin-bottom: 20px;">
            <h3 style="color: #667eea; font-size: 1.5em; margin-bottom: 10px;">
                {dim_info['icon']} {dim_info['name']}
            </h3>
            <p style="color: #666; font-size: 1em; line-height: 1.6;">
                {dim_info['description']}
            </p>
        </div>
        """
        
        # Add chart if provided
        if chart_html:
            content += f'<div class="chart-container">{chart_html}</div>'
        
        # Add version comparison table
        versions = sorted(results_by_version.keys())
        
        # Extract dimension data for each version
        version_summaries = {}
        for version_key in versions:
            version_results = results_by_version[version_key]
            dimension_data = dimension_mapper.extract_dimension_data(version_results, dimension_key)
            
            # Find best value for this version in this dimension
            best_value = 0
            best_test = "N/A"
            
            for tool_key, tool_data in dimension_data.items():
                tool_name = tool_key.replace('_tests', '').upper()
                for test_name, test_data in tool_data.items():
                    if not isinstance(test_data, dict) or test_data.get('status') != 'passed':
                        continue
                    
                    # Extract relevant metric
                    value = 0
                    if dimension_key == 'throughput':
                        value = (test_data.get('throughput_mbps') or 
                                test_data.get('write_bandwidth_mbps') or 
                                test_data.get('sequential_output_block_mbps') or 0)
                    elif dimension_key == 'iops':
                        value = max(test_data.get('write_iops', 0), test_data.get('read_iops', 0))
                    elif dimension_key == 'latency':
                        value = test_data.get('avg_latency_ms') or test_data.get('write_latency_ms', 0)
                    
                    if value > best_value:
                        best_value = value
                        best_test = f"{tool_name}: {test_name.replace('_', ' ').title()}"
            
            version_summaries[version_key] = {
                'best_value': best_value,
                'best_test': best_test
            }
        
        # Create comparison table
        if version_summaries:
            content += '<h4 style="color: #667eea; margin-top: 20px; margin-bottom: 10px;">Version Comparison</h4>'
            content += '<table><thead><tr><th>NFS Version</th><th>Best Performance</th><th>Test</th></tr></thead><tbody>'
            
            for version_key in versions:
                summary = version_summaries[version_key]
                version_display = version_key.replace('_', ' ').upper()
                
                # Format value based on dimension
                if dimension_key == 'throughput':
                    value_str = f"{summary['best_value']:.2f} MB/s"
                elif dimension_key == 'iops':
                    value_str = f"{summary['best_value']:,.0f} IOPS"
                elif dimension_key == 'latency':
                    value_str = f"{summary['best_value']:.2f} ms"
                else:
                    value_str = f"{summary['best_value']:.2f}"
                
                content += f"<tr><td><strong>{version_display}</strong></td><td>{value_str}</td><td>{summary['best_test']}</td></tr>"
            
            content += '</tbody></table>'
        
        return get_section_html(f"{dim_info['icon']} {dim_info['name']}", content)
    
    def get_multi_version_dimension_overview_html(results_by_version: Dict[str, Dict]) -> str:
        """
        Generate dimension overview for multi-version report.
        
        Shows summary cards comparing best performance across versions for each dimension.
        
        Args:
            results_by_version: Results organized by NFS version
            
        Returns:
            Dimension overview HTML
        """
        versions = sorted(results_by_version.keys())
        
        # Calculate best performance per dimension per version
        dimension_comparison = {}
        
        for dimension_key in dimension_mapper.get_all_dimensions():
            dimension_comparison[dimension_key] = {}
            
            for version_key in versions:
                version_results = results_by_version[version_key]
                summary = dimension_mapper.get_dimension_summary(version_results)
                
                if dimension_key in summary:
                    dimension_comparison[dimension_key][version_key] = summary[dimension_key]['value']
        
        # Generate overview cards
        cards_html = '<div class="summary-grid">'
        
        units = {
            'throughput': 'MB/s',
            'iops': 'ops/sec',
            'latency': 'ms',
            'metadata': 'ops/sec',
            'cache_effects': 'MB/s',
            'concurrency': 'MB/s'
        }
        
        for dimension_key in dimension_mapper.get_all_dimensions():
            dim_info = dimension_mapper.get_dimension_info(dimension_key)
            dim_data = dimension_comparison.get(dimension_key, {})
            
            if not dim_data:
                continue
            
            # Find best version for this dimension
            best_version = max(dim_data.items(), key=lambda x: x[1]) if dim_data else (None, 0)
            
            if best_version[0]:
                cards_html += f"""
                <div class="metric-card">
                    <h3>{dim_info['icon']} {dim_info['name']}</h3>
                    <div class="value">{best_version[1]:.2f}<span class="unit">{units.get(dimension_key, '')}</span></div>
                    <p style="font-size: 0.85em; color: #666; margin-top: 10px;">
                        <strong>Best:</strong> {best_version[0].replace('_', ' ').upper()}
                    </p>
                </div>
                """
        
        cards_html += '</div>'
        
        return get_section_html("📊 Performance Dimensions Overview", cards_html)
