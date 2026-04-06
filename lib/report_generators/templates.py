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
        
        /* Analysis Section Styles */
        .analysis-section {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .analysis-section h2 {
            color: #667eea;
            margin-bottom: 25px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        /* Health Score Card */
        .health-score-card {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 30px;
            margin-bottom: 30px;
            padding: 25px;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .score-display {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .score-circle {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            font-weight: bold;
            color: #1f2937;
            position: relative;
        }
        
        .score-circle.excellent {
            background: conic-gradient(#10b981 0deg 306deg, #e5e7eb 306deg 360deg);
        }
        
        .score-circle.good {
            background: conic-gradient(#3b82f6 0deg 270deg, #e5e7eb 270deg 360deg);
        }
        
        .score-circle.fair {
            background: conic-gradient(#f59e0b 0deg 216deg, #e5e7eb 216deg 360deg);
        }
        
        .score-circle.poor {
            background: conic-gradient(#ef4444 0deg 180deg, #e5e7eb 180deg 360deg);
        }
        
        .score-label {
            font-size: 14px;
            color: #6b7280;
            margin-top: 5px;
        }
        
        .severity-badges {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .severity-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
        }
        
        .severity-badge.critical {
            background: #fee2e2;
            color: #991b1b;
        }
        
        .severity-badge.warning {
            background: #fef3c7;
            color: #92400e;
        }
        
        .severity-badge.info {
            background: #dbeafe;
            color: #1e40af;
        }
        
        .severity-badge .count {
            font-size: 18px;
            font-weight: bold;
        }
        
        /* Insights Grid */
        .insights-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .insight-card {
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid;
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .insight-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .insight-card.critical {
            background: #fef2f2;
            border-left-color: #ef4444;
        }
        
        .insight-card.warning {
            background: #fffbeb;
            border-left-color: #f59e0b;
        }
        
        .insight-card.info {
            background: #eff6ff;
            border-left-color: #3b82f6;
        }
        
        .insight-card h4 {
            margin-bottom: 12px;
            color: #1f2937;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .insight-card p {
            color: #4b5563;
            line-height: 1.6;
            margin-bottom: 12px;
        }
        
        .insight-recommendation {
            margin-top: 15px;
            padding: 12px;
            background: rgba(255,255,255,0.7);
            border-radius: 6px;
            border-left: 3px solid #667eea;
            font-size: 14px;
            color: #374151;
        }
        
        .insight-recommendation::before {
            content: '💡 ';
            font-weight: bold;
        }
        
        /* Recommendations Section */
        .recommendations-section {
            background: #f9fafb;
            padding: 25px;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
        }
        
        .recommendations-section h3 {
            color: #667eea;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .recommendations-container {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .recommendation-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .recommendation-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .recommendation-header h4 {
            margin: 0;
            color: #1f2937;
            font-size: 16px;
        }
        
        .priority-badge {
            padding: 4px 12px;
            border-radius: 12px;
            color: white;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .recommendation-card p {
            color: #6b7280;
            margin: 10px 0;
            line-height: 1.6;
        }
        
        .recommendation-actions {
            list-style: none;
            padding: 0;
            margin: 15px 0 0 0;
        }
        
        .recommendation-actions li {
            padding: 8px 12px;
            margin-bottom: 6px;
            background: #f3f4f6;
            border-radius: 4px;
            border-left: 3px solid #667eea;
            font-size: 14px;
            color: #374151;
        }
        
        .recommendation-actions li:before {
            content: "✓ ";
            color: #667eea;
            font-weight: bold;
            margin-right: 8px;
        }
        
        .recommendations-list li::before {
            content: '✓';
            color: #10b981;
            font-weight: bold;
            font-size: 18px;
        }
        
        /* No Analysis Message */
        .no-analysis {
            padding: 20px;
            text-align: center;
            color: #6b7280;
            font-style: italic;
        }
        
        /* Analysis Error */
        .analysis-error {
            padding: 20px;
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 8px;
            color: #991b1b;
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
    Generate header HTML with test metadata.
    
    Args:
        title: Main title
        subtitle: Subtitle text
        metadata: Optional metadata to display (includes test_metadata fields)
        
    Returns:
        Header HTML string
    """
    metadata_html = ""
    if metadata:
        meta_items = []
        
        # Primary metadata (test_id, server, mount path)
        if 'test_id' in metadata:
            meta_items.append(f"<strong>Test ID:</strong> {metadata['test_id']}")
        if 'server_ip' in metadata:
            meta_items.append(f"<strong>Server:</strong> {metadata['server_ip']}")
        if 'mount_path' in metadata:
            meta_items.append(f"<strong>Mount Path:</strong> {metadata['mount_path']}")
        
        # Transport and test mode
        if 'transport' in metadata:
            meta_items.append(f"<strong>Transport:</strong> {metadata['transport'].upper()}")
        if 'test_mode' in metadata:
            meta_items.append(f"<strong>Test Mode:</strong> {metadata['test_mode'].title()}")
        
        # Versions tested
        if 'versions_tested' in metadata:
            versions = metadata['versions_tested']
            if isinstance(versions, list):
                versions_str = ', '.join([f"NFSv{v}" for v in versions])
            else:
                versions_str = str(versions)
            meta_items.append(f"<strong>Versions:</strong> {versions_str}")
        elif 'versions' in metadata:
            meta_items.append(f"<strong>Versions:</strong> {metadata['versions']}")
        
        # Timestamp
        if 'timestamp' in metadata:
            meta_items.append(f"<strong>Timestamp:</strong> {metadata['timestamp']}")
        
        if meta_items:
            metadata_html = f"""
            <div style="margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 8px; font-size: 0.95em;">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px;">
                    {''.join([f'<div>{item}</div>' for item in meta_items])}
                </div>
            </div>
            """
    
    return f"""
    <div class="header">
        <h1>🚀 {title}</h1>
        <p>{subtitle}</p>
        {metadata_html}
    </div>
    """


def get_comparison_header_html(title: str, subtitle: str,
                               metadata_1: Dict[str, Any] = None,
                               metadata_2: Dict[str, Any] = None) -> str:
    """
    Generate comparison header HTML with metadata from both test-ids.
    
    Args:
        title: Main title
        subtitle: Subtitle text
        metadata_1: Metadata from first test-id
        metadata_2: Metadata from second test-id
        
    Returns:
        Comparison header HTML string
    """
    def format_metadata_column(metadata: Dict[str, Any], label: str) -> str:
        """Format metadata for one test-id as a column."""
        if not metadata:
            return f"<div><h3>{label}</h3><p>No metadata available</p></div>"
        
        items = []
        
        # Test ID
        if 'test_id' in metadata:
            items.append(f"<div><strong>Test ID:</strong> {metadata['test_id']}</div>")
        
        # Server and mount
        if 'server_ip' in metadata:
            items.append(f"<div><strong>Server:</strong> {metadata['server_ip']}</div>")
        if 'mount_path' in metadata:
            items.append(f"<div><strong>Mount Path:</strong> {metadata['mount_path']}</div>")
        
        # Transport and mode
        if 'transport' in metadata:
            items.append(f"<div><strong>Transport:</strong> {metadata['transport'].upper()}</div>")
        if 'test_mode' in metadata:
            items.append(f"<div><strong>Test Mode:</strong> {metadata['test_mode'].title()}</div>")
        
        # Versions
        if 'versions_tested' in metadata:
            versions = metadata['versions_tested']
            if isinstance(versions, list):
                versions_str = ', '.join([f"NFSv{v}" for v in versions])
            else:
                versions_str = str(versions)
            items.append(f"<div><strong>Versions:</strong> {versions_str}</div>")
        
        # Timestamp
        if 'timestamp' in metadata:
            items.append(f"<div><strong>Timestamp:</strong> {metadata['timestamp']}</div>")
        
        return f"""
        <div style="flex: 1; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 8px;">
            <h3 style="margin-bottom: 15px; font-size: 1.1em; border-bottom: 2px solid rgba(255,255,255,0.3); padding-bottom: 8px;">{label}</h3>
            <div style="display: flex; flex-direction: column; gap: 8px; font-size: 0.95em;">
                {''.join(items)}
            </div>
        </div>
        """
    
    metadata_html = ""
    if metadata_1 or metadata_2:
        col1 = format_metadata_column(metadata_1 or {}, "Test Configuration 1")
        col2 = format_metadata_column(metadata_2 or {}, "Test Configuration 2")
        
        metadata_html = f"""
        <div style="margin-top: 20px; display: flex; gap: 20px; flex-wrap: wrap;">
            {col1}
            {col2}
        </div>
        """
    
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


# Analysis Section Template Functions

def get_analysis_section_html(analysis: Dict[str, Any], report_style: str = 'tool') -> str:
    """
    Generate complete analysis section HTML.
    
    Args:
        analysis: Analysis results from PerformanceAnalyzer
        report_style: 'tool' or 'dimension' for style-specific rendering
        
    Returns:
        Complete analysis section HTML
    """
    if not analysis or not analysis.get('insights'):
        return get_no_analysis_html()
    
    health_score = analysis.get('overall_health', 0)
    severity_counts = analysis.get('severity_counts', {})
    insights = analysis.get('insights', [])
    recommendations = analysis.get('recommendations', [])
    
    # Generate health score card
    health_card_html = get_health_score_card_html(health_score, severity_counts)
    
    # Generate insights grid
    insights_html = get_insights_grid_html(insights, report_style)
    
    # Generate recommendations
    recommendations_html = get_recommendations_html(recommendations)
    
    return f"""
    <div class="analysis-section">
        <h2>🔍 Performance Analysis & Insights</h2>
        {health_card_html}
        {insights_html}
        {recommendations_html}
    </div>
    """


def get_health_score_card_html(health_score: Any, severity_counts: Dict[str, int]) -> str:
    """
    Generate health score card with severity badges.
    
    Args:
        health_score: Overall health score (0-100) or dict with score/status/color
        severity_counts: Dictionary with counts for critical, warning, info
        
    Returns:
        Health score card HTML
    """
    # Handle dict format from PerformanceAnalyzer
    if isinstance(health_score, dict):
        score_value = health_score.get('score', 0)
        category = health_score.get('status', 'poor')
        # Map status to label
        label_map = {
            'excellent': 'Excellent',
            'good': 'Good',
            'fair': 'Fair',
            'poor': 'Needs Attention',
            'critical': 'Critical'
        }
        label = label_map.get(category, 'Unknown')
        # Map status to color
        color_map = {
            'excellent': '#10b981',
            'good': '#3b82f6',
            'fair': '#f59e0b',
            'poor': '#ef4444',
            'critical': '#dc2626'
        }
        color = color_map.get(category, '#6b7280')
    else:
        # Handle numeric format
        score_value = health_score
        if score_value >= 85:
            category = 'excellent'
            label = 'Excellent'
            color = '#10b981'
        elif score_value >= 70:
            category = 'good'
            label = 'Good'
            color = '#3b82f6'
        elif score_value >= 50:
            category = 'fair'
            label = 'Fair'
            color = '#f59e0b'
        else:
            category = 'poor'
            label = 'Needs Attention'
            color = '#ef4444'
    
    critical_count = severity_counts.get('critical', 0)
    warning_count = severity_counts.get('warning', 0)
    info_count = severity_counts.get('info', 0)
    
    badges_html = ''
    if critical_count > 0:
        badges_html += f'<div class="severity-badge critical"><span class="count">{critical_count}</span> Critical</div>'
    if warning_count > 0:
        badges_html += f'<div class="severity-badge warning"><span class="count">{warning_count}</span> Warnings</div>'
    if info_count > 0:
        badges_html += f'<div class="severity-badge info"><span class="count">{info_count}</span> Info</div>'
    
    return f"""
    <div class="health-score-card">
        <div class="score-display">
            <div class="score-circle {category}">
                <span>{score_value:.0f}</span>
            </div>
            <div>
                <div style="font-size: 20px; font-weight: 600; color: {color};">{label}</div>
                <div class="score-label">Overall Health Score</div>
            </div>
        </div>
        <div class="severity-badges">
            {badges_html}
        </div>
    </div>
    """


def get_insights_grid_html(insights: List[Dict[str, Any]], report_style: str) -> str:
    """
    Generate insights grid with cards.
    
    Args:
        insights: List of insight dictionaries
        report_style: Report style for context
        
    Returns:
        Insights grid HTML
    """
    if not insights:
        return '<p class="no-analysis">No insights generated.</p>'
    
    # Sort insights by severity: critical, warning, info
    severity_order = {'critical': 0, 'warning': 1, 'info': 2}
    sorted_insights = sorted(insights, key=lambda x: severity_order.get(x.get('severity', 'info'), 3))
    
    cards_html = []
    for insight in sorted_insights:
        severity = insight.get('severity', 'info')
        title = insight.get('title', 'Insight')
        description = insight.get('description', '')
        recommendation = insight.get('recommendation', '')
        
        # Add emoji based on severity
        emoji = {'critical': '🚨', 'warning': '⚠️', 'info': 'ℹ️'}.get(severity, 'ℹ️')
        
        recommendation_html = ''
        if recommendation:
            recommendation_html = f'<div class="insight-recommendation">{recommendation}</div>'
        
        card_html = f"""
        <div class="insight-card {severity}">
            <h4>{emoji} {severity.title()}: {title}</h4>
            <p>{description}</p>
            {recommendation_html}
        </div>
        """
        cards_html.append(card_html)
    
    return f'<div class="insights-grid">{"".join(cards_html)}</div>'


def get_recommendations_html(recommendations: List[Any]) -> str:
    """
    Generate recommendations section.
    
    Args:
        recommendations: List of recommendation dictionaries or strings
        
    Returns:
        Recommendations section HTML
    """
    if not recommendations:
        return ''
    
    recommendations_html = []
    for rec in recommendations:
        if isinstance(rec, dict):
            # Handle dict format from PerformanceAnalyzer
            priority = rec.get('priority', 'low')
            title = rec.get('title', 'Recommendation')
            description = rec.get('description', '')
            actions = rec.get('actions', [])
            
            # Priority badge
            priority_colors = {
                'high': '#ef4444',
                'medium': '#f59e0b',
                'low': '#3b82f6'
            }
            priority_color = priority_colors.get(priority, '#6b7280')
            
            actions_html = ''
            if actions:
                actions_items = ''.join([f'<li>{action}</li>' for action in actions])
                actions_html = f'<ul class="recommendation-actions">{actions_items}</ul>'
            
            rec_html = f"""
            <div class="recommendation-card">
                <div class="recommendation-header">
                    <h4>{title}</h4>
                    <span class="priority-badge" style="background-color: {priority_color};">{priority.upper()}</span>
                </div>
                <p>{description}</p>
                {actions_html}
            </div>
            """
            recommendations_html.append(rec_html)
        else:
            # Handle string format (backward compatibility)
            recommendations_html.append(f'<li>{rec}</li>')
    
    return f"""
    <div class="recommendations-section">
        <h3>🎯 Key Recommendations</h3>
        <div class="recommendations-container">
            {"".join(recommendations_html)}
        </div>
    </div>
    """


def get_no_analysis_html() -> str:
    """
    Generate message when analysis is disabled or unavailable.
    
    Returns:
        No analysis message HTML
    """
    return """
    <div class="analysis-section">
        <h2>🔍 Performance Analysis</h2>
        <p class="no-analysis">Analysis is disabled or unavailable for this report.</p>
    </div>
    """


def get_analysis_error_html(error: str) -> str:
    """
    Generate error message when analysis fails.
    
    Args:
        error: Error message string
        
    Returns:
        Analysis error HTML
    """
    return f"""
    <div class="analysis-section">
        <h2>🔍 Performance Analysis</h2>
        <div class="analysis-error">
            <strong>Analysis Error:</strong> {error}
            <p style="margin-top: 10px;">The report has been generated without performance analysis.</p>
        </div>
    </div>
    """


def get_comparison_analysis_html(test_id_1: str, analysis_1: Dict[str, Any],
                                test_id_2: str, analysis_2: Dict[str, Any],
                                comparison_insights: List[Dict[str, Any]],
                                report_style: str) -> str:
    """
    Generate comparison analysis HTML showing both test-ids side-by-side.
    
    Args:
        test_id_1: First test ID
        analysis_1: Analysis for first test
        test_id_2: Second test ID
        analysis_2: Analysis for second test
        comparison_insights: Additional comparison-specific insights
        report_style: Report style for rendering
        
    Returns:
        Comparison analysis HTML
    """
    # Generate side-by-side health scores
    health_comparison = f"""
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
        <div>
            <h3 style="text-align: center; color: #667eea; margin-bottom: 15px;">{test_id_1}</h3>
            {get_health_score_card_html(analysis_1.get('overall_health', 0), analysis_1.get('severity_counts', {}))}
        </div>
        <div>
            <h3 style="text-align: center; color: #667eea; margin-bottom: 15px;">{test_id_2}</h3>
            {get_health_score_card_html(analysis_2.get('overall_health', 0), analysis_2.get('severity_counts', {}))}
        </div>
    </div>
    """
    
    # Generate comparison insights
    comparison_insights_html = ''
    if comparison_insights:
        comparison_insights_html = f"""
        <div style="margin-bottom: 30px;">
            <h3 style="color: #667eea; margin-bottom: 15px;">📊 Comparison Insights</h3>
            {get_insights_grid_html(comparison_insights, report_style)}
        </div>
        """
    
    # Combine insights from both analyses - show all for detailed comparison
    insights_1 = analysis_1.get('insights', [])
    insights_2 = analysis_2.get('insights', [])
    
    # Create separate sections for each test-id's insights
    insights_html = ''
    if insights_1 or insights_2 or comparison_insights:
        insights_html = '<div style="margin-bottom: 30px;">'
        
        # Comparison insights first (if any)
        if comparison_insights:
            insights_html += f"""
            <h3 style="color: #667eea; margin-bottom: 15px;">📊 Comparison Insights</h3>
            {get_insights_grid_html(comparison_insights, report_style)}
            """
        
        # Test 1 insights
        if insights_1:
            insights_html += f"""
            <h3 style="color: #667eea; margin-bottom: 15px; margin-top: 20px;">🔍 {test_id_1} Insights</h3>
            {get_insights_grid_html(insights_1, report_style)}
            """
        
        # Test 2 insights
        if insights_2:
            insights_html += f"""
            <h3 style="color: #667eea; margin-bottom: 15px; margin-top: 20px;">🔍 {test_id_2} Insights</h3>
            {get_insights_grid_html(insights_2, report_style)}
            """
        
        insights_html += '</div>'
    
    # Combine recommendations from both analyses - show all
    recs_1 = analysis_1.get('recommendations', [])
    recs_2 = analysis_2.get('recommendations', [])
    
    # Create separate sections for each test-id's recommendations
    recommendations_html = ''
    if recs_1 or recs_2:
        recommendations_html = '<div style="margin-bottom: 30px;">'
        
        # Test 1 recommendations
        if recs_1:
            recommendations_html += f"""
            <h3 style="color: #667eea; margin-bottom: 15px;">💡 {test_id_1} Recommendations</h3>
            {get_recommendations_html(recs_1)}
            """
        
        # Test 2 recommendations
        if recs_2:
            recommendations_html += f"""
            <h3 style="color: #667eea; margin-bottom: 15px; margin-top: 20px;">💡 {test_id_2} Recommendations</h3>
            {get_recommendations_html(recs_2)}
            """
        
        recommendations_html += '</div>'
    
    return f"""
    <div class="analysis-section">
        <h2>🔍 Comparative Performance Analysis</h2>
        {health_comparison}
        {comparison_insights_html}
        {insights_html}
        {recommendations_html}
    </div>
    """


# Made with Bob
