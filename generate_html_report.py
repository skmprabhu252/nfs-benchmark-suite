#!/usr/bin/env python3
"""
Generate HTML Report from NFS Benchmark Suite Results

This script converts JSON test results into an interactive HTML report with charts.
Supports both single file and multi-file (test-id based) report generation.

Usage:
    # Single file
    python generate_html_report.py <json_file>
    python generate_html_report.py nfs_performance_test_20240403_120000.json
    
    # Multiple files by test-id
    python generate_html_report.py --test-id baseline_2026
    python generate_html_report.py --test-id prod_test
"""

import json
import sys
import os
import logging
import argparse
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Import performance analyzer
try:
    from lib.performance_analyzer import analyze_performance
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False
    logging.warning("Performance analyzer not available")

# Import historical comparison
try:
    from lib.historical_comparison import HistoricalComparison
    HISTORICAL_AVAILABLE = True
except ImportError:
    HISTORICAL_AVAILABLE = False
    logging.warning("Historical comparison not available")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Check for optional dependencies
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("plotly not installed. Charts will not be generated.")
    logger.info("Install with: pip3 install plotly")


def load_results(json_file):
    """Load test results from JSON file"""
    try:
        with open(json_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON file: {e}")
        sys.exit(1)


def find_test_id_files(test_id: str, directory: str = ".") -> List[str]:
    """
    Find all JSON files matching a test-id pattern.
    
    Args:
        test_id: Test identifier to search for
        directory: Directory to search in (default: current directory)
        
    Returns:
        List of matching file paths
    """
    pattern = f"nfs_performance_{test_id}_*.json"
    files = glob.glob(os.path.join(directory, pattern))
    return sorted(files)


def aggregate_test_results(json_files: List[str]) -> Dict[str, Any]:
    """
    Aggregate multiple JSON result files into a multi-version format.
    
    Args:
        json_files: List of JSON file paths to aggregate
        
    Returns:
        Aggregated results in multi-version format
    """
    if not json_files:
        raise ValueError("No JSON files provided for aggregation")
    
    # Load all results
    all_results = []
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                result = json.load(f)
                all_results.append((json_file, result))
        except Exception as e:
            logger.warning(f"Failed to load {json_file}: {e}")
            continue
    
    if not all_results:
        raise ValueError("No valid JSON files could be loaded")
    
    # Create aggregated structure
    aggregated = {
        'test_metadata': {},
        'results_by_version': {}
    }
    
    # Use metadata from first file as base
    first_file, first_result = all_results[0]
    if 'test_metadata' in first_result:
        aggregated['test_metadata'] = first_result['test_metadata'].copy()
    
    # Aggregate results by version
    for json_file, result in all_results:
        # Extract version and transport info
        nfs_version = result.get('nfs_version')
        transport = result.get('transport', 'tcp')
        
        if nfs_version:
            version_key = f"nfsv{nfs_version}_{transport}"
            aggregated['results_by_version'][version_key] = result.get('results', {})
            logger.info(f"Loaded {version_key} from {os.path.basename(json_file)}")
    
    if not aggregated['results_by_version']:
        raise ValueError("No version results found in JSON files")
    
    logger.info(f"Aggregated {len(aggregated['results_by_version'])} version results")
    return aggregated


def _safe_generate_html(func, *args, section_name="Section", **kwargs):
    """
    Safely execute HTML generation function with error handling.
    
    Args:
        func: HTML generation function to call
        *args: Positional arguments for the function
        section_name: Name of the section for error messages
        **kwargs: Keyword arguments for the function
        
    Returns:
        str: Generated HTML or error message
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"{section_name} generation failed: {e}")
        return f'''
        <div class="section">
            <h2>⚠️ {section_name} - Generation Error</h2>
            <p style="color: #ef4444;">Failed to generate this section due to an error.</p>
            <p style="color: #666; font-size: 0.9em;">Error: {str(e)}</p>
        </div>
        '''


def generate_html_report(results, output_file=None):
    """
    Generate HTML report from test results.
    
    Supports both single-version and multi-version result formats.
    """
    
    # Create report directory if it doesn't exist
    report_dir = Path("report")
    report_dir.mkdir(exist_ok=True)
    
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = report_dir / f"nfs_performance_report_{timestamp}.html"
    else:
        # Ensure output_file is in report directory
        output_file = report_dir / Path(output_file).name
    
    # Detect result format
    is_multi_version = 'test_metadata' in results and 'results_by_version' in results
    
    if is_multi_version:
        return generate_multi_version_report(results, output_file)
    else:
        return generate_single_version_report(results, output_file)


def generate_single_version_report(results, output_file):
    """Generate HTML report for single-version results (backward compatibility)."""
    
    # Extract data with None-safe defaults
    test_run = results.get('test_run') or {}
    dd_tests = results.get('dd_tests') or {}
    fio_tests = results.get('fio_tests') or {}
    iozone_tests = results.get('iozone_tests') or {}
    bonnie_tests = results.get('bonnie_tests') or {}
    dbench_tests = results.get('dbench_tests') or {}
    summary = results.get('summary') or {}
    nfs_stats = results.get('nfs_stats') or {}
    
    # Calculate statistics
    total_tests = summary.get('tests_passed', 0) + summary.get('tests_failed', 0)
    pass_rate = (summary.get('tests_passed', 0) / total_tests * 100) if total_tests > 0 else 0
    
    # Run performance analysis
    analysis_html = ""
    if ANALYZER_AVAILABLE:
        try:
            analysis = analyze_performance(results)
            analysis_html = generate_executive_summary_html(analysis)
        except Exception as e:
            logger.warning(f"Performance analysis failed: {e}")
    
    # Generate historical comparison
    historical_html = ""
    if HISTORICAL_AVAILABLE:
        try:
            hist = HistoricalComparison()
            comparison = hist.compare_with_previous(results)
            if comparison.get('has_previous'):
                historical_html = generate_historical_comparison_html(comparison)
        except Exception as e:
            logger.warning(f"Historical comparison failed: {e}")
    
    # Generate charts if plotly is available
    charts_html = ""
    if PLOTLY_AVAILABLE and (dd_tests or fio_tests or iozone_tests or bonnie_tests or dbench_tests):
        try:
            charts_html = generate_charts(dd_tests, fio_tests, iozone_tests, bonnie_tests, dbench_tests)
        except Exception as e:
            logger.warning(f"Chart generation failed: {e}")
            charts_html = '<div class="section"><h2>⚠️ Chart Generation Failed</h2><p>Charts could not be generated due to an error. Test results are still available below.</p></div>'
    
    # Generate HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NFS Benchmark Suite Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .metric-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        
        .metric-card h3 {{
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        
        .metric-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }}
        
        .metric-card .unit {{
            font-size: 0.9em;
            color: #666;
            margin-left: 5px;
        }}
        
        .section {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        
        .test-result {{
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
            background: #f9f9f9;
            border-radius: 5px;
        }}
        
        .test-result.passed {{
            border-left-color: #10b981;
        }}
        
        .test-result.failed {{
            border-left-color: #ef4444;
        }}
        
        .test-result h4 {{
            margin-bottom: 10px;
            color: #333;
        }}
        
        .test-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }}
        
        .test-metric {{
            display: flex;
            justify-content: space-between;
            padding: 8px;
            background: white;
            border-radius: 5px;
        }}
        
        .test-metric .label {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .test-metric .value {{
            font-weight: bold;
            color: #333;
        }}
        
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .status-badge.passed {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .status-badge.failed {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        th {{
            background: #f9fafb;
            font-weight: 600;
            color: #667eea;
        }}
        
        tr:hover {{
            background: #f9fafb;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 NFS Benchmark Suite Report</h1>
            <p><strong>Mount Path:</strong> {test_run.get('mount_path', 'N/A')}</p>
            <p><strong>Hostname:</strong> {test_run.get('hostname', 'N/A')}</p>
            <p><strong>Test Date:</strong> {test_run.get('timestamp', 'N/A')}</p>
        </div>
        
        <div class="summary-grid">
            <div class="metric-card">
                <h3>Total Tests</h3>
                <div class="value">{total_tests}</div>
            </div>
            <div class="metric-card">
                <h3>Tests Passed</h3>
                <div class="value" style="color: #10b981;">{summary.get('tests_passed', 0)}</div>
            </div>
            <div class="metric-card">
                <h3>Tests Failed</h3>
                <div class="value" style="color: #ef4444;">{summary.get('tests_failed', 0)}</div>
            </div>
            <div class="metric-card">
                <h3>Pass Rate</h3>
                <div class="value">{pass_rate:.1f}<span class="unit">%</span></div>
            </div>
            <div class="metric-card">
                <h3>Total Duration</h3>
                <div class="value">{summary.get('total_duration', 0):.1f}<span class="unit">s</span></div>
            </div>
        </div>
        
        {analysis_html}
        
        {historical_html}
        
        {_safe_generate_html(generate_cross_tool_comparison, dd_tests, fio_tests, iozone_tests, bonnie_tests, dbench_tests, section_name="Cross-Tool Comparison")}
        
        {charts_html}
        
        <div class="section">
            <h2>DD Test Results</h2>
            {_safe_generate_html(generate_dd_tests_html, dd_tests, section_name="DD Tests")}
        </div>
        
        <div class="section">
            <h2>FIO Test Results</h2>
            {_safe_generate_html(generate_fio_tests_html, fio_tests, section_name="FIO Tests")}
        </div>
        
        <div class="section">
            <h2>IOzone Test Results</h2>
            {_safe_generate_html(generate_iozone_tests_html, iozone_tests, section_name="IOzone Tests")}
        </div>
        
        <div class="section">
            <h2>Bonnie++ Test Results</h2>
            {_safe_generate_html(generate_bonnie_tests_html, bonnie_tests, section_name="Bonnie++ Tests")}
        </div>
        
        <div class="section">
            <h2>DBench Test Results</h2>
            {_safe_generate_html(generate_dbench_tests_html, dbench_tests, section_name="DBench Tests")}
        </div>
        
        {_safe_generate_html(generate_nfs_stats_html, nfs_stats, section_name="NFS Statistics")}
        
        <div class="footer">
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>NFS Benchmark Suite</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Write HTML to file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"Report saved to: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Failed to write report file: {e}")
        return None


def generate_executive_summary_html(analysis: Dict[str, Any]) -> str:
    """
    Generate Executive Summary section with insights and recommendations.
    
    Args:
        analysis: Analysis results from PerformanceAnalyzer
        
    Returns:
        str: HTML content for executive summary
    """
    if not analysis:
        return ""
    
    health = analysis.get('overall_health', {})
    insights = analysis.get('insights', [])
    recommendations = analysis.get('recommendations', [])
    severity_counts = analysis.get('severity_counts', {})
    
    html = '<div class="section" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px;">'
    html += '<h2 style="color: white; margin-bottom: 20px;">🎯 Executive Summary</h2>'
    
    # Health Score
    score = health.get('score', 0)
    status = health.get('status', 'unknown')
    html += f'''
    <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h3 style="color: white; margin-bottom: 10px;">Overall Health Score</h3>
        <div style="font-size: 3em; font-weight: bold;">{score}/100</div>
        <div style="font-size: 1.2em; margin-top: 10px; text-transform: uppercase; letter-spacing: 2px;">{status}</div>
    </div>
    '''
    
    # Issue Summary
    if severity_counts.get('critical', 0) > 0 or severity_counts.get('warning', 0) > 0:
        html += '<div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 10px; margin-bottom: 20px;">'
        html += '<h3 style="color: white; margin-bottom: 15px;">Issues Found</h3>'
        html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">'
        
        if severity_counts.get('critical', 0) > 0:
            html += f'''
            <div style="background: rgba(239, 68, 68, 0.3); padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 2em; font-weight: bold;">{severity_counts['critical']}</div>
                <div style="font-size: 0.9em; margin-top: 5px;">Critical</div>
            </div>
            '''
        
        if severity_counts.get('warning', 0) > 0:
            html += f'''
            <div style="background: rgba(251, 191, 36, 0.3); padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 2em; font-weight: bold;">{severity_counts['warning']}</div>
                <div style="font-size: 0.9em; margin-top: 5px;">Warnings</div>
            </div>
            '''
        
        html += '</div></div>'
    
    html += '</div>'
    
    # Detailed Insights
    if insights:
        html += '<div class="section"><h2>🔍 Performance Insights</h2>'
        html += '<p style="color: #666; margin-bottom: 20px;">Automated analysis of test results with actionable recommendations</p>'
        
        for insight in insights:
            severity = insight.get('severity', 'info')
            title = insight.get('title', '')
            description = insight.get('description', '')
            recommendation = insight.get('recommendation', '')
            
            # Color coding by severity
            if severity == 'critical':
                border_color = '#ef4444'
                bg_color = '#fee2e2'
                icon = '🚨'
            elif severity == 'warning':
                border_color = '#f59e0b'
                bg_color = '#fef3c7'
                icon = '⚠️'
            else:
                border_color = '#3b82f6'
                bg_color = '#dbeafe'
                icon = 'ℹ️'
            
            html += f'''
            <div style="border-left: 4px solid {border_color}; background: {bg_color}; padding: 20px; margin-bottom: 15px; border-radius: 5px;">
                <h3 style="color: #333; margin-bottom: 10px;">{icon} {title}</h3>
                <p style="color: #555; margin-bottom: 10px;">{description}</p>
                <div style="background: white; padding: 15px; border-radius: 5px; margin-top: 10px;">
                    <strong style="color: #667eea;">💡 Recommendation:</strong>
                    <p style="color: #555; margin-top: 5px;">{recommendation}</p>
                </div>
            </div>
            '''
        
        html += '</div>'
    
    # Recommendations
    if recommendations:
        html += '<div class="section"><h2>📋 Action Items</h2>'
        html += '<p style="color: #666; margin-bottom: 20px;">Prioritized recommendations to improve NFS performance</p>'
        
        for rec in recommendations:
            priority = rec.get('priority', 'low')
            title = rec.get('title', '')
            description = rec.get('description', '')
            actions = rec.get('actions', [])
            
            # Priority styling
            if priority == 'high':
                priority_badge = '<span style="background: #ef4444; color: white; padding: 5px 10px; border-radius: 5px; font-size: 0.8em; font-weight: bold;">HIGH PRIORITY</span>'
            elif priority == 'medium':
                priority_badge = '<span style="background: #f59e0b; color: white; padding: 5px 10px; border-radius: 5px; font-size: 0.8em; font-weight: bold;">MEDIUM PRIORITY</span>'
            else:
                priority_badge = '<span style="background: #3b82f6; color: white; padding: 5px 10px; border-radius: 5px; font-size: 0.8em; font-weight: bold;">LOW PRIORITY</span>'
            
            html += f'''
            <div style="background: white; padding: 25px; margin-bottom: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="margin-bottom: 15px;">
                    {priority_badge}
                    <h3 style="color: #333; margin-top: 10px;">{title}</h3>
                </div>
                <p style="color: #666; margin-bottom: 15px;">{description}</p>
                <div style="background: #f9fafb; padding: 15px; border-radius: 5px;">
                    <strong style="color: #667eea;">Action Steps:</strong>
                    <ul style="margin-top: 10px; padding-left: 20px;">
            '''
            
            for action in actions:
                html += f'<li style="color: #555; margin-bottom: 5px;">{action}</li>'
            
            html += '''
                    </ul>
                </div>
            </div>
            '''
        
        html += '</div>'
    
    return html


def generate_historical_comparison_html(comparison: Dict[str, Any]) -> str:
    """
    Generate Historical Comparison section HTML.
    
    Args:
        comparison: Comparison dictionary from HistoricalComparison
        
    Returns:
        HTML string for historical comparison section
    """
    html = '<div class="section" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px;">'
    html += '<h2 style="color: white; margin-bottom: 20px;">📈 Historical Comparison</h2>'
    
    # Previous run info
    prev_date = comparison.get('previous_date', 'Unknown')
    html += f'<p style="color: rgba(255,255,255,0.9); margin-bottom: 20px;">Comparing with previous run: <strong>{prev_date}</strong></p>'
    
    # Summary
    summary = comparison.get('summary', {})
    total = summary.get('total_comparisons', 0)
    improvements = summary.get('improvements', 0)
    regressions = summary.get('regressions', 0)
    warnings = summary.get('warnings', 0)
    stable = summary.get('stable', 0)
    
    html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 25px;">'
    
    # Total comparisons
    html += f'''
    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; text-align: center;">
        <div style="font-size: 2em; font-weight: bold;">{total}</div>
        <div style="font-size: 0.9em; opacity: 0.9;">Total Metrics</div>
    </div>
    '''
    
    # Improvements
    html += f'''
    <div style="background: rgba(16,185,129,0.2); padding: 15px; border-radius: 8px; text-align: center;">
        <div style="font-size: 2em; font-weight: bold;">✅ {improvements}</div>
        <div style="font-size: 0.9em; opacity: 0.9;">Improved</div>
    </div>
    '''
    
    # Regressions
    html += f'''
    <div style="background: rgba(239,68,68,0.2); padding: 15px; border-radius: 8px; text-align: center;">
        <div style="font-size: 2em; font-weight: bold;">❌ {regressions}</div>
        <div style="font-size: 0.9em; opacity: 0.9;">Regressed</div>
    </div>
    '''
    
    # Warnings
    html += f'''
    <div style="background: rgba(245,158,11,0.2); padding: 15px; border-radius: 8px; text-align: center;">
        <div style="font-size: 2em; font-weight: bold;">⚠️ {warnings}</div>
        <div style="font-size: 0.9em; opacity: 0.9;">Warnings</div>
    </div>
    '''
    
    # Stable
    html += f'''
    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; text-align: center;">
        <div style="font-size: 2em; font-weight: bold;">➡️ {stable}</div>
        <div style="font-size: 0.9em; opacity: 0.9;">Stable</div>
    </div>
    '''
    
    html += '</div>'
    
    # Detailed comparisons
    if regressions > 0:
        html += '<div style="background: rgba(239,68,68,0.1); padding: 20px; border-radius: 8px; margin-bottom: 20px;">'
        html += '<h3 style="color: white; margin-bottom: 15px;">❌ Performance Regressions</h3>'
        html += '<div style="display: grid; gap: 10px;">'
        
        for reg in comparison.get('regressions', []):
            metric_name = reg['metric'].replace('_', ' ').title()
            html += f'''
            <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 6px;">
                <div style="font-weight: bold; margin-bottom: 5px;">{reg['icon']} {metric_name}</div>
                <div style="font-size: 0.9em; opacity: 0.9;">
                    {reg['previous']} → {reg['current']} 
                    <span style="color: #fca5a5; font-weight: bold;">({reg['change_percent']:+.1f}%)</span>
                </div>
            </div>
            '''
        
        html += '</div></div>'
    
    if improvements > 0:
        html += '<div style="background: rgba(16,185,129,0.1); padding: 20px; border-radius: 8px; margin-bottom: 20px;">'
        html += '<h3 style="color: white; margin-bottom: 15px;">✅ Performance Improvements</h3>'
        html += '<div style="display: grid; gap: 10px;">'
        
        for imp in comparison.get('improvements', [])[:5]:  # Show top 5
            metric_name = imp['metric'].replace('_', ' ').title()
            html += f'''
            <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 6px;">
                <div style="font-weight: bold; margin-bottom: 5px;">{imp['icon']} {metric_name}</div>
                <div style="font-size: 0.9em; opacity: 0.9;">
                    {imp['previous']} → {imp['current']} 
                    <span style="color: #86efac; font-weight: bold;">({imp['change_percent']:+.1f}%)</span>
                </div>
            </div>
            '''
        
        html += '</div></div>'
    
    if warnings > 0:
        html += '<div style="background: rgba(245,158,11,0.1); padding: 20px; border-radius: 8px;">'
        html += '<h3 style="color: white; margin-bottom: 15px;">⚠️ Performance Warnings</h3>'
        html += '<div style="display: grid; gap: 10px;">'
        
        for warn in comparison.get('warnings', [])[:3]:  # Show top 3
            metric_name = warn['metric'].replace('_', ' ').title()
            html += f'''
            <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 6px;">
                <div style="font-weight: bold; margin-bottom: 5px;">{warn['icon']} {metric_name}</div>
                <div style="font-size: 0.9em; opacity: 0.9;">
                    {warn['previous']} → {warn['current']} 
                    <span style="color: #fcd34d; font-weight: bold;">({warn['change_percent']:+.1f}%)</span>
                </div>
            </div>
            '''
        
        html += '</div></div>'
    
    html += '</div>'
    return html

def generate_cross_tool_comparison(dd_tests, fio_tests, iozone_tests, bonnie_tests, dbench_tests):
    """
    Generate unified cross-tool comparison view with normalized metrics.
    
    This provides a single view comparing performance across all tools
    with consistent units (MB/s for throughput, IOPS for operations).
    """
    html = '<div class="section"><h2>📊 Cross-Tool Performance Comparison</h2>'
    html += '<p style="color: #666; margin-bottom: 20px;">Unified view of performance metrics across all benchmark tools (normalized to MB/s)</p>'
    
    # Sequential Write Throughput Comparison
    write_data = []
    
    # DD write tests
    for name, data in (dd_tests or {}).items():
        if data.get('status') == 'passed' and 'write' in name.lower():
            write_data.append({
                'tool': 'DD',
                'test': name.replace('_', ' ').title(),
                'throughput_mbps': data.get('throughput_mbps', 0)
            })
    
    # FIO write tests
    for name, data in (fio_tests or {}).items():
        if data.get('status') == 'passed' and data.get('write_bandwidth_mbps', 0) > 0:
            write_data.append({
                'tool': 'FIO',
                'test': name.replace('_', ' ').title(),
                'throughput_mbps': data.get('write_bandwidth_mbps', 0)
            })
    
    # IOzone write tests
    for name, data in (iozone_tests or {}).items():
        if data.get('status') == 'passed' and data.get('write_throughput_mbps', 0) > 0:
            write_data.append({
                'tool': 'IOzone',
                'test': name.replace('_', ' ').title(),
                'throughput_mbps': data.get('write_throughput_mbps', 0)
            })
    
    # Bonnie++ write tests
    for name, data in (bonnie_tests or {}).items():
        if data.get('status') == 'passed' and data.get('sequential_output_block_mbps', 0) > 0:
            write_data.append({
                'tool': 'Bonnie++',
                'test': name.replace('_', ' ').title(),
                'throughput_mbps': data.get('sequential_output_block_mbps', 0)
            })
    
    # DBench tests (general throughput)
    for name, data in (dbench_tests or {}).items():
        if data.get('status') == 'passed' and data.get('throughput_mbps', 0) > 0:
            if name != 'scalability_test':  # Skip scalability for main comparison
                write_data.append({
                    'tool': 'DBench',
                    'test': name.replace('_', ' ').title(),
                    'throughput_mbps': data.get('throughput_mbps', 0)
                })
    
    if write_data:
        html += '<h3>Sequential Write Throughput (MB/s)</h3>'
        html += '<table><thead><tr><th>Tool</th><th>Test</th><th>Throughput (MB/s)</th></tr></thead><tbody>'
        
        # Sort by throughput descending
        write_data.sort(key=lambda x: x['throughput_mbps'], reverse=True)
        
        for item in write_data:
            html += f'<tr><td><strong>{item["tool"]}</strong></td><td>{item["test"]}</td><td>{item["throughput_mbps"]:.2f}</td></tr>'
        
        html += '</tbody></table>'
    
    # Sequential Read Throughput Comparison
    read_data = []
    
    # DD read tests
    for name, data in (dd_tests or {}).items():
        if data.get('status') == 'passed' and 'read' in name.lower():
            read_data.append({
                'tool': 'DD',
                'test': name.replace('_', ' ').title(),
                'throughput_mbps': data.get('throughput_mbps', 0)
            })
    
    # FIO read tests
    for name, data in (fio_tests or {}).items():
        if data.get('status') == 'passed' and data.get('read_bandwidth_mbps', 0) > 0:
            read_data.append({
                'tool': 'FIO',
                'test': name.replace('_', ' ').title(),
                'throughput_mbps': data.get('read_bandwidth_mbps', 0)
            })
    
    # IOzone read tests
    for name, data in (iozone_tests or {}).items():
        if data.get('status') == 'passed' and data.get('read_throughput_mbps', 0) > 0:
            read_data.append({
                'tool': 'IOzone',
                'test': name.replace('_', ' ').title(),
                'throughput_mbps': data.get('read_throughput_mbps', 0)
            })
    
    # Bonnie++ read tests
    for name, data in (bonnie_tests or {}).items():
        if data.get('status') == 'passed' and data.get('sequential_input_block_mbps', 0) > 0:
            read_data.append({
                'tool': 'Bonnie++',
                'test': name.replace('_', ' ').title(),
                'throughput_mbps': data.get('sequential_input_block_mbps', 0)
            })
    
    if read_data:
        html += '<h3 style="margin-top: 30px;">Sequential Read Throughput (MB/s)</h3>'
        html += '<table><thead><tr><th>Tool</th><th>Test</th><th>Throughput (MB/s)</th></tr></thead><tbody>'
        
        # Sort by throughput descending
        read_data.sort(key=lambda x: x['throughput_mbps'], reverse=True)
        
        for item in read_data:
            html += f'<tr><td><strong>{item["tool"]}</strong></td><td>{item["test"]}</td><td>{item["throughput_mbps"]:.2f}</td></tr>'
        
        html += '</tbody></table>'
    
    # IOPS Comparison (FIO only provides this)
    iops_data = []
    
    for name, data in (fio_tests or {}).items():
        if data.get('status') == 'passed':
            if data.get('read_iops', 0) > 0:
                iops_data.append({
                    'tool': 'FIO',
                    'test': name.replace('_', ' ').title(),
                    'operation': 'Read',
                    'iops': data.get('read_iops', 0)
                })
            if data.get('write_iops', 0) > 0:
                iops_data.append({
                    'tool': 'FIO',
                    'test': name.replace('_', ' ').title(),
                    'operation': 'Write',
                    'iops': data.get('write_iops', 0)
                })
    
    if iops_data:
        html += '<h3 style="margin-top: 30px;">IOPS Performance</h3>'
        html += '<table><thead><tr><th>Tool</th><th>Test</th><th>Operation</th><th>IOPS</th></tr></thead><tbody>'
        
        # Sort by IOPS descending
        iops_data.sort(key=lambda x: x['iops'], reverse=True)
        
        for item in iops_data:
            html += f'<tr><td><strong>{item["tool"]}</strong></td><td>{item["test"]}</td><td>{item["operation"]}</td><td>{item["iops"]:.2f}</td></tr>'
        
        html += '</tbody></table>'
    
    # Latency Comparison
    latency_data = []
    
    # FIO latency tests
    for name, data in (fio_tests or {}).items():
        if data.get('status') == 'passed':
            if data.get('read_latency_ms', 0) > 0:
                latency_data.append({
                    'tool': 'FIO',
                    'test': name.replace('_', ' ').title(),
                    'operation': 'Read',
                    'avg_latency_ms': data.get('read_latency_ms', 0),
                    'p99_latency_ms': data.get('read_latency_p99_ms', 0) if 'read_latency_p99_ms' in data else None
                })
            if data.get('write_latency_ms', 0) > 0:
                latency_data.append({
                    'tool': 'FIO',
                    'test': name.replace('_', ' ').title(),
                    'operation': 'Write',
                    'avg_latency_ms': data.get('write_latency_ms', 0),
                    'p99_latency_ms': data.get('write_latency_p99_ms', 0) if 'write_latency_p99_ms' in data else None
                })
    
    # DBench latency tests
    for name, data in (dbench_tests or {}).items():
        if data.get('status') == 'passed' and data.get('avg_latency_ms', 0) > 0:
            latency_data.append({
                'tool': 'DBench',
                'test': name.replace('_', ' ').title(),
                'operation': 'Mixed',
                'avg_latency_ms': data.get('avg_latency_ms', 0),
                'max_latency_ms': data.get('max_latency_ms', 0)
            })
    
    if latency_data:
        html += '<h3 style="margin-top: 30px;">Latency Performance (milliseconds)</h3>'
        html += '<p style="color: #666; font-size: 0.9em; margin-bottom: 10px;">Lower latency = better responsiveness - critical for interactive NFS workloads</p>'
        html += '<table><thead><tr><th>Tool</th><th>Test</th><th>Operation</th><th>Avg Latency (ms)</th><th>P99/Max Latency (ms)</th></tr></thead><tbody>'
        
        # Sort by average latency ascending (lower is better)
        latency_data.sort(key=lambda x: x['avg_latency_ms'])
        
        for item in latency_data:
            p99_max = item.get('p99_latency_ms') or item.get('max_latency_ms', 0)
            p99_max_str = f'{p99_max:.2f}' if p99_max > 0 else '-'
            p99_max_label = 'P99' if 'p99_latency_ms' in item else 'Max'
            
            html += f'<tr><td><strong>{item["tool"]}</strong></td><td>{item["test"]}</td><td>{item["operation"]}</td><td>{item["avg_latency_ms"]:.2f}</td><td>{p99_max_str} ({p99_max_label})</td></tr>'
        
        html += '</tbody></table>'
    
    # Performance Summary
    html += '<h3 style="margin-top: 30px;">Performance Summary</h3>'
    html += '<div class="summary-grid">'
    
    if write_data:
        max_write = max(write_data, key=lambda x: x['throughput_mbps'])
        html += f'''
        <div class="metric-card">
            <h3>Best Write Performance</h3>
            <div class="value">{max_write["throughput_mbps"]:.2f}<span class="unit">MB/s</span></div>
            <p style="font-size: 0.9em; color: #666; margin-top: 10px;">{max_write["tool"]} - {max_write["test"]}</p>
        </div>
        '''
    
    if read_data:
        max_read = max(read_data, key=lambda x: x['throughput_mbps'])
        html += f'''
        <div class="metric-card">
            <h3>Best Read Performance</h3>
            <div class="value">{max_read["throughput_mbps"]:.2f}<span class="unit">MB/s</span></div>
            <p style="font-size: 0.9em; color: #666; margin-top: 10px;">{max_read["tool"]} - {max_read["test"]}</p>
        </div>
        '''
    
    if iops_data:
        max_iops = max(iops_data, key=lambda x: x['iops'])
        html += f'''
        <div class="metric-card">
            <h3>Best IOPS Performance</h3>
            <div class="value">{max_iops["iops"]:.0f}<span class="unit">IOPS</span></div>
            <p style="font-size: 0.9em; color: #666; margin-top: 10px;">{max_iops["tool"]} - {max_iops["test"]} ({max_iops["operation"]})</p>
        </div>
        '''
    
    if latency_data:
        min_latency = min(latency_data, key=lambda x: x['avg_latency_ms'])
        html += f'''
        <div class="metric-card">
            <h3>Best Latency (Lowest)</h3>
            <div class="value">{min_latency["avg_latency_ms"]:.2f}<span class="unit">ms</span></div>
            <p style="font-size: 0.9em; color: #666; margin-top: 10px;">{min_latency["tool"]} - {min_latency["test"]} ({min_latency["operation"]})</p>
        </div>
        '''
    
    html += '</div>'
    
    # Metadata Operations Comparison (File Operations)
    metadata_data = []
    
    # Bonnie++ file operations
    for name, data in (bonnie_tests or {}).items():
        if data.get('status') == 'passed':
            # Sequential file operations
            if data.get('file_create_seq_per_sec', 0) > 0:
                metadata_data.append({
                    'tool': 'Bonnie++',
                    'test': name.replace('_', ' ').title(),
                    'operation': 'Create (Sequential)',
                    'ops_per_sec': data.get('file_create_seq_per_sec', 0)
                })
            if data.get('file_delete_seq_per_sec', 0) > 0:
                metadata_data.append({
                    'tool': 'Bonnie++',
                    'test': name.replace('_', ' ').title(),
                    'operation': 'Delete (Sequential)',
                    'ops_per_sec': data.get('file_delete_seq_per_sec', 0)
                })
            # Random file operations
            if data.get('file_create_random_per_sec', 0) > 0:
                metadata_data.append({
                    'tool': 'Bonnie++',
                    'test': name.replace('_', ' ').title(),
                    'operation': 'Create (Random)',
                    'ops_per_sec': data.get('file_create_random_per_sec', 0)
                })
            if data.get('file_delete_random_per_sec', 0) > 0:
                metadata_data.append({
                    'tool': 'Bonnie++',
                    'test': name.replace('_', ' ').title(),
                    'operation': 'Delete (Random)',
                    'ops_per_sec': data.get('file_delete_random_per_sec', 0)
                })
    
    # FIO metadata operations
    for name, data in (fio_tests or {}).items():
        if data.get('status') == 'passed' and 'metadata' in name.lower():
            if data.get('write_iops', 0) > 0:
                metadata_data.append({
                    'tool': 'FIO',
                    'test': name.replace('_', ' ').title(),
                    'operation': 'File Operations',
                    'ops_per_sec': data.get('write_iops', 0)
                })
    
    # DBench operations (general workload includes metadata)
    for name, data in (dbench_tests or {}).items():
        if data.get('status') == 'passed' and 'metadata' in name.lower():
            if data.get('operations_per_sec', 0) > 0:
                metadata_data.append({
                    'tool': 'DBench',
                    'test': name.replace('_', ' ').title(),
                    'operation': 'Mixed Operations',
                    'ops_per_sec': data.get('operations_per_sec', 0)
                })
    
    if metadata_data:
        html += '<h3 style="margin-top: 30px;">Metadata Operations Performance (Files/sec)</h3>'
        html += '<p style="color: #666; font-size: 0.9em; margin-bottom: 10px;">File creation, deletion, and stat operations - critical for NFS metadata performance</p>'
        html += '<table><thead><tr><th>Tool</th><th>Test</th><th>Operation</th><th>Operations/sec</th></tr></thead><tbody>'
        
        # Sort by ops/sec descending
        metadata_data.sort(key=lambda x: x['ops_per_sec'], reverse=True)
        
        for item in metadata_data:
            html += f'<tr><td><strong>{item["tool"]}</strong></td><td>{item["test"]}</td><td>{item["operation"]}</td><td>{item["ops_per_sec"]:.2f}</td></tr>'
        
        html += '</tbody></table>'
    
    # Multi-Threading / Scalability Comparison
    scaling_data = []
    
    # IOzone scaling test
    for name, data in (iozone_tests or {}).items():
        if data.get('status') == 'passed' and name == 'scaling_test':
            scaling_results = data.get('scaling_results', {})
            for thread_name, thread_data in scaling_results.items():
                # Extract thread count from name like "4_threads"
                thread_count = thread_name.split('_')[0] if '_' in thread_name else thread_name
                scaling_data.append({
                    'tool': 'IOzone',
                    'threads': thread_count,
                    'read_mbps': thread_data.get('read_throughput_mbps', 0),
                    'write_mbps': thread_data.get('write_throughput_mbps', 0)
                })
    
    # DBench scalability test
    for name, data in (dbench_tests or {}).items():
        if data.get('status') == 'passed' and name == 'scalability_test':
            client_results = data.get('client_results', [])
            for client_data in client_results:
                num_clients = client_data.get('num_clients', 0)
                scaling_data.append({
                    'tool': 'DBench',
                    'threads': str(num_clients),
                    'throughput_mbps': client_data.get('throughput_mbps', 0),
                    'ops_per_sec': client_data.get('operations_per_sec', 0)
                })
    
    if scaling_data:
        html += '<h3 style="margin-top: 30px;">Multi-Threading / Scalability Performance</h3>'
        html += '<p style="color: #666; font-size: 0.9em; margin-bottom: 10px;">Performance scaling with concurrent threads/clients - tests parallel workload handling</p>'
        html += '<table><thead><tr><th>Tool</th><th>Threads/Clients</th><th>Read (MB/s)</th><th>Write (MB/s)</th><th>Throughput (MB/s)</th><th>Operations/sec</th></tr></thead><tbody>'
        
        for item in scaling_data:
            read_val = item.get('read_mbps', 0)
            write_val = item.get('write_mbps', 0)
            throughput_val = item.get('throughput_mbps', 0)
            ops_val = item.get('ops_per_sec', 0)
            
            read_str = f'{read_val:.2f}' if read_val > 0 else '-'
            write_str = f'{write_val:.2f}' if write_val > 0 else '-'
            throughput_str = f'{throughput_val:.2f}' if throughput_val > 0 else '-'
            ops_str = f'{ops_val:.2f}' if ops_val > 0 else '-'
            
            html += f'<tr><td><strong>{item["tool"]}</strong></td><td>{item["threads"]}</td><td>{read_str}</td><td>{write_str}</td><td>{throughput_str}</td><td>{ops_str}</td></tr>'
        
        html += '</tbody></table>'
    
    html += '</div>'
    html += '</div>'
    
    return html


def generate_charts(dd_tests, fio_tests, iozone_tests=None, bonnie_tests=None, dbench_tests=None):
    """Generate interactive charts using Plotly"""
    if not PLOTLY_AVAILABLE:
        return ""
    
    charts_html = '<div class="section"><h2>Performance Charts</h2>'
    
    # DD Tests Throughput Chart
    if dd_tests:
        dd_names = []
        dd_throughputs = []
        
        for name, data in dd_tests.items():
            if data.get('status') == 'passed':
                dd_names.append(name.replace('_', ' ').title())
                dd_throughputs.append(data.get('throughput_mbps', 0))
        
        if dd_names:
            fig = go.Figure(data=[
                go.Bar(x=dd_names, y=dd_throughputs, marker_color='#667eea')
            ])
            fig.update_layout(
                title='DD Test Throughput',
                xaxis_title='Test Name',
                yaxis_title='Throughput (MB/s)',
                height=400
            )
            charts_html += f'<div class="chart-container">{fig.to_html(include_plotlyjs="cdn", full_html=False)}</div>'
    
    # FIO Tests IOPS Chart
    if fio_tests:
        fio_names = []
        read_iops = []
        write_iops = []
        
        for name, data in fio_tests.items():
            if data.get('status') == 'passed':
                fio_names.append(name.replace('_', ' ').title())
                read_iops.append(data.get('read_iops', 0))
                write_iops.append(data.get('write_iops', 0))
        
        if fio_names:
            fig = go.Figure(data=[
                go.Bar(name='Read IOPS', x=fio_names, y=read_iops, marker_color='#10b981'),
                go.Bar(name='Write IOPS', x=fio_names, y=write_iops, marker_color='#ef4444')
            ])
            fig.update_layout(
                title='FIO Test IOPS',
                xaxis_title='Test Name',
                yaxis_title='IOPS',
                barmode='group',
                height=400
            )
            charts_html += f'<div class="chart-container">{fig.to_html(include_plotlyjs="cdn", full_html=False)}</div>'
    
    # IOzone Tests Throughput Chart
    if iozone_tests:
        iozone_names = []
        read_throughputs = []
        write_throughputs = []
        
        for name, data in iozone_tests.items():
            if data.get('status') == 'passed':
                # Handle scaling test separately
                if name == 'scaling_test':
                    scaling_data = data.get('scaling_results', {})
                    for thread_name, thread_data in scaling_data.items():
                        iozone_names.append(f"Scaling {thread_name}")
                        read_throughputs.append(thread_data.get('read_throughput_mbps', 0))
                        write_throughputs.append(thread_data.get('write_throughput_mbps', 0))
                else:
                    iozone_names.append(name.replace('_', ' ').title())
                    read_throughputs.append(data.get('read_throughput_mbps', 0))
                    write_throughputs.append(data.get('write_throughput_mbps', 0))
        
        if iozone_names:
            fig = go.Figure(data=[
                go.Bar(name='Read', x=iozone_names, y=read_throughputs, marker_color='#10b981'),
                go.Bar(name='Write', x=iozone_names, y=write_throughputs, marker_color='#3b82f6')
            ])
            fig.update_layout(
                title='IOzone Test Throughput',
                xaxis_title='Test Name',
                yaxis_title='Throughput (MB/s)',
                barmode='group',
                height=400
            )
            charts_html += f'<div class="chart-container">{fig.to_html(include_plotlyjs="cdn", full_html=False)}</div>'
    
    # Bonnie++ Tests Throughput Chart
    if bonnie_tests:
        bonnie_names = []
        output_throughputs = []
        input_throughputs = []
        
        for name, data in bonnie_tests.items():
            if data.get('status') == 'passed':
                bonnie_names.append(name.replace('_', ' ').title())
                output_throughputs.append(data.get('sequential_output_block_mbps', 0))
                input_throughputs.append(data.get('sequential_input_block_mbps', 0))
        
        if bonnie_names:
            fig = go.Figure(data=[
                go.Bar(name='Output', x=bonnie_names, y=output_throughputs, marker_color='#f59e0b'),
                go.Bar(name='Input', x=bonnie_names, y=input_throughputs, marker_color='#8b5cf6')
            ])
            fig.update_layout(
                title='Bonnie++ Test Throughput',
                xaxis_title='Test Name',
                yaxis_title='Throughput (MB/s)',
                barmode='group',
                height=400
            )
            charts_html += f'<div class="chart-container">{fig.to_html(include_plotlyjs="cdn", full_html=False)}</div>'
        
        # Bonnie++ File Operations Chart
        file_create_seq = []
        file_delete_seq = []
        file_names = []
        
        for name, data in bonnie_tests.items():
            if data.get('status') == 'passed' and 'file_create_seq_per_sec' in data:
                file_names.append(name.replace('_', ' ').title())
                file_create_seq.append(data.get('file_create_seq_per_sec', 0))
                file_delete_seq.append(data.get('file_delete_seq_per_sec', 0))
        
        if file_names:
            fig = go.Figure(data=[
                go.Bar(name='Create', x=file_names, y=file_create_seq, marker_color='#10b981'),
                go.Bar(name='Delete', x=file_names, y=file_delete_seq, marker_color='#ef4444')
            ])
            fig.update_layout(
                title='Bonnie++ File Operations',
                xaxis_title='Test Name',
                yaxis_title='Operations (files/sec)',
                barmode='group',
                height=400
            )
            charts_html += f'<div class="chart-container">{fig.to_html(include_plotlyjs="cdn", full_html=False)}</div>'
    
    # DBench Tests Charts
    if dbench_tests:
        # Throughput vs Clients Chart
        dbench_names = []
        throughputs = []
        
        for name, data in dbench_tests.items():
            if data.get('status') == 'passed':
                # Handle scalability test specially
                if name == 'scalability_test' and 'client_results' in data:
                    for client_data in data['client_results']:
                        num_clients = client_data.get('num_clients', 0)
                        dbench_names.append(f"{num_clients} clients")
                        throughputs.append(client_data.get('throughput_mbps', 0))
                else:
                    dbench_names.append(name.replace('_', ' ').title())
                    throughputs.append(data.get('throughput_mbps', 0))
        
        if dbench_names:
            fig = go.Figure(data=[
                go.Bar(x=dbench_names, y=throughputs, marker_color='#ec4899')
            ])
            fig.update_layout(
                title='DBench Test Throughput',
                xaxis_title='Test Name',
                yaxis_title='Throughput (MB/s)',
                height=400
            )
            charts_html += f'<div class="chart-container">{fig.to_html(include_plotlyjs="cdn", full_html=False)}</div>'
        
        # Operations per Second Chart
        ops_names = []
        ops_per_sec = []
        
        for name, data in dbench_tests.items():
            if data.get('status') == 'passed' and 'operations_per_sec' in data:
                if name == 'scalability_test' and 'client_results' in data:
                    for client_data in data['client_results']:
                        num_clients = client_data.get('num_clients', 0)
                        ops_names.append(f"{num_clients} clients")
                        ops_per_sec.append(client_data.get('operations_per_sec', 0))
                else:
                    ops_names.append(name.replace('_', ' ').title())
                    ops_per_sec.append(data.get('operations_per_sec', 0))
        
        if ops_names:
            fig = go.Figure(data=[
                go.Bar(x=ops_names, y=ops_per_sec, marker_color='#06b6d4')
            ])
            fig.update_layout(
                title='DBench Operations per Second',
                xaxis_title='Test Name',
                yaxis_title='Operations/sec',
                height=400
            )
            charts_html += f'<div class="chart-container">{fig.to_html(include_plotlyjs="cdn", full_html=False)}</div>'
        
        # Latency Chart
        latency_names = []
        avg_latencies = []
        max_latencies = []
        
        for name, data in dbench_tests.items():
            if data.get('status') == 'passed' and 'avg_latency_ms' in data:
                if name != 'scalability_test':  # Skip scalability for latency chart
                    latency_names.append(name.replace('_', ' ').title())
                    avg_latencies.append(data.get('avg_latency_ms', 0))
                    max_latencies.append(data.get('max_latency_ms', 0))
        
        if latency_names:
            fig = go.Figure(data=[
                go.Bar(name='Average', x=latency_names, y=avg_latencies, marker_color='#10b981'),
                go.Bar(name='Maximum', x=latency_names, y=max_latencies, marker_color='#ef4444')
            ])
            fig.update_layout(
                title='DBench Latency',
                xaxis_title='Test Name',
                yaxis_title='Latency (ms)',
                barmode='group',
                height=400
            )
            charts_html += f'<div class="chart-container">{fig.to_html(include_plotlyjs="cdn", full_html=False)}</div>'
    
    charts_html += '</div>'
    return charts_html


def generate_dd_tests_html(dd_tests):
    """Generate HTML for DD test results"""
    if not dd_tests:
        return "<p>No DD tests were run.</p>"
    
    html = ""
    for name, data in dd_tests.items():
        status = data.get('status', 'unknown')
        status_class = 'passed' if status == 'passed' else 'failed'
        
        html += f'<div class="test-result {status_class}">'
        html += f'<h4>{name.replace("_", " ").title()} <span class="status-badge {status_class}">{status}</span></h4>'
        
        if status == 'passed':
            html += '<div class="test-metrics">'
            html += f'<div class="test-metric"><span class="label">Throughput:</span><span class="value">{data.get("throughput_mbps", 0):.2f} MB/s</span></div>'
            html += f'<div class="test-metric"><span class="label">Duration:</span><span class="value">{data.get("duration_seconds", 0):.2f} s</span></div>'
            html += f'<div class="test-metric"><span class="label">Size:</span><span class="value">{data.get("size_mb", 0)} MB</span></div>'
            html += f'<div class="test-metric"><span class="label">Block Size:</span><span class="value">{data.get("block_size", "N/A")}</span></div>'
            
            # Add system metrics if available
            if 'system_metrics' in data:
                metrics = data['system_metrics']
                if 'cpu' in metrics:
                    html += f'<div class="test-metric"><span class="label">Avg CPU:</span><span class="value">{metrics["cpu"]["avg_percent"]:.1f}%</span></div>'
                if 'memory' in metrics:
                    html += f'<div class="test-metric"><span class="label">Avg Memory:</span><span class="value">{metrics["memory"]["avg_percent"]:.1f}%</span></div>'
            
            html += '</div>'
        else:
            html += f'<p style="color: #ef4444;">Error: {data.get("error", "Unknown error")}</p>'
        
        html += '</div>'
    
    return html


def generate_fio_tests_html(fio_tests):
    """Generate HTML for FIO test results"""
    if not fio_tests:
        return "<p>No FIO tests were run.</p>"
    
    html = ""
    for name, data in fio_tests.items():
        status = data.get('status', 'unknown')
        status_class = 'passed' if status == 'passed' else 'failed'
        
        html += f'<div class="test-result {status_class}">'
        html += f'<h4>{name.replace("_", " ").title()} <span class="status-badge {status_class}">{status}</span></h4>'
        
        if status == 'passed':
            html += '<div class="test-metrics">'
            html += f'<div class="test-metric"><span class="label">Read IOPS:</span><span class="value">{data.get("read_iops", 0):.2f}</span></div>'
            html += f'<div class="test-metric"><span class="label">Write IOPS:</span><span class="value">{data.get("write_iops", 0):.2f}</span></div>'
            html += f'<div class="test-metric"><span class="label">Read BW:</span><span class="value">{data.get("read_bandwidth_mbps", 0):.2f} MB/s</span></div>'
            html += f'<div class="test-metric"><span class="label">Write BW:</span><span class="value">{data.get("write_bandwidth_mbps", 0):.2f} MB/s</span></div>'
            html += f'<div class="test-metric"><span class="label">Read Latency:</span><span class="value">{data.get("read_latency_ms", 0):.2f} ms</span></div>'
            html += f'<div class="test-metric"><span class="label">Write Latency:</span><span class="value">{data.get("write_latency_ms", 0):.2f} ms</span></div>'
            
            # Add system metrics if available
            if 'system_metrics' in data:
                metrics = data['system_metrics']
                if 'cpu' in metrics:
                    html += f'<div class="test-metric"><span class="label">Avg CPU:</span><span class="value">{metrics["cpu"]["avg_percent"]:.1f}%</span></div>'
                if 'memory' in metrics:
                    html += f'<div class="test-metric"><span class="label">Avg Memory:</span><span class="value">{metrics["memory"]["avg_percent"]:.1f}%</span></div>'
            
            html += '</div>'
        else:
            html += f'<p style="color: #ef4444;">Error: {data.get("error", "Unknown error")}</p>'
        
        html += '</div>'
    
    return html


def generate_iozone_tests_html(iozone_tests):
    """Generate HTML for IOzone test results"""
    if not iozone_tests:
        return "<p>No IOzone tests were run.</p>"
    
    html = ""
    for name, data in iozone_tests.items():
        status = data.get('status', 'unknown')
        status_class = 'passed' if status == 'passed' else 'failed'
        
        html += f'<div class="test-result {status_class}">'
        html += f'<h4>{name.replace("_", " ").title()} <span class="status-badge {status_class}">{status}</span></h4>'
        
        if status == 'passed':
            html += '<div class="test-metrics">'
            
            # Handle scaling test specially
            if name == 'scaling_test':
                scaling_results = data.get('scaling_results', {})
                for thread_name, thread_data in scaling_results.items():
                    html += f'<div class="test-metric"><span class="label">{thread_name} Read:</span><span class="value">{thread_data.get("read_throughput_mbps", 0):.2f} MB/s</span></div>'
                    html += f'<div class="test-metric"><span class="label">{thread_name} Write:</span><span class="value">{thread_data.get("write_throughput_mbps", 0):.2f} MB/s</span></div>'
            else:
                # Regular test metrics
                if 'read_throughput_mbps' in data:
                    html += f'<div class="test-metric"><span class="label">Read Throughput:</span><span class="value">{data.get("read_throughput_mbps", 0):.2f} MB/s</span></div>'
                if 'write_throughput_mbps' in data:
                    html += f'<div class="test-metric"><span class="label">Write Throughput:</span><span class="value">{data.get("write_throughput_mbps", 0):.2f} MB/s</span></div>'
                if 'random_read_throughput_mbps' in data:
                    html += f'<div class="test-metric"><span class="label">Random Read:</span><span class="value">{data.get("random_read_throughput_mbps", 0):.2f} MB/s</span></div>'
                if 'random_write_throughput_mbps' in data:
                    html += f'<div class="test-metric"><span class="label">Random Write:</span><span class="value">{data.get("random_write_throughput_mbps", 0):.2f} MB/s</span></div>'
                
                html += f'<div class="test-metric"><span class="label">Duration:</span><span class="value">{data.get("duration_seconds", 0):.2f} s</span></div>'
                
                # Configuration details
                config = data.get('config', {})
                if config:
                    html += f'<div class="test-metric"><span class="label">File Size:</span><span class="value">{config.get("file_size", "N/A")}</span></div>'
                    html += f'<div class="test-metric"><span class="label">Record Size:</span><span class="value">{config.get("record_size", "N/A")}</span></div>'
                    if config.get('threads', 1) > 1:
                        html += f'<div class="test-metric"><span class="label">Threads:</span><span class="value">{config.get("threads", 1)}</span></div>'
                
                # Add system metrics if available
                if 'system_metrics' in data:
                    metrics = data['system_metrics']
                    if 'cpu' in metrics:
                        html += f'<div class="test-metric"><span class="label">Avg CPU:</span><span class="value">{metrics["cpu"]["avg_percent"]:.1f}%</span></div>'
                    if 'memory' in metrics:
                        html += f'<div class="test-metric"><span class="label">Avg Memory:</span><span class="value">{metrics["memory"]["avg_percent"]:.1f}%</span></div>'
            
            html += '</div>'
        else:
            html += f'<p style="color: #ef4444;">Error: {data.get("error", "Unknown error")}</p>'
        
        html += '</div>'
    
    return html


def generate_nfs_stats_html(nfs_stats):
    """Generate HTML for NFS statistics"""
    if not nfs_stats:
        return ""
    
    html = '<div class="section"><h2>NFS Statistics</h2>'
    
    before = nfs_stats.get('before_tests', {})
    after = nfs_stats.get('after_tests', {})
    
    if before:
        html += f'<h3>NFS Version: {before.get("nfs_version", "Unknown")}</h3>'
    
    if before.get('operations') or after.get('operations'):
        html += '<h3>Operation Counts</h3>'
        html += '<table><thead><tr><th>Operation</th><th>Before Tests</th><th>After Tests</th><th>Delta</th></tr></thead><tbody>'
        
        all_ops = set(before.get('operations', {}).keys()) | set(after.get('operations', {}).keys())
        for op in sorted(all_ops):
            before_count = before.get('operations', {}).get(op, 0)
            after_count = after.get('operations', {}).get(op, 0)
            delta = after_count - before_count
            html += f'<tr><td>{op}</td><td>{before_count}</td><td>{after_count}</td><td>{delta}</td></tr>'
        
        html += '</tbody></table>'
    
    # Add NFS metrics summary (from NFSMetricsCollector)
    if 'rates' in nfs_stats or 'deltas' in nfs_stats or 'issues' in nfs_stats:
        html += '<h3>NFS Performance Metrics</h3>'
        
        # RPC Statistics
        rates = nfs_stats.get('rates', {})
        rpc_rates = rates.get('rpc', {})
        if rpc_rates:
            html += '<h4>RPC Statistics</h4>'
            html += '<table><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>'
            
            if 'calls_per_sec' in rpc_rates:
                html += f'<tr><td>RPC Calls/sec</td><td>{rpc_rates["calls_per_sec"]:.2f}</td></tr>'
            if 'retrans_percent' in rpc_rates:
                retrans_pct = rpc_rates['retrans_percent']
                status_class = 'critical' if retrans_pct > 5 else ('warning' if retrans_pct > 1 else 'success')
                html += f'<tr class="{status_class}"><td>Retransmission Rate</td><td>{retrans_pct:.2f}%</td></tr>'
            if 'retransmissions_per_sec' in rpc_rates:
                html += f'<tr><td>Retransmissions/sec</td><td>{rpc_rates["retransmissions_per_sec"]:.2f}</td></tr>'
            
            html += '</tbody></table>'
        
        # Transport (xprt) Statistics
        xprt_rates = rates.get('xprt', {})
        if xprt_rates:
            html += '<h4>Transport (xprt) Statistics</h4>'
            html += '<table><thead><tr><th>Metric</th><th>Value</th><th>Status</th></tr></thead><tbody>'
            
            # Protocol
            if 'protocol' in xprt_rates:
                html += f'<tr><td>Protocol</td><td>{xprt_rates["protocol"].upper()}</td><td>-</td></tr>'
            
            # Connection stats
            if 'connects_per_sec' in xprt_rates:
                connects = xprt_rates['connects_per_sec']
                status = '✓ Good' if connects == 0 else ('⚠ Warning' if connects < 1 else '✗ Poor')
                status_class = 'success' if connects == 0 else ('warning' if connects < 1 else 'critical')
                html += f'<tr class="{status_class}"><td>Connections/sec</td><td>{connects:.2f}</td><td>{status}</td></tr>'
            
            # Send/Receive rates
            if 'sends_per_sec' in xprt_rates:
                html += f'<tr><td>Sends/sec</td><td>{xprt_rates["sends_per_sec"]:.2f}</td><td>-</td></tr>'
            if 'recvs_per_sec' in xprt_rates:
                html += f'<tr><td>Receives/sec</td><td>{xprt_rates["recvs_per_sec"]:.2f}</td><td>-</td></tr>'
            
            # Bad XIDs
            if 'bad_xids_per_sec' in xprt_rates:
                bad_xids = xprt_rates['bad_xids_per_sec']
                status = '✓ Good' if bad_xids == 0 else '✗ Critical'
                status_class = 'success' if bad_xids == 0 else 'critical'
                html += f'<tr class="{status_class}"><td>Bad XIDs/sec</td><td>{bad_xids:.2f}</td><td>{status}</td></tr>'
            
            # Queue times
            if 'avg_req_queue_time_us' in xprt_rates:
                req_time = xprt_rates['avg_req_queue_time_us']
                status = '✓ Good' if req_time < 100 else ('⚠ Warning' if req_time < 1000 else '✗ Poor')
                status_class = 'success' if req_time < 100 else ('warning' if req_time < 1000 else 'critical')
                html += f'<tr class="{status_class}"><td>Avg Request Queue Time</td><td>{req_time:.2f} μs</td><td>{status}</td></tr>'
            
            if 'avg_resp_queue_time_us' in xprt_rates:
                resp_time = xprt_rates['avg_resp_queue_time_us']
                status = '✓ Good' if resp_time < 100 else ('⚠ Warning' if resp_time < 1000 else '✗ Poor')
                status_class = 'success' if resp_time < 100 else ('warning' if resp_time < 1000 else 'critical')
                html += f'<tr class="{status_class}"><td>Avg Response Queue Time</td><td>{resp_time:.2f} μs</td><td>{status}</td></tr>'
            
            # Queue depths
            if 'sending_queue' in xprt_rates:
                sending_q = xprt_rates['sending_queue']
                status = '✓ Good' if sending_q <= 2 else ('⚠ Warning' if sending_q <= 10 else '✗ High')
                status_class = 'success' if sending_q <= 2 else ('warning' if sending_q <= 10 else 'critical')
                html += f'<tr class="{status_class}"><td>Sending Queue Depth</td><td>{sending_q}</td><td>{status}</td></tr>'
            
            if 'pending_queue' in xprt_rates:
                pending_q = xprt_rates['pending_queue']
                status = '✓ Good' if pending_q <= 5 else ('⚠ Warning' if pending_q <= 10 else '✗ High')
                status_class = 'success' if pending_q <= 5 else ('warning' if pending_q <= 10 else 'critical')
                html += f'<tr class="{status_class}"><td>Pending Queue Depth</td><td>{pending_q}</td><td>{status}</td></tr>'
            
            if 'max_slots' in xprt_rates:
                html += f'<tr><td>Max Slots</td><td>{xprt_rates["max_slots"]}</td><td>-</td></tr>'
            
            html += '</tbody></table>'
        
        # Throughput Statistics
        throughput_rates = rates.get('throughput', {})
        if throughput_rates:
            html += '<h4>Throughput Statistics</h4>'
            html += '<table><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>'
            
            if 'read_mbps' in throughput_rates:
                html += f'<tr><td>Read Throughput</td><td>{throughput_rates["read_mbps"]:.2f} MB/s</td></tr>'
            if 'write_mbps' in throughput_rates:
                html += f'<tr><td>Write Throughput</td><td>{throughput_rates["write_mbps"]:.2f} MB/s</td></tr>'
            if 'read_iops' in throughput_rates:
                html += f'<tr><td>Read IOPS</td><td>{throughput_rates["read_iops"]:.2f}</td></tr>'
            if 'write_iops' in throughput_rates:
                html += f'<tr><td>Write IOPS</td><td>{throughput_rates["write_iops"]:.2f}</td></tr>'
            
            html += '</tbody></table>'
        
        # Issues
        issues = nfs_stats.get('issues', [])
        if issues:
            html += '<h4>Detected Issues</h4>'
            html += '<table><thead><tr><th>Severity</th><th>Category</th><th>Message</th><th>Impact</th></tr></thead><tbody>'
            
            for issue in issues:
                severity = issue.get('severity', 'unknown')
                category = issue.get('category', 'unknown')
                message = issue.get('message', '')
                impact = issue.get('impact', '')
                
                severity_class = 'critical' if severity == 'critical' else 'warning'
                severity_icon = '✗' if severity == 'critical' else '⚠'
                
                html += f'<tr class="{severity_class}">'
                html += f'<td>{severity_icon} {severity.upper()}</td>'
                html += f'<td>{category}</td>'
                html += f'<td>{message}</td>'
                html += f'<td>{impact}</td>'
                html += '</tr>'
            
            html += '</tbody></table>'
        
        # Per-Operation Timing Statistics
        per_op_stats = nfs_stats.get('deltas', {}).get('per_op_stats', {})
        if per_op_stats:
            html += '<h4>Per-Operation Timing Analysis</h4>'
            html += '<p style="font-size: 0.9em; color: #666;">Breakdown of where time is spent for each NFS operation (Queue = client wait, RTT = network, Execute = server processing)</p>'
            html += '<table><thead><tr>'
            html += '<th>Operation</th><th>Count</th><th>Avg Queue (ms)</th><th>Avg RTT (ms)</th>'
            html += '<th>Avg Execute (ms)</th><th>Avg Total (ms)</th><th>Errors</th><th>Timeouts</th><th>Bottleneck</th>'
            html += '</tr></thead><tbody>'
            
            # Sort by total latency descending
            sorted_ops = sorted(per_op_stats.items(),
                              key=lambda x: x[1].get('avg_total_latency_ms', 0),
                              reverse=True)
            
            for op_name, op_data in sorted_ops:
                ops_count = op_data.get('ops', 0)
                avg_queue = op_data.get('avg_queue_ms', 0)
                avg_rtt = op_data.get('avg_rtt_ms', 0)
                avg_exe = op_data.get('avg_exe_ms', 0)
                avg_total = op_data.get('avg_total_latency_ms', 0)
                errors = op_data.get('errors', 0)
                timeouts = op_data.get('timeouts', 0)
                
                # Determine bottleneck
                max_component = max(avg_queue, avg_rtt, avg_exe)
                if max_component == avg_queue:
                    bottleneck = "Client Queue"
                    bottleneck_class = "warning"
                elif max_component == avg_rtt:
                    bottleneck = "Network RTT"
                    bottleneck_class = "warning"
                else:
                    bottleneck = "Server Exec"
                    bottleneck_class = "warning"
                
                # Determine row class based on total latency
                if avg_total > 100:
                    row_class = "critical"
                elif avg_total > 50:
                    row_class = "warning"
                else:
                    row_class = "success"
                
                # Override if errors or timeouts
                if errors > 0 or timeouts > 0:
                    row_class = "critical"
                
                html += f'<tr class="{row_class}">'
                html += f'<td><strong>{op_name}</strong></td>'
                html += f'<td>{ops_count}</td>'
                html += f'<td>{avg_queue:.2f}</td>'
                html += f'<td>{avg_rtt:.2f}</td>'
                html += f'<td>{avg_exe:.2f}</td>'
                html += f'<td><strong>{avg_total:.2f}</strong></td>'
                html += f'<td>{errors if errors > 0 else "-"}</td>'
                html += f'<td>{timeouts if timeouts > 0 else "-"}</td>'
                html += f'<td class="{bottleneck_class}">{bottleneck}</td>'
                html += '</tr>'
            
            html += '</tbody></table>'
            
            # Add legend
            html += '<div style="margin-top: 10px; font-size: 0.85em; color: #666;">'
            html += '<p><strong>Bottleneck Identification:</strong></p>'
            html += '<ul style="margin: 5px 0; padding-left: 20px;">'
            html += '<li><strong>Client Queue</strong>: High queue time means client cannot send requests fast enough (CPU/network send buffer issue)</li>'
            html += '<li><strong>Network RTT</strong>: High RTT means network latency is the problem (check network path, reduce hops)</li>'
            html += '<li><strong>Server Exec</strong>: High execution time means server is slow (overloaded server or slow storage)</li>'
            html += '</ul>'
            html += '</div>'
    
    html += '</div>'
    return html


def generate_bonnie_tests_html(bonnie_tests):
    """Generate HTML for Bonnie++ test results"""
    if not bonnie_tests:
        return "<p>No Bonnie++ tests were run.</p>"
    
    html = ""
    for name, data in bonnie_tests.items():
        status = data.get('status', 'unknown')
        status_class = 'passed' if status == 'passed' else 'failed'
        
        html += f'<div class="test-result {status_class}">'
        html += f'<h4>{name.replace("_", " ").title()} <span class="status-badge {status_class}">{status}</span></h4>'
        
        if status == 'passed':
            html += '<div class="test-metrics">'
            
            # Sequential output metrics
            if 'sequential_output_block_mbps' in data:
                html += f'<div class="test-metric"><span class="label">Sequential Output (Block):</span><span class="value">{data["sequential_output_block_mbps"]:.2f} MB/s</span></div>'
            if 'sequential_rewrite_mbps' in data:
                html += f'<div class="test-metric"><span class="label">Sequential Rewrite:</span><span class="value">{data["sequential_rewrite_mbps"]:.2f} MB/s</span></div>'
            
            # Sequential input metrics
            if 'sequential_input_block_mbps' in data:
                html += f'<div class="test-metric"><span class="label">Sequential Input (Block):</span><span class="value">{data["sequential_input_block_mbps"]:.2f} MB/s</span></div>'
            
            # Character I/O metrics (if available)
            if 'sequential_output_char_mbps' in data:
                html += f'<div class="test-metric"><span class="label">Sequential Output (Char):</span><span class="value">{data["sequential_output_char_mbps"]:.2f} MB/s</span></div>'
            if 'sequential_input_char_mbps' in data:
                html += f'<div class="test-metric"><span class="label">Sequential Input (Char):</span><span class="value">{data["sequential_input_char_mbps"]:.2f} MB/s</span></div>'
            
            # Random seeks
            if 'random_seeks_per_sec' in data:
                html += f'<div class="test-metric"><span class="label">Random Seeks:</span><span class="value">{data["random_seeks_per_sec"]:.2f} seeks/sec</span></div>'
            
            # File operations - sequential
            if 'file_create_seq_per_sec' in data:
                html += f'<div class="test-metric"><span class="label">File Create (Seq):</span><span class="value">{data["file_create_seq_per_sec"]:.2f} files/sec</span></div>'
            if 'file_stat_seq_per_sec' in data:
                html += f'<div class="test-metric"><span class="label">File Stat (Seq):</span><span class="value">{data["file_stat_seq_per_sec"]:.2f} files/sec</span></div>'
            if 'file_delete_seq_per_sec' in data:
                html += f'<div class="test-metric"><span class="label">File Delete (Seq):</span><span class="value">{data["file_delete_seq_per_sec"]:.2f} files/sec</span></div>'
            
            # File operations - random
            if 'file_create_random_per_sec' in data:
                html += f'<div class="test-metric"><span class="label">File Create (Random):</span><span class="value">{data["file_create_random_per_sec"]:.2f} files/sec</span></div>'
            if 'file_stat_random_per_sec' in data:
                html += f'<div class="test-metric"><span class="label">File Stat (Random):</span><span class="value">{data["file_stat_random_per_sec"]:.2f} files/sec</span></div>'
            if 'file_delete_random_per_sec' in data:
                html += f'<div class="test-metric"><span class="label">File Delete (Random):</span><span class="value">{data["file_delete_random_per_sec"]:.2f} files/sec</span></div>'
            
            html += f'<div class="test-metric"><span class="label">Duration:</span><span class="value">{data.get("duration_seconds", 0):.2f} s</span></div>'
            
            # Add system metrics if available
            if 'system_metrics' in data:
                metrics = data['system_metrics']
                if 'cpu' in metrics:
                    html += f'<div class="test-metric"><span class="label">Avg CPU:</span><span class="value">{metrics["cpu"]["avg_percent"]:.1f}%</span></div>'
                if 'memory' in metrics:
                    html += f'<div class="test-metric"><span class="label">Avg Memory:</span><span class="value">{metrics["memory"]["avg_percent"]:.1f}%</span></div>'
            
            html += '</div>'
        else:
            html += f'<p style="color: #ef4444;">Error: {data.get("error", "Unknown error")}</p>'
        
        html += '</div>'
    
    return html


def generate_dbench_tests_html(dbench_tests):
    """Generate HTML for DBench test results"""
    if not dbench_tests:
        return "<p>No DBench tests were run.</p>"
    
    html = ""
    for name, data in dbench_tests.items():
        status = data.get('status', 'unknown')
        status_class = 'passed' if status == 'passed' else 'failed'
        
        html += f'<div class="test-result {status_class}">'
        html += f'<h4>{name.replace("_", " ").title()} <span class="status-badge {status_class}">{status}</span></h4>'
        
        if status == 'passed':
            html += '<div class="test-metrics">'
            
            # Handle scalability test specially
            if name == 'scalability_test' and 'client_results' in data:
                html += '<h5 style="margin: 10px 0; color: #667eea;">Scalability Results:</h5>'
                for client_data in data['client_results']:
                    num_clients = client_data.get('num_clients', 0)
                    html += f'<div style="margin: 10px 0; padding: 10px; background: white; border-radius: 5px;">'
                    html += f'<strong>{num_clients} Clients:</strong>'
                    html += '<div class="test-metrics" style="margin-top: 5px;">'
                    html += f'<div class="test-metric"><span class="label">Throughput:</span><span class="value">{client_data.get("throughput_mbps", 0):.2f} MB/s</span></div>'
                    html += f'<div class="test-metric"><span class="label">Operations/sec:</span><span class="value">{client_data.get("operations_per_sec", 0):.2f}</span></div>'
                    if 'avg_latency_ms' in client_data:
                        html += f'<div class="test-metric"><span class="label">Avg Latency:</span><span class="value">{client_data.get("avg_latency_ms", 0):.2f} ms</span></div>'
                    html += '</div></div>'
            else:
                # Regular test metrics
                if 'throughput_mbps' in data:
                    html += f'<div class="test-metric"><span class="label">Throughput:</span><span class="value">{data.get("throughput_mbps", 0):.2f} MB/s</span></div>'
                if 'operations_per_sec' in data:
                    html += f'<div class="test-metric"><span class="label">Operations/sec:</span><span class="value">{data.get("operations_per_sec", 0):.2f}</span></div>'
                if 'avg_latency_ms' in data:
                    html += f'<div class="test-metric"><span class="label">Avg Latency:</span><span class="value">{data.get("avg_latency_ms", 0):.2f} ms</span></div>'
                if 'max_latency_ms' in data:
                    html += f'<div class="test-metric"><span class="label">Max Latency:</span><span class="value">{data.get("max_latency_ms", 0):.2f} ms</span></div>'
                
                html += f'<div class="test-metric"><span class="label">Duration:</span><span class="value">{data.get("duration_seconds", 0):.2f} s</span></div>'
                
                # Configuration details
                config = data.get('config', {})
                if config:
                    if 'num_clients' in config:
                        html += f'<div class="test-metric"><span class="label">Clients:</span><span class="value">{config.get("num_clients", 1)}</span></div>'
                    if 'loadfile' in config:
                        html += f'<div class="test-metric"><span class="label">Loadfile:</span><span class="value">{config.get("loadfile", "N/A")}</span></div>'
                
                # Add system metrics if available
                if 'system_metrics' in data:
                    metrics = data['system_metrics']
                    if 'cpu' in metrics:
                        html += f'<div class="test-metric"><span class="label">Avg CPU:</span><span class="value">{metrics["cpu"]["avg_percent"]:.1f}%</span></div>'
                    if 'memory' in metrics:
                        html += f'<div class="test-metric"><span class="label">Avg Memory:</span><span class="value">{metrics["memory"]["avg_percent"]:.1f}%</span></div>'
            
            html += '</div>'
        else:
            html += f'<p style="color: #ef4444;">Error: {data.get("error", "Unknown error")}</p>'
        
        html += '</div>'
    
    return html


def main():
    parser = argparse.ArgumentParser(
        description='Generate HTML report from NFS benchmark results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Generate report from single JSON file
  python3 generate_html_report.py nfs_performance_nfsv3_tcp_20240403_120000.json
  
  # Generate report from all files with test-id
  python3 generate_html_report.py --test-id baseline_2026
  
  # Generate report from all files with test-id in specific directory
  python3 generate_html_report.py --test-id prod_test --directory ./results
        '''
    )
    
    # Create mutually exclusive group for file or test-id
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        'json_file',
        nargs='?',
        help='Path to single JSON results file'
    )
    input_group.add_argument(
        '--test-id',
        help='Test identifier to aggregate multiple result files'
    )
    
    parser.add_argument(
        '--directory',
        default='.',
        help='Directory to search for JSON files (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Handle test-id based aggregation
    if args.test_id:
        logger.info(f"Searching for files with test-id: {args.test_id}")
        json_files = find_test_id_files(args.test_id, args.directory)
        
        if not json_files:
            logger.error(f"No files found matching test-id: {args.test_id}")
            logger.info(f"Searched in: {os.path.abspath(args.directory)}")
            logger.info(f"Pattern: nfs_performance_{args.test_id}_*.json")
            sys.exit(1)
        
        logger.info(f"Found {len(json_files)} matching files:")
        for f in json_files:
            logger.info(f"  - {os.path.basename(f)}")
        
        logger.info("Aggregating results...")
        try:
            results = aggregate_test_results(json_files)
        except Exception as e:
            logger.error(f"Failed to aggregate results: {e}")
            sys.exit(1)
    
    # Handle single file
    else:
        json_file = args.json_file
        
        if not os.path.exists(json_file):
            logger.error(f"File not found: {json_file}")
            sys.exit(1)
        
        logger.info(f"Loading results from: {json_file}")
        results = load_results(json_file)
    
    # Generate report
    logger.info("Generating HTML report...")
    output_file = generate_html_report(results)
    
    if output_file:
        logger.info("✓ Report generated successfully!")
        logger.info(f"Open in browser: file://{os.path.abspath(output_file)}")
    else:
        logger.error("Failed to generate report")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
