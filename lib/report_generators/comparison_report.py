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
    get_section_html,
    get_comparison_grid_html,
)
from .charts import ChartGenerator


logger = logging.getLogger(__name__)


class ComparisonReportGenerator(BaseReportGenerator):
    """
    Generate HTML report comparing two different test-ids.
    
    This generator loads results for two test-ids and creates a side-by-side
    comparison report. Useful for evaluating changes between different
    configurations, OS versions, or software versions.
    """
    
    def __init__(self, test_id_1: str, test_id_2: str,
                 directory: Path = None, output_dir: Path = None, report_style: str = 'tool-based'):
        """
        Initialize comparison report generator.
        
        Args:
            test_id_1: First test identifier
            test_id_2: Second test identifier
            directory: Directory to search for JSON files (default: current directory)
            output_dir: Optional output directory (default: ./report)
            report_style: Report organization style - 'tool-based' or 'dimension-based' (default: 'tool-based')
        
        Note:
            Dimension-based reporting is currently only supported for single-file reports.
            Comparison reports will use tool-based style regardless of this parameter.
        """
        super().__init__(output_dir, report_style)
        self.test_id_1 = test_id_1
        self.test_id_2 = test_id_2
        self.directory = Path(directory) if directory else Path(".")
        self.chart_generator = ChartGenerator()
        
        # Log warning if dimension-based style requested
        if report_style == 'dimension-based':
            self.logger.warning(
                "Dimension-based reporting is not yet implemented for comparison reports. "
                "Using tool-based style instead."
            )
            self.report_style = 'tool-based'
    
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
        
        # Generate sections
        header_html = self._generate_header(test_id_1, test_id_2)
        comparison_grid_html = self._generate_comparison_grid(
            test_id_1, test_id_2, results_1, results_2
        )
        charts_html = self._generate_comparison_charts(results_1, results_2)
        details_html = self._generate_comparison_details(
            test_id_1, test_id_2, results_1, results_2
        )
        
        # Combine all sections
        content = f"""
        <div class="container">
            {header_html}
            {comparison_grid_html}
            {charts_html}
            {details_html}
        </div>
        """
        
        # Wrap in base template
        return get_base_template("NFS Benchmark Suite - Test-ID Comparison", content)
    
    def _generate_header(self, test_id_1: str, test_id_2: str) -> str:
        """
        Generate report header.
        
        Args:
            test_id_1: First test ID
            test_id_2: Second test ID
            
        Returns:
            Header HTML string
        """
        title = "NFS Benchmark Suite"
        subtitle = "Test-ID Comparison Report"
        
        display_metadata = {
            'comparison': f"{test_id_1} vs {test_id_2}",
        }
        
        return get_header_html(title, subtitle, display_metadata)
    
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

# Made with Bob
