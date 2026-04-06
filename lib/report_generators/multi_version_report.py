#!/usr/bin/env python3
"""
Multi-Version Report Generator

Generates HTML reports aggregating results from multiple NFS versions
for the same test-id. Useful for comparing NFSv3, v4.0, v4.1, and v4.2.
"""

import glob
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from .base import BaseReportGenerator
from .formatters import extract_test_results, get_test_metadata
from .templates import (
    get_base_template,
    get_header_html,
    get_section_html,
    get_version_card_html,
    get_no_data_html,
    get_multi_version_dimension_overview_html,
    get_multi_version_dimension_section_html,
)
from .charts import ChartGenerator
from . import dimension_mapper


logger = logging.getLogger(__name__)


class MultiVersionReportGenerator(BaseReportGenerator):
    """
    Generate HTML report aggregating multiple NFS versions by test-id.
    
    This generator finds all JSON files matching a test-id pattern and
    creates a unified report comparing performance across NFS versions.
    """
    
    def __init__(self, test_id: str, directory: Path = None, output_dir: Path = None,
                 report_style: str = 'tool-based', enable_analysis: bool = True,
                 analysis_level: str = 'detailed'):
        """
        Initialize multi-version report generator.
        
        Args:
            test_id: Test identifier to search for
            directory: Directory to search for JSON files (default: current directory)
            output_dir: Optional output directory (default: ./report)
            report_style: Report organization style - 'tool-based' or 'dimension-based' (default: 'tool-based')
            enable_analysis: Whether to include performance analysis (default: True)
            analysis_level: Analysis detail level - 'basic', 'detailed', or 'comprehensive' (default: 'detailed')
        """
        super().__init__(output_dir, report_style, enable_analysis, analysis_level)
        self.test_id = test_id
        self.directory = Path(directory) if directory else Path(".")
        self.chart_generator = ChartGenerator()
    
    def generate(self) -> Path:
        """
        Generate HTML report from multiple version files.
        
        Returns:
            Path to generated HTML file
            
        Raises:
            FileNotFoundError: If no matching files found
            ValueError: If data aggregation fails
        """
        self.logger.info(f"Generating multi-version report for test-id: {self.test_id}")
        
        # Load data
        data = self._load_data()
        
        # Generate HTML
        html_content = self._generate_html(data)
        
        # Write report
        filename = f"nfs_performance_report_{self.test_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        output_file = self._write_report(html_content, filename)
        
        return output_file
    
    def _load_data(self) -> Dict[str, Any]:
        """
        Find and load all JSON files matching test-id.
        
        Returns:
            Aggregated results dictionary
            
        Raises:
            FileNotFoundError: If no matching files found
            ValueError: If aggregation fails
        """
        # Find matching files
        pattern = f"nfs_performance_{self.test_id}_*.json"
        json_files = sorted(glob.glob(str(self.directory / pattern)))
        
        if not json_files:
            raise FileNotFoundError(
                f"No files found matching test-id: {self.test_id}\n"
                f"Searched in: {self.directory.absolute()}\n"
                f"Pattern: {pattern}"
            )
        
        self.logger.info(f"Found {len(json_files)} matching files:")
        for f in json_files:
            self.logger.info(f"  - {Path(f).name}")
        
        # Aggregate results
        return self._aggregate_results(json_files)
    
    def _aggregate_results(self, json_files: List[str]) -> Dict[str, Any]:
        """
        Aggregate multiple JSON files into multi-version format.
        
        Args:
            json_files: List of JSON file paths
            
        Returns:
            Aggregated results dictionary
        """
        aggregated = {
            'test_metadata': {},
            'results_by_version': {}
        }
        
        # Track all versions found
        all_versions = []
        
        # Load all results
        for json_file in json_files:
            try:
                result = self._load_json_file(Path(json_file))
                
                # Extract version and transport info
                nfs_version = result.get('nfs_version')
                transport = result.get('transport', 'tcp')
                
                if nfs_version:
                    version_key = f"nfsv{nfs_version}_{transport}"
                    
                    # Track this version
                    if nfs_version not in all_versions:
                        all_versions.append(nfs_version)
                    
                    # Extract test results (handle both old and new formats)
                    if 'results' in result and isinstance(result['results'], dict):
                        aggregated['results_by_version'][version_key] = result['results']
                    else:
                        # Old format - results at top level
                        aggregated['results_by_version'][version_key] = result
                    
                    self.logger.info(f"Loaded {version_key} from {Path(json_file).name}")
                
                # Use metadata from first file as base
                if not aggregated['test_metadata'] and 'test_metadata' in result:
                    aggregated['test_metadata'] = result['test_metadata'].copy()
                    aggregated['test_metadata']['test_id'] = self.test_id
                    
            except Exception as e:
                self.logger.warning(f"Failed to load {json_file}: {e}")
                continue
        
        if not aggregated['results_by_version']:
            raise ValueError("No valid version results found in JSON files")
        
        # Update versions_tested with all versions found
        if aggregated['test_metadata']:
            aggregated['test_metadata']['versions_tested'] = sorted(all_versions, key=lambda x: float(x) if '.' in x else int(x))
        
        self.logger.info(f"Aggregated {len(aggregated['results_by_version'])} version results")
        return aggregated
    
    def _generate_html(self, data: Dict[str, Any]) -> str:
        """
        Generate complete HTML content.
        
        Args:
            data: Aggregated data dictionary
            
        Returns:
            Complete HTML document string
        """
        metadata = data.get('test_metadata', {})
        results_by_version = data.get('results_by_version', {})
        
        # Generate sections based on report style
        header_html = self._generate_header(metadata, len(results_by_version))
        
        if self.report_style == 'dimension-based':
            # Dimension-based report
            overview_html = get_multi_version_dimension_overview_html(results_by_version)
            charts_html = self._generate_dimension_charts(results_by_version)
            details_html = self._generate_dimension_sections(results_by_version)
        else:
            # Tool-based report (default)
            overview_html = self._generate_version_grid(results_by_version)
            charts_html = self._generate_charts(results_by_version)
            details_html = self._generate_version_details(results_by_version)
        
        # Generate analysis section (includes version comparisons)
        analysis_html = self._generate_analysis_section(data)
        
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
        title = "NFS Benchmark Suite - Multi-Version Report"
        if self.report_style == 'dimension-based':
            title += " - Dimension View"
        return get_base_template(title, content)
    
    def _generate_header(self, metadata: Dict[str, Any], num_versions: int) -> str:
        """
        Generate report header with test metadata.
        
        Args:
            metadata: Test metadata (from test_metadata field in JSON)
            num_versions: Number of versions tested
            
        Returns:
            Header HTML string
        """
        title = "NFS Benchmark Suite"
        subtitle = "Multi-Version Performance Report"
        
        # Pass all metadata and add version count
        display_metadata = metadata.copy() if metadata else {}
        display_metadata['versions_count'] = f"{num_versions} versions tested"
        
        return get_header_html(title, subtitle, display_metadata)
    
    def _generate_version_grid(self, results_by_version: Dict[str, Dict]) -> str:
        """
        Generate version comparison grid.
        
        Args:
            results_by_version: Results organized by version
            
        Returns:
            Version grid HTML string
        """
        grid_html = '<div class="version-grid">'
        
        for version_key in sorted(results_by_version.keys()):
            version_results = results_by_version[version_key]
            test_results = extract_test_results(version_results)
            
            # Count tests
            total_tests = 0
            passed_tests = 0
            
            for category, tests in test_results.items():
                if category in ['test_run', 'summary', 'nfs_stats']:
                    continue
                if isinstance(tests, dict):
                    for test_name, test_data in tests.items():
                        if isinstance(test_data, dict):
                            total_tests += 1
                            if test_data.get('status') == 'passed':
                                passed_tests += 1
            
            version_metadata = {
                'tests_passed': passed_tests,
                'tests_failed': total_tests - passed_tests,
            }
            
            grid_html += get_version_card_html(
                version_key.replace('_', ' ').upper(),
                version_metadata
            )
        
        grid_html += '</div>'
        
        return get_section_html("📊 Version Comparison", grid_html)
    
    def _generate_charts(self, results_by_version: Dict[str, Dict]) -> str:
        """
        Generate multi-version comparison charts.
        
        Args:
            results_by_version: Results organized by version
            
        Returns:
            Charts HTML string
        """
        if not self.chart_generator.plotly_available:
            return get_section_html(
                "📊 Performance Charts",
                "<p>Charts not available. Install plotly: pip3 install plotly</p>"
            )
        
        return self.chart_generator.generate_all_multi_version_charts(results_by_version)
    
    def _generate_version_details(self, results_by_version: Dict[str, Dict]) -> str:
        """
        Generate detailed results for each version.
        
        Args:
            results_by_version: Results organized by version
            
        Returns:
            Version details HTML string
        """
        details_html = ""
        
        for version_key in sorted(results_by_version.keys()):
            version_results = results_by_version[version_key]
            test_results = extract_test_results(version_results)
            
            # Generate summary for this version
            version_summary = self._generate_version_summary(version_key, test_results)
            details_html += get_section_html(
                f"{version_key.replace('_', ' ').upper()} - Test Summary",
                version_summary
            )
        
        return details_html
    
    def _generate_version_summary(self, version_key: str, 
                                  test_results: Dict[str, Dict]) -> str:
        """
        Generate summary for a single version.
        
        Args:
            version_key: Version identifier
            test_results: Test results for this version
            
        Returns:
            Summary HTML string
        """
        summary_html = "<table><thead><tr><th>Test Category</th><th>Tests Passed</th><th>Tests Failed</th></tr></thead><tbody>"
        
        categories = {
            'dd_tests': 'DD Tests',
            'fio_tests': 'FIO Tests',
            'iozone_tests': 'IOzone Tests',
            'bonnie_tests': 'Bonnie++ Tests',
            'dbench_tests': 'DBench Tests',
        }
        
        for category_key, category_name in categories.items():
            tests = test_results.get(category_key, {})
            if tests:
                passed = sum(1 for t in tests.values() if isinstance(t, dict) and t.get('status') == 'passed')
                failed = sum(1 for t in tests.values() if isinstance(t, dict) and t.get('status') == 'failed')
                
                row_class = 'success' if failed == 0 else 'warning' if passed > 0 else 'critical'
                summary_html += f'<tr class="{row_class}"><td><strong>{category_name}</strong></td><td>{passed}</td><td>{failed}</td></tr>'
        
        summary_html += "</tbody></table>"
        
        return summary_html
    
    def _generate_dimension_charts(self, results_by_version: Dict[str, Dict]) -> str:
        """
        Generate dimension-based performance charts for multi-version report.
        
        Args:
            results_by_version: Results organized by NFS version
            
        Returns:
            Charts HTML string
        """
        if not self.chart_generator.plotly_available:
            return get_section_html(
                "📊 Performance Charts",
                "<p>Charts not available. Install plotly: pip3 install plotly</p>"
            )
        
        return self.chart_generator.generate_all_multi_version_dimension_charts(results_by_version)
    
    def _generate_dimension_sections(self, results_by_version: Dict[str, Dict]) -> str:
        """
        Generate test result sections organized by performance dimension.
        
        Args:
            results_by_version: Results organized by NFS version
            
        Returns:
            Dimension sections HTML string
        """
        sections_html = ""
        
        # Generate a section for each dimension
        for dimension_key in dimension_mapper.get_all_dimensions():
            # Check if any version has data for this dimension
            has_data = False
            for version_results in results_by_version.values():
                dimension_data = dimension_mapper.extract_dimension_data(version_results, dimension_key)
                if dimension_data:
                    has_data = True
                    break
            
            if not has_data:
                continue
            
            # Get chart for this dimension
            chart_html = ""
            if self.chart_generator.plotly_available:
                if dimension_key == 'throughput':
                    chart_html = self.chart_generator.create_multi_version_dimension_throughput_chart(results_by_version)
                elif dimension_key == 'iops':
                    chart_html = self.chart_generator.create_multi_version_dimension_iops_chart(results_by_version)
                elif dimension_key == 'latency':
                    chart_html = self.chart_generator.create_multi_version_dimension_latency_chart(results_by_version)
            
            # Generate section with chart and comparison table
            sections_html += get_multi_version_dimension_section_html(
                dimension_key,
                results_by_version,
                chart_html or ""
            )
        
    
    def _generate_analysis_section(self, data: Dict[str, Any]) -> str:
        """
        Generate workload-category-based analysis for multi-version reports.
        Shows best NFS version per workload category in a table format.
        """
        if not self.enable_analysis:
            return ""
        
        try:
            results_by_version = data.get('results_by_version', {})
            
            if not results_by_version:
                return ""
            
            # Generate workload-category-based analysis
            analysis_html = self._generate_workload_category_analysis(results_by_version)
            
            return analysis_html
            
        except Exception as e:
            self.logger.error(f"Multi-version analysis failed: {e}", exc_info=True)
            from .templates import get_analysis_error_html
            return get_analysis_error_html(str(e))
    
    def _generate_workload_category_analysis(self, results_by_version: Dict[str, Dict]) -> str:
        """
        Generate workload-category-based performance analysis.
        
        Args:
            results_by_version: Results organized by version
            
        Returns:
            Analysis HTML with workload category table
        """
        # Extract version metrics
        versions_data = {}
        for version_key, version_data in results_by_version.items():
            # Parse nfs_version and transport from version_key
            parts = version_key.rsplit('_', 1)
            if len(parts) == 2:
                nfs_version, transport = parts
            else:
                nfs_version = version_key
                transport = 'tcp'
            
            # Extract metrics
            metrics = self._extract_version_metrics_for_analysis(version_data)
            
            versions_data[version_key] = {
                'nfs_version': nfs_version,
                'transport': transport,
                'metrics': metrics
            }
        
        if len(versions_data) < 2:
            return ""
        
        # Analyze workload categories
        category_insights = self._analyze_categories(versions_data)
        
        # Generate HTML
        from .templates import get_multi_version_workload_analysis_html
        return get_multi_version_workload_analysis_html(category_insights, self.test_id)
    
    def _analyze_categories(self, versions_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """
        Analyze performance by workload category across versions.
        
        Args:
            versions_data: Dictionary of version data with metrics
            
        Returns:
            List of category insights
        """
        from ..performance_analyzer import ComparisonAnalyzer
        
        # Create a temporary analyzer to use its helper methods
        temp_analyzer = ComparisonAnalyzer(
            testid1_name=self.test_id,
            testid2_name=self.test_id,
            testid1_versions=versions_data,
            testid2_versions={}
        )
        
        # Group metrics by category across all versions
        category_metrics = {}  # {category: {metric: {version: value}}}
        
        for version_key, version_data in versions_data.items():
            nfs_version = version_data['nfs_version']
            for metric, value in version_data['metrics'].items():
                category = temp_analyzer._get_metric_category(metric)
                
                if category not in category_metrics:
                    category_metrics[category] = {}
                if metric not in category_metrics[category]:
                    category_metrics[category][metric] = {}
                
                category_metrics[category][metric][nfs_version] = value
        
        # For each category, find best performing version
        insights = []
        for category in sorted(category_metrics.keys()):
            if category == 'Other':
                continue
            
            # Calculate average performance per version for this category
            version_avgs = {}
            for metric, version_values in category_metrics[category].items():
                for version, value in version_values.items():
                    if version not in version_avgs:
                        version_avgs[version] = []
                    version_avgs[version].append(value)
            
            # Calculate averages
            version_scores = {}
            for version, values in version_avgs.items():
                version_scores[version] = sum(values) / len(values) if values else 0
            
            if not version_scores:
                continue
            
            # Find best and worst
            sorted_versions = sorted(version_scores.items(), key=lambda x: x[1], reverse=True)
            best_version = sorted_versions[0][0]
            worst_version = sorted_versions[-1][0]
            
            # Calculate improvement percentage
            best_score = sorted_versions[0][1]
            worst_score = sorted_versions[-1][1]
            improvement_pct = ((best_score - worst_score) / worst_score * 100) if worst_score > 0 else 0
            
            # Create ranking
            ranking = [v[0] for v in sorted_versions]
            
            insights.append({
                'category': category,
                'best_version': best_version,
                'improvement_pct': improvement_pct,
                'ranking': ranking
            })
        
        return insights
    
    def _extract_version_metrics_for_analysis(self, version_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract metrics from version data for workload category analysis.
        
        Args:
            version_data: Single version's test results
            
        Returns:
            Dictionary of metric_name -> value
        """
        metrics = {}
        
        # Extract FIO metrics
        fio_tests = version_data.get('fio_tests', {})
        for test_name, test_data in fio_tests.items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                if 'read_bandwidth_mbps' in test_data and test_data['read_bandwidth_mbps'] > 0:
                    metrics[f'fio_{test_name}_read_mbps'] = test_data['read_bandwidth_mbps']
                if 'write_bandwidth_mbps' in test_data and test_data['write_bandwidth_mbps'] > 0:
                    metrics[f'fio_{test_name}_write_mbps'] = test_data['write_bandwidth_mbps']
                if 'read_iops' in test_data and test_data['read_iops'] > 0:
                    metrics[f'fio_{test_name}_read_iops'] = test_data['read_iops']
                if 'write_iops' in test_data and test_data['write_iops'] > 0:
                    metrics[f'fio_{test_name}_write_iops'] = test_data['write_iops']
        
        # Extract IOzone metrics
        iozone_tests = version_data.get('iozone_tests', {})
        for test_name, test_data in iozone_tests.items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                if 'read_throughput_mbps' in test_data and test_data['read_throughput_mbps'] > 0:
                    metrics[f'iozone_{test_name}_read_mbps'] = test_data['read_throughput_mbps']
                if 'write_throughput_mbps' in test_data and test_data['write_throughput_mbps'] > 0:
                    metrics[f'iozone_{test_name}_write_mbps'] = test_data['write_throughput_mbps']
        
        # Extract DBench metrics
        dbench_tests = version_data.get('dbench_tests', {})
        for test_name, test_data in dbench_tests.items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                if 'throughput_mbps' in test_data and test_data['throughput_mbps'] > 0:
                    metrics[f'dbench_{test_name}_mbps'] = test_data['throughput_mbps']
        
        # Extract Bonnie++ metrics
        bonnie_tests = version_data.get('bonnie_tests', {})
        for test_name, test_data in bonnie_tests.items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                if 'sequential_output_block_mbps' in test_data and test_data['sequential_output_block_mbps'] > 0:
                    metrics[f'bonnie_{test_name}_seq_out'] = test_data['sequential_output_block_mbps']
                if 'sequential_input_block_mbps' in test_data and test_data['sequential_input_block_mbps'] > 0:
                    metrics[f'bonnie_{test_name}_seq_in'] = test_data['sequential_input_block_mbps']
        
        # Extract DD metrics
        dd_tests = version_data.get('dd_tests', {})
        for test_name, test_data in dd_tests.items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                if 'throughput_mbps' in test_data and test_data['throughput_mbps'] > 0:
                    metrics[f'dd_{test_name}_mbps'] = test_data['throughput_mbps']
        
        return metrics
        return sections_html

# Made with Bob
