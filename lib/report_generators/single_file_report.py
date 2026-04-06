#!/usr/bin/env python3
"""
Single File Report Generator

Generates HTML reports from a single JSON benchmark result file.
This is the most common use case for quick test validation.
"""

import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from .base import BaseReportGenerator
from .formatters import (
    extract_test_results,
    get_test_metadata,
    calculate_summary_stats,
    get_best_throughput,
    get_best_iops,
    get_best_latency,
    format_throughput,
    format_iops,
    format_latency,
)
from .templates import (
    get_base_template,
    get_header_html,
    get_metric_card_html,
    get_section_html,
    get_test_result_html,
    get_no_data_html,
    get_dimension_overview_html,
    get_dimension_section_html,
)
from .charts import ChartGenerator
from . import dimension_mapper


logger = logging.getLogger(__name__)


class SingleFileReportGenerator(BaseReportGenerator):
    """
    Generate HTML report from a single JSON benchmark result file.
    
    This generator handles the most common scenario: generating a report
    from a single test run with one NFS version.
    """
    
    def __init__(self, json_file: Path, output_dir: Path = None, report_style: str = 'tool-based'):
        """
        Initialize single file report generator.
        
        Args:
            json_file: Path to JSON results file
            output_dir: Optional output directory (default: ./report)
            report_style: Report organization style - 'tool-based' or 'dimension-based' (default: 'tool-based')
        """
        super().__init__(output_dir, report_style)
        self.json_file = Path(json_file)
        self.chart_generator = ChartGenerator()
    
    def generate(self) -> Path:
        """
        Generate HTML report from single JSON file.
        
        Returns:
            Path to generated HTML file
            
        Raises:
            FileNotFoundError: If JSON file doesn't exist
            ValueError: If JSON data is invalid
        """
        self.logger.info(f"Generating report from: {self.json_file}")
        
        # Load data
        data = self._load_data()
        
        # Generate HTML
        html_content = self._generate_html(data)
        
        # Write report
        output_file = self._write_report(html_content)
        
        return output_file
    
    def _load_data(self) -> Dict[str, Any]:
        """
        Load and validate JSON data.
        
        Returns:
            Dictionary containing loaded data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If data validation fails
        """
        results = self._load_json_file(self.json_file)
        
        # Validate that we have some test results
        test_results = extract_test_results(results)
        has_tests = any(test_results.get(key) for key in 
                       ['dd_tests', 'fio_tests', 'iozone_tests', 'bonnie_tests', 'dbench_tests'])
        
        if not has_tests:
            raise ValueError("No test results found in JSON file")
        
        return results
    
    def _generate_html(self, data: Dict[str, Any]) -> str:
        """
        Generate complete HTML content.
        
        Args:
            data: Loaded JSON data
            
        Returns:
            Complete HTML document string
        """
        # Extract test results
        test_results = extract_test_results(data)
        metadata = get_test_metadata(data)
        
        # Generate sections based on report style
        header_html = self._generate_header(metadata)
        
        if self.report_style == 'dimension-based':
            # Dimension-based report
            summary_html = get_dimension_overview_html(test_results)
            charts_html = self._generate_dimension_charts(test_results)
            tests_html = self._generate_dimension_sections(test_results)
        else:
            # Tool-based report (default)
            summary_html = self._generate_summary(test_results, metadata)
            charts_html = self._generate_charts(test_results)
            tests_html = self._generate_test_sections(test_results)
        
        # Combine all sections
        content = f"""
        <div class="container">
            {header_html}
            {summary_html}
            {charts_html}
            {tests_html}
        </div>
        """
        
        # Wrap in base template
        title = "NFS Benchmark Suite Report"
        if self.report_style == 'dimension-based':
            title += " - Dimension View"
        return get_base_template(title, content)
    
    def _generate_header(self, metadata: Dict[str, Any]) -> str:
        """
        Generate report header.
        
        Args:
            metadata: Test metadata
            
        Returns:
            Header HTML string
        """
        title = "NFS Benchmark Suite"
        subtitle = "Performance Test Report"
        
        # Format metadata for display
        display_metadata = {}
        if metadata.get('server_ip'):
            display_metadata['server_ip'] = metadata['server_ip']
        if metadata.get('hostname'):
            display_metadata['hostname'] = metadata['hostname']
        if metadata.get('timestamp'):
            display_metadata['timestamp'] = metadata['timestamp']
        
        return get_header_html(title, subtitle, display_metadata)
    
    def _generate_summary(self, test_results: Dict[str, Dict], 
                         metadata: Dict[str, Any]) -> str:
        """
        Generate summary section with key metrics.
        
        Args:
            test_results: Dictionary of test results
            metadata: Test metadata
            
        Returns:
            Summary HTML string
        """
        # Calculate statistics
        stats = calculate_summary_stats(test_results)
        
        # Get best metrics
        best_tp_tool, best_tp_value, best_tp_test = get_best_throughput(test_results)
        best_iops_tool, best_iops_value, best_iops_test = get_best_iops(test_results)
        best_lat_tool, best_lat_value, best_lat_test = get_best_latency(test_results)
        
        # Generate metric cards
        cards_html = '<div class="summary-grid">'
        
        # Test statistics card
        cards_html += get_metric_card_html(
            "Tests Passed",
            f"{stats['passed_tests']}/{stats['total_tests']}",
            "",
            f"Pass Rate: {stats['pass_rate']:.1f}%"
        )
        
        # Best throughput card
        if best_tp_value > 0:
            cards_html += get_metric_card_html(
                "Best Throughput",
                format_throughput(best_tp_value, ""),
                "MB/s",
                f"{best_tp_tool} - {best_tp_test.replace('_', ' ').title()}"
            )
        
        # Best IOPS card
        if best_iops_value > 0:
            cards_html += get_metric_card_html(
                "Best IOPS",
                f"{best_iops_value:.0f}",
                "IOPS",
                f"{best_iops_tool} - {best_iops_test.replace('_', ' ').title()}"
            )
        
        # Best latency card
        if best_lat_value > 0 and best_lat_value != float('inf'):
            cards_html += get_metric_card_html(
                "Best Latency",
                format_latency(best_lat_value, ""),
                "ms",
                f"{best_lat_tool} - {best_lat_test.replace('_', ' ').title()}"
            )
        
        cards_html += '</div>'
        
        return cards_html
    
    def _generate_charts(self, test_results: Dict[str, Dict]) -> str:
        """
        Generate all performance charts.
        
        Args:
            test_results: Dictionary of test results
            
        Returns:
            Charts HTML string
        """
        if not self.chart_generator.plotly_available:
            return get_section_html(
                "📊 Performance Charts",
                "<p>Charts not available. Install plotly: pip3 install plotly</p>"
            )
        
        return self.chart_generator.generate_all_single_version_charts(test_results)
    
    def _generate_test_sections(self, test_results: Dict[str, Dict]) -> str:
        """
        Generate detailed test result sections.
        
        Args:
            test_results: Dictionary of test results
            
        Returns:
            Test sections HTML string
        """
        sections_html = ""
        
        # DD Tests
        if test_results.get('dd_tests'):
            sections_html += self._generate_dd_section(test_results['dd_tests'])
        
        # FIO Tests
        if test_results.get('fio_tests'):
            sections_html += self._generate_fio_section(test_results['fio_tests'])
        
        # IOzone Tests
        if test_results.get('iozone_tests'):
            sections_html += self._generate_iozone_section(test_results['iozone_tests'])
        
        # Bonnie++ Tests
        if test_results.get('bonnie_tests'):
            sections_html += self._generate_bonnie_section(test_results['bonnie_tests'])
        
        # DBench Tests
        if test_results.get('dbench_tests'):
            sections_html += self._generate_dbench_section(test_results['dbench_tests'])
        
        return sections_html
    
    def _generate_dd_section(self, dd_tests: Dict[str, Any]) -> str:
        """Generate DD tests section."""
        content = ""
        for test_name, test_data in dd_tests.items():
            if test_data.get('status') == 'passed':
                metrics = {
                    'Throughput': format_throughput(test_data.get('throughput_mbps', 0)),
                    'Duration': f"{test_data.get('duration_seconds', 0):.1f}s",
                    'Size': f"{test_data.get('size_mb', 0)} MB",
                    'Block Size': test_data.get('block_size', 'N/A'),
                }
                content += get_test_result_html(test_name, 'passed', metrics)
            else:
                content += f'<div class="test-result failed"><h4>{test_name.replace("_", " ").title()} <span class="status-badge failed">failed</span></h4><p style="color: #ef4444;">Error: {test_data.get("error", "Unknown error")}</p></div>'
        
        return get_section_html("DD Test Results", content or get_no_data_html())
    
    def _generate_fio_section(self, fio_tests: Dict[str, Any]) -> str:
        """Generate FIO tests section."""
        content = ""
        for test_name, test_data in fio_tests.items():
            if test_data.get('status') == 'passed':
                metrics = {
                    'Read IOPS': f"{test_data.get('read_iops', 0):.0f}",
                    'Write IOPS': f"{test_data.get('write_iops', 0):.0f}",
                    'Read BW': format_throughput(test_data.get('read_bw_mbps', 0)),
                    'Write BW': format_throughput(test_data.get('write_bw_mbps', 0)),
                    'Duration': f"{test_data.get('duration_seconds', 0):.1f}s",
                }
                content += get_test_result_html(test_name, 'passed', metrics)
            else:
                content += f'<div class="test-result failed"><h4>{test_name.replace("_", " ").title()} <span class="status-badge failed">failed</span></h4><p style="color: #ef4444;">Error: {test_data.get("error", "Unknown error")}</p></div>'
        
        return get_section_html("FIO Test Results", content or get_no_data_html())
    
    def _generate_iozone_section(self, iozone_tests: Dict[str, Any]) -> str:
        """Generate IOzone tests section."""
        content = ""
        for test_name, test_data in iozone_tests.items():
            if test_data.get('status') == 'passed':
                if test_name == 'scaling_test':
                    # Handle scaling test specially
                    scaling_results = test_data.get('scaling_results', {})
                    for thread_name, thread_data in scaling_results.items():
                        metrics = {
                            'Threads': thread_name.replace('_', ' '),
                            'Read': format_throughput(thread_data.get('read_throughput_mbps', 0)),
                            'Write': format_throughput(thread_data.get('write_throughput_mbps', 0)),
                        }
                        content += get_test_result_html(f"{test_name}_{thread_name}", 'passed', metrics)
                else:
                    metrics = {
                        'Read': format_throughput(test_data.get('read_throughput_mbps', 0)),
                        'Write': format_throughput(test_data.get('write_throughput_mbps', 0)),
                        'Duration': f"{test_data.get('duration_seconds', 0):.1f}s",
                    }
                    content += get_test_result_html(test_name, 'passed', metrics)
            else:
                content += f'<div class="test-result failed"><h4>{test_name.replace("_", " ").title()} <span class="status-badge failed">failed</span></h4><p style="color: #ef4444;">Error: {test_data.get("error", "Unknown error")}</p></div>'
        
        return get_section_html("IOzone Test Results", content or get_no_data_html())
    
    def _generate_bonnie_section(self, bonnie_tests: Dict[str, Any]) -> str:
        """Generate Bonnie++ tests section."""
        content = ""
        for test_name, test_data in bonnie_tests.items():
            if test_data.get('status') == 'passed':
                metrics = {
                    'Sequential Output': format_throughput(test_data.get('sequential_output_block_mbps', 0)),
                    'Sequential Input': format_throughput(test_data.get('sequential_input_block_mbps', 0)),
                    'File Create': f"{test_data.get('file_create_seq_per_sec', 0):.0f} files/sec",
                    'File Delete': f"{test_data.get('file_delete_seq_per_sec', 0):.0f} files/sec",
                    'Duration': f"{test_data.get('duration_seconds', 0):.1f}s",
                }
                content += get_test_result_html(test_name, 'passed', metrics)
            else:
                content += f'<div class="test-result failed"><h4>{test_name.replace("_", " ").title()} <span class="status-badge failed">failed</span></h4><p style="color: #ef4444;">Error: {test_data.get("error", "Unknown error")}</p></div>'
        
        return get_section_html("Bonnie++ Test Results", content or get_no_data_html())
    
    def _generate_dbench_section(self, dbench_tests: Dict[str, Any]) -> str:
        """Generate DBench tests section."""
        content = ""
        for test_name, test_data in dbench_tests.items():
            if test_data.get('status') == 'passed':
                if test_name == 'scalability_test' and 'client_results' in test_data:
                    # Handle scalability test
                    for client_data in test_data['client_results']:
                        num_clients = client_data.get('num_clients', 0)
                        metrics = {
                            'Clients': str(num_clients),
                            'Throughput': format_throughput(client_data.get('throughput_mbps', 0)),
                            'Operations/sec': f"{client_data.get('operations_per_sec', 0):.0f}",
                            'Avg Latency': format_latency(client_data.get('avg_latency_ms', 0)),
                        }
                        content += get_test_result_html(f"{test_name}_{num_clients}_clients", 'passed', metrics)
                else:
                    metrics = {
                        'Throughput': format_throughput(test_data.get('throughput_mbps', 0)),
                        'Operations/sec': f"{test_data.get('operations_per_sec', 0):.0f}",
                        'Avg Latency': format_latency(test_data.get('avg_latency_ms', 0)),
                        'Max Latency': format_latency(test_data.get('max_latency_ms', 0)),
                    }
                    content += get_test_result_html(test_name, 'passed', metrics)
            else:
                content += f'<div class="test-result failed"><h4>{test_name.replace("_", " ").title()} <span class="status-badge failed">failed</span></h4><p style="color: #ef4444;">Error: {test_data.get("error", "Unknown error")}</p></div>'
        
        return get_section_html("DBench Test Results", content or get_no_data_html())
    
    def _generate_dimension_charts(self, test_results: Dict[str, Dict]) -> str:
        """
        Generate dimension-based performance charts.
        
        Args:
            test_results: Dictionary of test results
            
        Returns:
            Charts HTML string
        """
        if not self.chart_generator.plotly_available:
            return get_section_html(
                "📊 Performance Charts",
                "<p>Charts not available. Install plotly: pip3 install plotly</p>"
            )
        
        return self.chart_generator.generate_all_dimension_charts(test_results)
    
    def _generate_dimension_sections(self, test_results: Dict[str, Dict]) -> str:
        """
        Generate test result sections organized by performance dimension.
        
        Args:
            test_results: Dictionary of test results
            
        Returns:
            Dimension sections HTML string
        """
        sections_html = ""
        
        # Generate a section for each dimension
        for dimension_key in dimension_mapper.get_all_dimensions():
            # Extract data for this dimension
            dimension_data = dimension_mapper.extract_dimension_data(test_results, dimension_key)
            
            if not dimension_data:
                continue
            
            # Get chart for this dimension
            chart_html = ""
            if self.chart_generator.plotly_available:
                if dimension_key == 'throughput':
                    chart_html = self.chart_generator.create_dimension_throughput_chart(test_results)
                elif dimension_key == 'iops':
                    chart_html = self.chart_generator.create_dimension_iops_chart(test_results)
                elif dimension_key == 'latency':
                    chart_html = self.chart_generator.create_dimension_latency_chart(test_results)
                elif dimension_key == 'metadata':
                    chart_html = self.chart_generator.create_dimension_metadata_chart(test_results)
                elif dimension_key == 'cache_effects':
                    chart_html = self.chart_generator.create_dimension_cache_chart(test_results)
                elif dimension_key == 'concurrency':
                    chart_html = self.chart_generator.create_dimension_concurrency_chart(test_results)
            
            # Generate section with chart and test results
            sections_html += get_dimension_section_html(dimension_key, dimension_data, chart_html or "")
        
        return sections_html

# Made with Bob
