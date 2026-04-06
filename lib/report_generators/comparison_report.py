#!/usr/bin/env python3
"""
Comparison Report Generator

Generates HTML reports comparing two different test-ids side-by-side.
Useful for comparing different OS versions, software versions, or configurations.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Tuple
from datetime import datetime

from .base import BaseReportGenerator
from .multi_version_report import MultiVersionReportGenerator
from .templates import (
    get_base_template,
    get_header_html,
    get_comparison_header_html,
    get_section_html,
    get_comparison_grid_html,
    get_multi_version_dimension_overview_html,
    get_multi_version_dimension_section_html,
)
from .charts import ChartGenerator
from .dimension_mapper import DIMENSIONS


logger = logging.getLogger(__name__)


class ComparisonReportGenerator(BaseReportGenerator):
    """
    Generate HTML report comparing two different test-ids.
    
    This generator loads results for two test-ids and creates a side-by-side
    comparison report. Useful for evaluating changes between different
    configurations, OS versions, or software versions.
    """
    
    def __init__(self, test_id_1: str, test_id_2: str,
                 directory: Path = None, output_dir: Path = None, report_style: str = 'tool-based',
                 enable_analysis: bool = True, analysis_level: str = 'detailed'):
        """
        Initialize comparison report generator.
        
        Args:
            test_id_1: First test identifier
            test_id_2: Second test identifier
            directory: Directory to search for JSON files (default: current directory)
            output_dir: Optional output directory (default: ./report)
            report_style: Report organization style - 'tool-based' or 'dimension-based' (default: 'tool-based')
            enable_analysis: Whether to include performance analysis (default: True)
            analysis_level: Analysis detail level - 'basic', 'detailed', or 'comprehensive' (default: 'detailed')
        """
        super().__init__(output_dir, report_style, enable_analysis, analysis_level)
        self.test_id_1 = test_id_1
        self.test_id_2 = test_id_2
        self.directory = Path(directory) if directory else Path(".")
        self.chart_generator = ChartGenerator()
    
    def generate(self) -> Path:
        """
        Generate HTML comparison report.
        
        Returns:
            Path to generated HTML file
            
        Raises:
            FileNotFoundError: If files for either test-id not found
            ValueError: If data loading fails
        """
        self.logger.info(f"Generating comparison report: {self.test_id_1} vs {self.test_id_2}")
        
        # Load data
        data = self._load_data()
        
        # Generate HTML
        html_content = self._generate_html(data)
        
        # Write report
        filename = f"nfs_performance_comparison_{self.test_id_1}_vs_{self.test_id_2}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        output_file = self._write_report(html_content, filename)
        
        return output_file
    
    def _load_data(self) -> Dict[str, Any]:
        """
        Load data for both test-ids.
        
        Returns:
            Dictionary containing both test results
            
        Raises:
            FileNotFoundError: If files not found for either test-id
        """
        # Use MultiVersionReportGenerator to load each test-id
        generator_1 = MultiVersionReportGenerator(self.test_id_1, self.directory)
        generator_2 = MultiVersionReportGenerator(self.test_id_2, self.directory)
        
        try:
            results_1 = generator_1._load_data()
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Failed to load test-id '{self.test_id_1}': {e}")
        
        try:
            results_2 = generator_2._load_data()
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Failed to load test-id '{self.test_id_2}': {e}")
        
        return {
            'test_id_1': self.test_id_1,
            'test_id_2': self.test_id_2,
            'results_1': results_1,
            'results_2': results_2,
        }
    
    def _generate_html(self, data: Dict[str, Any]) -> str:
        """
        Generate complete HTML content.
        
        Args:
            data: Comparison data dictionary
            
        Returns:
            Complete HTML document string
        """
        test_id_1 = data['test_id_1']
        test_id_2 = data['test_id_2']
        results_1 = data['results_1']
        results_2 = data['results_2']
        
        # Extract metadata from both test-ids
        metadata_1 = results_1.get('test_metadata', {})
        metadata_2 = results_2.get('test_metadata', {})
        
        # Generate sections based on report style
        header_html = self._generate_header(test_id_1, test_id_2, metadata_1, metadata_2)
        
        if self.report_style == 'dimension-based':
            # Dimension-based report
            # Combine results for dimension-based view
            combined_results = {}
            for version_key, version_data in results_1.get('results_by_version', {}).items():
                combined_results[f"{test_id_1}_{version_key}"] = version_data
            for version_key, version_data in results_2.get('results_by_version', {}).items():
                combined_results[f"{test_id_2}_{version_key}"] = version_data
            
            overview_html = get_multi_version_dimension_overview_html(combined_results)
            charts_html = self._generate_dimension_charts(combined_results)
            details_html = self._generate_dimension_sections(combined_results)
        else:
            # Tool-based report (default)
            comparison_grid_html = self._generate_comparison_grid(
                test_id_1, test_id_2, results_1, results_2
            )
            charts_html = self._generate_comparison_charts(results_1, results_2)
            details_html = self._generate_comparison_details(
                test_id_1, test_id_2, results_1, results_2
            )
            overview_html = comparison_grid_html
        
        # Generate comparison analysis (comparison-only, no individual test-id analysis)
        analysis_html = self._generate_comparison_only_analysis(
            test_id_1, results_1, test_id_2, results_2
        )
        
        # Combine all sections
        content = f"""
        <div class="container">
            {header_html}
            {overview_html}
            {charts_html}
            {analysis_html}
            {details_html}
        </div>
        """
        
        # Wrap in base template
        title = "NFS Benchmark Suite - Test-ID Comparison"
        if self.report_style == 'dimension-based':
            title += " - Dimension View"
        return get_base_template(title, content)
    
    def _generate_dimension_charts(self, combined_results: Dict[str, Any]) -> str:
        """
        Generate dimension-based charts for comparison.
        
        Args:
            combined_results: Combined results from both test-IDs
            
        Returns:
            HTML string with dimension charts
        """
        # Generate all multi-version dimension charts using chart generator
        # This returns a complete HTML string, not a list
        dimension_charts = self.chart_generator.generate_all_multi_version_dimension_charts(combined_results)
        
        return dimension_charts if dimension_charts else ''
    
    def _generate_dimension_sections(self, combined_results: Dict[str, Any]) -> str:
        """
        Generate dimension-based detail sections for comparison.
        
        Args:
            combined_results: Combined results from both test-IDs
            
        Returns:
            HTML string with dimension sections
        """
        sections_html = ''
        
        # Iterate through all dimensions
        for dimension_key, dimension_info in DIMENSIONS.items():
            section_html = get_multi_version_dimension_section_html(
                dimension_key, combined_results
            )
            if section_html:
                sections_html += section_html + '\n'
        
        return sections_html
    
    def _generate_header(self, test_id_1: str, test_id_2: str,
                        metadata_1: Dict[str, Any], metadata_2: Dict[str, Any]) -> str:
        """
        Generate report header for comparison with metadata from both test-ids.
        
        Args:
            test_id_1: First test ID
            test_id_2: Second test ID
            metadata_1: Metadata from first test-id
            metadata_2: Metadata from second test-id
            
        Returns:
            Header HTML string
        """
        title = "NFS Benchmark Suite"
        subtitle = f"Comparison Report: {test_id_1} vs {test_id_2}"
        
        # Use the new comparison header template that shows both metadata side-by-side
        return get_comparison_header_html(title, subtitle, metadata_1, metadata_2)
    
    def _generate_comparison_grid(self, test_id_1: str, test_id_2: str,
                                  results_1: Dict[str, Any], 
                                  results_2: Dict[str, Any]) -> str:
        """
        Generate comparison grid showing both test-ids.
        
        Args:
            test_id_1: First test ID
            test_id_2: Second test ID
            results_1: Results for first test
            results_2: Results for second test
            
        Returns:
            Comparison grid HTML string
        """
        # Extract metadata
        metadata_1 = results_1.get('test_metadata', {})
        metadata_2 = results_2.get('test_metadata', {})
        
        # Count versions
        versions_1 = len(results_1.get('results_by_version', {}))
        versions_2 = len(results_2.get('results_by_version', {}))
        
        # Prepare display metadata
        display_meta_1 = {
            'versions': versions_1,
        }
        if metadata_1.get('server_ip'):
            display_meta_1['server_ip'] = metadata_1['server_ip']
        if metadata_1.get('transport'):
            display_meta_1['transport'] = metadata_1['transport'].upper()
        
        display_meta_2 = {
            'versions': versions_2,
        }
        if metadata_2.get('server_ip'):
            display_meta_2['server_ip'] = metadata_2['server_ip']
        if metadata_2.get('transport'):
            display_meta_2['transport'] = metadata_2['transport'].upper()
        
        grid_html = get_comparison_grid_html(
            test_id_1, test_id_2,
            display_meta_1, display_meta_2
        )
        
        return get_section_html("🔄 Test-ID Comparison", grid_html)
    
    def _generate_comparison_charts(self, results_1: Dict[str, Any], 
                                    results_2: Dict[str, Any]) -> str:
        """
        Generate comparison charts.
        
        Args:
            results_1: Results for first test
            results_2: Results for second test
            
        Returns:
            Charts HTML string
        """
        if not self.chart_generator.plotly_available:
            return get_section_html(
                "📊 Performance Charts",
                "<p>Charts not available. Install plotly: pip3 install plotly</p>"
            )
        
        # Combine results from both test-ids for comparison
        combined_results = {}
        
        # Add results from test-id 1
        for version_key, version_data in results_1.get('results_by_version', {}).items():
            combined_results[f"{self.test_id_1}_{version_key}"] = version_data
        
        # Add results from test-id 2
        for version_key, version_data in results_2.get('results_by_version', {}).items():
            combined_results[f"{self.test_id_2}_{version_key}"] = version_data
        
        # Generate charts using combined data
        return self.chart_generator.generate_all_multi_version_charts(combined_results)
    
    def _generate_comparison_details(self, test_id_1: str, test_id_2: str,
                                     results_1: Dict[str, Any], 
                                     results_2: Dict[str, Any]) -> str:
        """
        Generate detailed comparison information.
        
        Args:
            test_id_1: First test ID
            test_id_2: Second test ID
            results_1: Results for first test
            results_2: Results for second test
            
        Returns:
            Details HTML string
        """
        details_html = """
        <div class="section">
            <h2>📋 Comparison Details</h2>
            <p>This report compares performance metrics between two different test runs.</p>
            <p>Use this to evaluate:</p>
            <ul style="margin-left: 20px; margin-top: 10px;">
                <li>Different operating system versions</li>
                <li>Different NFS server software versions</li>
                <li>Different hardware configurations</li>
                <li>Different network configurations</li>
                <li>Before/after optimization changes</li>
            </ul>
        </div>
        """
        
        # Add version-by-version comparison
        versions_1 = set(results_1.get('results_by_version', {}).keys())
        versions_2 = set(results_2.get('results_by_version', {}).keys())
        common_versions = versions_1 & versions_2
        
        if common_versions:
            comparison_table = "<table><thead><tr><th>NFS Version</th><th>Test ID 1</th><th>Test ID 2</th><th>Status</th></tr></thead><tbody>"
            
            for version in sorted(common_versions):
                comparison_table += f"""
                <tr class="success">
                    <td><strong>{version.replace('_', ' ').upper()}</strong></td>
                    <td>{test_id_1}</td>
                    <td>{test_id_2}</td>
                    <td>✓ Both tested</td>
                </tr>
                """
            
            # Add versions only in test 1
            only_in_1 = versions_1 - versions_2
            for version in sorted(only_in_1):
                comparison_table += f"""
                <tr class="warning">
                    <td><strong>{version.replace('_', ' ').upper()}</strong></td>
                    <td>{test_id_1}</td>
                    <td>-</td>
                    <td>⚠ Only in Test 1</td>
                </tr>
                """
            
            # Add versions only in test 2
            only_in_2 = versions_2 - versions_1
            for version in sorted(only_in_2):
                comparison_table += f"""
                <tr class="warning">
                    <td><strong>{version.replace('_', ' ').upper()}</strong></td>
                    <td>-</td>
                    <td>{test_id_2}</td>
                    <td>⚠ Only in Test 2</td>
                </tr>
                """
            
            comparison_table += "</tbody></table>"
            
            details_html += get_section_html("Version Coverage Comparison", comparison_table)
        
        return details_html
    
    def _generate_comparison_analysis(self, test_id_1: str, results_1: Dict[str, Any],
                                     test_id_2: str, results_2: Dict[str, Any]) -> str:
        """
        Generate comparison analysis for both test-ids.
        
        Args:
            test_id_1: First test ID
            results_1: Results for first test
            test_id_2: Second test ID
            results_2: Results for second test
            
        Returns:
            Comparison analysis HTML
        """
        if not self.enable_analysis:
            return ""
        
        try:
            from ..performance_analyzer import PerformanceAnalyzer
            from .templates import get_comparison_analysis_html, get_analysis_error_html
            
            # Analyze both test-ids
            analyzer_1 = PerformanceAnalyzer(results_1)
            analyzer_2 = PerformanceAnalyzer(results_2)
            
            analysis_1 = analyzer_1.analyze()
            analysis_2 = analyzer_2.analyze()
            
            # Generate comparison-specific insights
            comparison_insights = self._generate_comparison_insights(
                test_id_1, analysis_1, test_id_2, analysis_2
            )
            
            # Add enhanced comparison insights from ComparisonAnalyzer
            enhanced_insights = self._generate_enhanced_comparison_insights(
                test_id_1, results_1, test_id_2, results_2
            )
            comparison_insights.extend(enhanced_insights)
            
            # Render comparison analysis HTML
            return get_comparison_analysis_html(
                test_id_1, analysis_1,
                test_id_2, analysis_2,
                comparison_insights,
                self.report_style
            )
            
        except Exception as e:
            self.logger.error(f"Comparison analysis failed: {e}", exc_info=True)
            from .templates import get_analysis_error_html
            return get_analysis_error_html(str(e))
    
    def _generate_enhanced_comparison_insights(self, test_id_1: str, results_1: Dict[str, Any],
                                               test_id_2: str, results_2: Dict[str, Any]) -> list:
        """
        Generate enhanced comparison insights using ComparisonAnalyzer.
        
        This is a new function that doesn't modify existing behavior.
        
        Args:
            test_id_1: First test ID
            results_1: Results for first test
            test_id_2: Second test ID
            results_2: Results for second test
            
        Returns:
            List of enhanced comparison insights
        """
        try:
            from ..performance_analyzer import ComparisonAnalyzer
            
            # Extract version data for ComparisonAnalyzer
            testid1_versions = self._extract_version_metrics(results_1)
            testid2_versions = self._extract_version_metrics(results_2)
            
            # Use ComparisonAnalyzer for cross-testid and within-testid comparisons
            comparison_analyzer = ComparisonAnalyzer(
                test_id_1, testid1_versions,
                test_id_2, testid2_versions
            )
            comparison_analysis = comparison_analyzer.analyze()
            
            # Combine all insights
            all_insights = []
            
            # Add cross-testid same-version insights (1a)
            cross_testid_insights = comparison_analysis.get('cross_testid_insights', [])
            # Filter out "No Common NFS Versions" warning if it's the only insight
            if len(cross_testid_insights) == 1 and cross_testid_insights[0].get('title') == 'No Common NFS Versions':
                # Don't add this warning - it's expected when comparing different transports
                pass
            else:
                all_insights.extend(cross_testid_insights)
            
            # Add within-testid cross-version insights (1b)
            testid1_version_insights = comparison_analysis.get('testid1_version_insights', [])
            testid2_version_insights = comparison_analysis.get('testid2_version_insights', [])
            
            # Filter out "Single Version Only" info messages
            testid1_version_insights = [i for i in testid1_version_insights if 'Single Version Only' not in i.get('title', '')]
            testid2_version_insights = [i for i in testid2_version_insights if 'Single Version Only' not in i.get('title', '')]
            
            all_insights.extend(testid1_version_insights)
            all_insights.extend(testid2_version_insights)
            
            return all_insights
            
        except Exception as e:
            self.logger.warning(f"Enhanced comparison analysis failed: {e}")
            return []
    
    def _generate_comparison_only_analysis(self, test_id_1: str, results_1: Dict[str, Any],
                                          test_id_2: str, results_2: Dict[str, Any]) -> str:
        """
        Generate comparison analysis using ONLY ComparisonAnalyzer (no individual PerformanceAnalyzer).
        
        This method provides clean comparison insights without the critical/warning counts
        or health scores from individual test-id analysis.
        
        Args:
            test_id_1: First test ID
            results_1: Results for first test
            test_id_2: Second test ID
            results_2: Results for second test
            
        Returns:
            Comparison analysis HTML with only ComparisonAnalyzer insights (no health scores)
        """
        if not self.enable_analysis:
            return ""
        
        try:
            from ..performance_analyzer import ComparisonAnalyzer
            from .templates import get_analysis_error_html, get_comparison_only_analysis_html
            
            # Extract version data for ComparisonAnalyzer
            testid1_versions = self._extract_version_metrics(results_1)
            testid2_versions = self._extract_version_metrics(results_2)
            
            # Use ComparisonAnalyzer for cross-testid and within-testid comparisons
            comparison_analyzer = ComparisonAnalyzer(
                test_id_1, testid1_versions,
                test_id_2, testid2_versions
            )
            comparison_analysis = comparison_analyzer.analyze()
            
            # Get only comparison insights (no individual test-id analysis)
            comparison_insights = []
            
            # Add cross-testid same-version insights (1a)
            cross_testid_insights = comparison_analysis.get('cross_testid_insights', [])
            # Filter out "No Common NFS Versions" warning if it's expected
            for insight in cross_testid_insights:
                if insight.get('title') != 'No Common NFS Versions':
                    comparison_insights.append(insight)
            
            # Add within-testid cross-version insights (1b)
            testid1_version_insights = comparison_analysis.get('testid1_version_insights', [])
            testid2_version_insights = comparison_analysis.get('testid2_version_insights', [])
            
            # Filter out "Single Version Only" info messages
            for insight in testid1_version_insights:
                if 'Single Version Only' not in insight.get('title', ''):
                    comparison_insights.append(insight)
            
            for insight in testid2_version_insights:
                if 'Single Version Only' not in insight.get('title', ''):
                    comparison_insights.append(insight)
            
            # Render using comparison-only template (no health scores)
            return get_comparison_only_analysis_html(
                comparison_insights,
                self.report_style
            )
            
        except Exception as e:
            self.logger.error(f"Comparison-only analysis failed: {e}", exc_info=True)
            from .templates import get_analysis_error_html
            return get_analysis_error_html(str(e))

    
    def _extract_version_metrics(self, results: Dict[str, Any]) -> Dict[str, Dict]:
        """
        Extract version-specific metrics for ComparisonAnalyzer.
        
        Args:
            results: Multi-version test results
            
        Returns:
            Dict of version data with extracted metrics
        """
        versions = {}
        
        # Get versions from results - use results_by_version key
        versions_data = results.get('results_by_version', {})
        
        for version_key, version_data in versions_data.items():
            # Parse nfs_version and transport from version_key (e.g., "nfsv3_tcp")
            parts = version_key.rsplit('_', 1)
            if len(parts) == 2:
                nfs_version, transport = parts
            else:
                nfs_version = version_key
                transport = 'tcp'
            
            # Extract metrics from this version
            metrics = {}
            
            # Extract FIO metrics
            fio_tests = version_data.get('fio_tests', {})
            for test_name, test_data in fio_tests.items():
                if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                    if 'read_bandwidth_mbps' in test_data:
                        metrics[f'fio_{test_name}_read_mbps'] = test_data['read_bandwidth_mbps']
                    if 'write_bandwidth_mbps' in test_data:
                        metrics[f'fio_{test_name}_write_mbps'] = test_data['write_bandwidth_mbps']
                    if 'read_iops' in test_data:
                        metrics[f'fio_{test_name}_read_iops'] = test_data['read_iops']
                    if 'write_iops' in test_data:
                        metrics[f'fio_{test_name}_write_iops'] = test_data['write_iops']
                    if 'avg_latency_ms' in test_data:
                        metrics[f'fio_{test_name}_latency_ms'] = test_data['avg_latency_ms']
            
            # Extract IOzone metrics
            iozone_tests = version_data.get('iozone_tests', {})
            for test_name, test_data in iozone_tests.items():
                if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                    if 'read_throughput_mbps' in test_data:
                        metrics[f'iozone_{test_name}_read_mbps'] = test_data['read_throughput_mbps']
                    if 'write_throughput_mbps' in test_data:
                        metrics[f'iozone_{test_name}_write_mbps'] = test_data['write_throughput_mbps']
            
            # Extract DBench metrics
            dbench_tests = version_data.get('dbench_tests', {})
            for test_name, test_data in dbench_tests.items():
                if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                    if 'throughput_mbps' in test_data:
                        metrics[f'dbench_{test_name}_mbps'] = test_data['throughput_mbps']
                    if 'operations_per_sec' in test_data:
                        metrics[f'dbench_{test_name}_ops'] = test_data['operations_per_sec']
            
            # Extract Bonnie++ metrics
            bonnie_tests = version_data.get('bonnie_tests', {})
            for test_name, test_data in bonnie_tests.items():
                if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                    if 'sequential_output_block_mbps' in test_data:
                        metrics[f'bonnie_{test_name}_seq_out'] = test_data['sequential_output_block_mbps']
                    if 'sequential_input_block_mbps' in test_data:
                        metrics[f'bonnie_{test_name}_seq_in'] = test_data['sequential_input_block_mbps']
            
            # Extract DD metrics
            dd_tests = version_data.get('dd_tests', {})
            for test_name, test_data in dd_tests.items():
                if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                    if 'throughput_mbps' in test_data:
                        metrics[f'dd_{test_name}_mbps'] = test_data['throughput_mbps']
            
            versions[version_key] = {
                'nfs_version': nfs_version,
                'transport': transport,
                'metrics': metrics
            }
        
        return versions
    
    def _generate_comparison_insights(self, test_id_1: str, analysis_1: Dict[str, Any],
                                      test_id_2: str, analysis_2: Dict[str, Any]) -> list:
        """
        Generate insights comparing the two test-ids.
        
        Args:
            test_id_1: First test ID
            analysis_1: Analysis for first test
            test_id_2: Second test ID
            analysis_2: Analysis for second test
            
        Returns:
            List of comparison insight dictionaries
        """
        insights = []
        
        # Compare health scores - extract score from dict if needed
        health_1_raw = analysis_1.get('overall_health', 0)
        health_2_raw = analysis_2.get('overall_health', 0)
        
        # Handle dict format
        health_1 = health_1_raw.get('score', 0) if isinstance(health_1_raw, dict) else health_1_raw
        health_2 = health_2_raw.get('score', 0) if isinstance(health_2_raw, dict) else health_2_raw
        
        if abs(health_1 - health_2) > 10:
            if health_2 > health_1:
                insights.append({
                    'severity': 'info',
                    'title': 'Performance Improvement Detected',
                    'description': f'{test_id_2} shows {health_2 - health_1:.1f} point improvement in health score ({health_2:.0f} vs {health_1:.0f})',
                    'recommendation': f'Consider adopting configuration from {test_id_2} for production use.'
                })
            else:
                insights.append({
                    'severity': 'warning',
                    'title': 'Performance Regression Detected',
                    'description': f'{test_id_2} shows {health_1 - health_2:.1f} point decrease in health score ({health_2:.0f} vs {health_1:.0f})',
                    'recommendation': f'Investigate changes between {test_id_1} and {test_id_2} that may have caused regression.'
                })
        
        # Compare critical issues
        critical_1 = analysis_1.get('severity_counts', {}).get('critical', 0)
        critical_2 = analysis_2.get('severity_counts', {}).get('critical', 0)
        
        if critical_2 < critical_1:
            insights.append({
                'severity': 'info',
                'title': 'Critical Issues Resolved',
                'description': f'{test_id_2} has {critical_1 - critical_2} fewer critical issues than {test_id_1}',
                'recommendation': 'Review what changes resolved these critical issues.'
            })
        elif critical_2 > critical_1:
            insights.append({
                'severity': 'critical',
                'title': 'New Critical Issues Introduced',
                'description': f'{test_id_2} has {critical_2 - critical_1} more critical issues than {test_id_1}',
                'recommendation': 'Investigate and resolve new critical issues before deployment.'
            })
        
        return insights

# Made with Bob
