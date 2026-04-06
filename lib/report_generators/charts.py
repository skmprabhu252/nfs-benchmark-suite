#!/usr/bin/env python3
"""
Chart generation utilities for HTML reports

Provides Plotly chart generation for all benchmark types with proper
NFSv3-only filtering for dbench and correct field names for all tests.
Includes dimension-based chart generation for organizing results by
performance dimensions rather than tools.
"""

import logging
from typing import Dict, Any, List, Optional

from . import dimension_mapper

logger = logging.getLogger(__name__)

# Check for Plotly availability
try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly not available. Charts will not be generated.")


class ChartGenerator:
    """
    Generates Plotly charts for benchmark results.
    
    Handles single-version and multi-version chart generation with
    proper data extraction and formatting.
    """
    
    def __init__(self):
        """Initialize chart generator."""
        self.plotly_available = PLOTLY_AVAILABLE
    
    def create_dd_chart(self, dd_tests: Dict[str, Any]) -> Optional[str]:
        """
        Create DD throughput chart.
        
        Args:
            dd_tests: DD test results dictionary
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available or not dd_tests:
            return None
        
        names = []
        throughputs = []
        
        for test_name, test_data in dd_tests.items():
            if test_data.get('status') == 'passed':
                names.append(test_name.replace('_', ' ').title())
                throughputs.append(test_data.get('throughput_mbps', 0))
        
        if not names:
            return None
        
        fig = go.Figure(data=[
            go.Bar(x=names, y=throughputs, marker_color='#667eea')
        ])
        fig.update_layout(
            title={
                'text': 'DD Test Throughput',
                'font': {'size': 20, 'color': '#1f2937', 'family': 'Arial, sans-serif'},
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Test Name',
            yaxis_title='Throughput (MB/s)',
            height=400
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_fio_chart(self, fio_tests: Dict[str, Any]) -> Optional[str]:
        """
        Create FIO IOPS chart.
        
        Args:
            fio_tests: FIO test results dictionary
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available or not fio_tests:
            return None
        
        names = []
        read_iops = []
        write_iops = []
        
        for test_name, test_data in fio_tests.items():
            if test_data.get('status') == 'passed':
                names.append(test_name.replace('_', ' ').title())
                read_iops.append(test_data.get('read_iops', 0))
                write_iops.append(test_data.get('write_iops', 0))
        
        if not names:
            return None
        
        fig = go.Figure(data=[
            go.Bar(name='Read IOPS', x=names, y=read_iops, marker_color='#10b981'),
            go.Bar(name='Write IOPS', x=names, y=write_iops, marker_color='#ef4444')
        ])
        fig.update_layout(
            title={
                'text': 'FIO Test IOPS',
                'font': {'size': 20, 'color': '#1f2937', 'family': 'Arial, sans-serif'},
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Test Name',
            yaxis_title='IOPS',
            barmode='group',
            height=400
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_iozone_chart(self, iozone_tests: Dict[str, Any]) -> Optional[str]:
        """
        Create IOzone throughput chart.
        
        Args:
            iozone_tests: IOzone test results dictionary
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available or not iozone_tests:
            return None
        
        names = []
        read_throughputs = []
        write_throughputs = []
        
        for test_name, test_data in iozone_tests.items():
            if test_data.get('status') == 'passed':
                if test_name == 'scaling_test':
                    scaling_results = test_data.get('scaling_results', {})
                    for thread_name, thread_data in scaling_results.items():
                        read_tp = thread_data.get('read_throughput_mbps', 0)
                        write_tp = thread_data.get('write_throughput_mbps', 0)
                        # Only add if there's actual throughput data
                        if read_tp > 0 or write_tp > 0:
                            names.append(f"Scaling {thread_name}")
                            read_throughputs.append(read_tp)
                            write_throughputs.append(write_tp)
                else:
                    read_tp = test_data.get('read_throughput_mbps', 0)
                    write_tp = test_data.get('write_throughput_mbps', 0)
                    # Only add if there's actual throughput data (skip tests with parsing failures)
                    if read_tp > 0 or write_tp > 0:
                        names.append(test_name.replace('_', ' ').title())
                        read_throughputs.append(read_tp)
                        write_throughputs.append(write_tp)
        
        if not names:
            return None
        
        fig = go.Figure(data=[
            go.Bar(name='Read', x=names, y=read_throughputs, marker_color='#10b981'),
            go.Bar(name='Write', x=names, y=write_throughputs, marker_color='#3b82f6')
        ])
        fig.update_layout(
            title='IOzone Test Throughput',
            xaxis_title='Test Name',
            yaxis_title='Throughput (MB/s)',
            barmode='group',
            height=400
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_bonnie_throughput_chart(self, bonnie_tests: Dict[str, Any]) -> Optional[str]:
        """
        Create Bonnie++ throughput chart.
        
        Args:
            bonnie_tests: Bonnie++ test results dictionary
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available or not bonnie_tests:
            return None
        
        names = []
        output_throughputs = []
        input_throughputs = []
        
        for test_name, test_data in bonnie_tests.items():
            if test_data.get('status') == 'passed':
                names.append(test_name.replace('_', ' ').title())
                # Use correct field names
                output_throughputs.append(test_data.get('sequential_output_block_mbps', 0))
                input_throughputs.append(test_data.get('sequential_input_block_mbps', 0))
        
        if not names:
            return None
        
        fig = go.Figure(data=[
            go.Bar(name='Write (Sequential Output)', x=names, y=output_throughputs, marker_color='#3b82f6'),
            go.Bar(name='Read (Sequential Input)', x=names, y=input_throughputs, marker_color='#10b981')
        ])
        fig.update_layout(
            title='Bonnie++ Sequential Block Throughput',
            xaxis_title='Test Name',
            yaxis_title='Throughput (MB/s)',
            barmode='group',
            height=400
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_bonnie_file_ops_chart(self, bonnie_tests: Dict[str, Any]) -> Optional[str]:
        """
        Create Bonnie++ file operations chart.
        
        Args:
            bonnie_tests: Bonnie++ test results dictionary
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available or not bonnie_tests:
            return None
        
        names = []
        create_ops = []
        delete_ops = []
        
        for test_name, test_data in bonnie_tests.items():
            if test_data.get('status') == 'passed' and 'file_create_seq_per_sec' in test_data:
                names.append(test_name.replace('_', ' ').title())
                # Use correct field names
                create_ops.append(test_data.get('file_create_seq_per_sec', 0))
                delete_ops.append(test_data.get('file_delete_seq_per_sec', 0))
        
        if not names:
            return None
        
        fig = go.Figure(data=[
            go.Bar(name='Create', x=names, y=create_ops, marker_color='#10b981'),
            go.Bar(name='Delete', x=names, y=delete_ops, marker_color='#ef4444')
        ])
        fig.update_layout(
            title='Bonnie++ File Operations',
            xaxis_title='Test Name',
            yaxis_title='Operations (files/sec)',
            barmode='group',
            height=400
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_dbench_chart(self, dbench_tests: Dict[str, Any]) -> Optional[str]:
        """
        Create DBench throughput chart.
        
        Args:
            dbench_tests: DBench test results dictionary
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available or not dbench_tests:
            return None
        
        names = []
        throughputs = []
        
        for test_name, test_data in dbench_tests.items():
            if test_data.get('status') == 'passed':
                if test_name == 'scalability_test' and 'results' in test_data:
                    # Scalability test has nested results by client count
                    for client_count, client_data in test_data['results'].items():
                        num_clients = client_data.get('num_clients', client_count)
                        names.append(f"{num_clients} clients")
                        throughputs.append(client_data.get('throughput_mbps', 0))
                else:
                    names.append(test_name.replace('_', ' ').title())
                    throughputs.append(test_data.get('throughput_mbps', 0))
        
        if not names:
            return None
        
        fig = go.Figure(data=[
            go.Bar(x=names, y=throughputs, marker_color='#ec4899')
        ])
        fig.update_layout(
            title='DBench Test Throughput',
            xaxis_title='Test Name',
            yaxis_title='Throughput (MB/s)',
            height=400
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_multi_version_dd_chart(self, results_by_version: Dict[str, Dict]) -> Optional[str]:
        """
        Create multi-version DD comparison chart.
        
        Args:
            results_by_version: Results organized by NFS version
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available:
            return None
        
        versions = sorted(results_by_version.keys())
        dd_data = {}
        
        for version_key, version_results in results_by_version.items():
            dd_tests = version_results.get('dd_tests', {})
            for test_name, test_data in dd_tests.items():
                if test_data.get('status') == 'passed':
                    if test_name not in dd_data:
                        dd_data[test_name] = {}
                    dd_data[test_name][version_key] = test_data.get('throughput_mbps', 0)
        
        if not dd_data:
            return None
        
        fig = go.Figure()
        for version_key in versions:
            test_names = []
            throughputs = []
            for test_name in dd_data.keys():
                if version_key in dd_data[test_name]:
                    test_names.append(test_name.replace('_', ' ').title())
                    throughputs.append(dd_data[test_name][version_key])
            
            if test_names:
                fig.add_trace(go.Bar(
                    name=version_key.replace('_', ' ').upper(),
                    x=test_names,
                    y=throughputs
                ))
        
        fig.update_layout(
            title='DD Test Throughput Comparison',
            xaxis_title='Test Name',
            yaxis_title='Throughput (MB/s)',
            barmode='group',
            height=400
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_multi_version_fio_chart(self, results_by_version: Dict[str, Dict]) -> Optional[str]:
        """
        Create multi-version FIO comparison chart.
        
        Args:
            results_by_version: Results organized by NFS version
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available:
            return None
        
        versions = sorted(results_by_version.keys())
        fio_read_data = {}
        fio_write_data = {}
        
        for version_key, version_results in results_by_version.items():
            fio_tests = version_results.get('fio_tests', {})
            for test_name, test_data in fio_tests.items():
                if test_data.get('status') == 'passed':
                    if test_name not in fio_read_data:
                        fio_read_data[test_name] = {}
                        fio_write_data[test_name] = {}
                    fio_read_data[test_name][version_key] = test_data.get('read_iops', 0)
                    fio_write_data[test_name][version_key] = test_data.get('write_iops', 0)
        
        if not fio_read_data:
            return None
        
        fig = go.Figure()
        for version_key in versions:
            test_names = []
            read_iops = []
            write_iops = []
            for test_name in fio_read_data.keys():
                if version_key in fio_read_data[test_name]:
                    test_names.append(test_name.replace('_', ' ').title())
                    read_iops.append(fio_read_data[test_name][version_key])
                    write_iops.append(fio_write_data[test_name][version_key])
            
            if test_names:
                fig.add_trace(go.Bar(
                    name=f'{version_key.replace("_", " ").upper()} Read',
                    x=test_names,
                    y=read_iops
                ))
                fig.add_trace(go.Bar(
                    name=f'{version_key.replace("_", " ").upper()} Write',
                    x=test_names,
                    y=write_iops
                ))
        
        fig.update_layout(
            title='FIO Test IOPS Comparison',
            xaxis_title='Test Name',
            yaxis_title='IOPS',
            barmode='group',
            height=400
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_multi_version_dbench_chart(self, results_by_version: Dict[str, Dict]) -> Optional[str]:
        """
        Create multi-version DBench comparison chart (NFSv3 only).
        
        Args:
            results_by_version: Results organized by NFS version
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available:
            return None
        
        # Filter to NFSv3 only
        nfsv3_versions = {k: v for k, v in results_by_version.items() 
                         if 'nfsv3' in k.lower()}
        
        if not nfsv3_versions:
            return None
        
        versions = sorted(nfsv3_versions.keys())
        dbench_data = {}
        
        for version_key, version_results in nfsv3_versions.items():
            dbench_tests = version_results.get('dbench_tests', {})
            for test_name, test_data in dbench_tests.items():
                if test_data.get('status') == 'passed':
                    if test_name not in dbench_data:
                        dbench_data[test_name] = {}
                    dbench_data[test_name][version_key] = test_data.get('throughput_mbps', 0)
        
        if not dbench_data:
            return None
        
        fig = go.Figure()
        for version_key in versions:
            test_names = []
            throughputs = []
            for test_name in dbench_data.keys():
                if version_key in dbench_data[test_name]:
                    test_names.append(test_name.replace('_', ' ').title())
                    throughputs.append(dbench_data[test_name][version_key])
            
            if test_names:
                fig.add_trace(go.Bar(
                    name=version_key.replace('_', ' ').upper(),
                    x=test_names,
                    y=throughputs
                ))
        
        fig.update_layout(
            title='DBench Test Throughput Comparison (NFSv3 Only)',
            xaxis_title='Test Name',
            yaxis_title='Throughput (MB/s)',
            barmode='group',
            height=400
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_multi_version_iozone_chart(self, results_by_version: Dict[str, Dict]) -> Optional[str]:
        """
        Create multi-version IOzone comparison chart showing write and read throughput.
        
        Args:
            results_by_version: Results organized by NFS version
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available:
            return None
        
        versions = sorted(results_by_version.keys())
        
        # Collect data for each test and metric type
        test_names_set = set()
        write_data = {}  # {test_name: {version: value}}
        read_data = {}   # {test_name: {version: value}}
        
        for version_key, version_results in results_by_version.items():
            iozone_tests = version_results.get('iozone_tests', {})
            for test_name, test_data in iozone_tests.items():
                if test_data.get('status') == 'passed':
                    test_names_set.add(test_name)
                    
                    # Get write throughput
                    write_tp = test_data.get('write_throughput_mbps', 0)
                    if write_tp > 0:
                        if test_name not in write_data:
                            write_data[test_name] = {}
                        write_data[test_name][version_key] = write_tp
                    
                    # Get read throughput
                    read_tp = test_data.get('read_throughput_mbps', 0)
                    if read_tp > 0:
                        if test_name not in read_data:
                            read_data[test_name] = {}
                        read_data[test_name][version_key] = read_tp
        
        if not test_names_set:
            return None
        
        test_names = sorted(test_names_set)
        
        fig = go.Figure()
        
        # Add write throughput traces
        for version_key in versions:
            write_values = []
            x_labels = []
            for test_name in test_names:
                if test_name in write_data and version_key in write_data[test_name]:
                    x_labels.append(f"{test_name.replace('_', ' ').title()} (Write)")
                    write_values.append(write_data[test_name][version_key])
            
            if x_labels:
                fig.add_trace(go.Bar(
                    name=f"{version_key.replace('_', ' ').upper()} Write",
                    x=x_labels,
                    y=write_values,
                    marker_color='#3b82f6'
                ))
        
        # Add read throughput traces
        for version_key in versions:
            read_values = []
            x_labels = []
            for test_name in test_names:
                if test_name in read_data and version_key in read_data[test_name]:
                    x_labels.append(f"{test_name.replace('_', ' ').title()} (Read)")
                    read_values.append(read_data[test_name][version_key])
            
            if x_labels:
                fig.add_trace(go.Bar(
                    name=f"{version_key.replace('_', ' ').upper()} Read",
                    x=x_labels,
                    y=read_values,
                    marker_color='#10b981'
                ))
        
        fig.update_layout(
            title='IOzone Test Throughput Comparison (Write & Read)',
            xaxis_title='Test Name',
            yaxis_title='Throughput (MB/s)',
            barmode='group',
            height=400
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_multi_version_bonnie_chart(self, results_by_version: Dict[str, Dict]) -> Optional[str]:
        """
        Create multi-version Bonnie++ comparison chart showing both output and input throughput.
        
        Args:
            results_by_version: Results organized by NFS version
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available:
            return None
        
        versions = sorted(results_by_version.keys())
        
        # Collect data for each test and metric type
        test_names_set = set()
        output_data = {}  # {test_name: {version: value}}
        input_data = {}   # {test_name: {version: value}}
        
        for version_key, version_results in results_by_version.items():
            bonnie_tests = version_results.get('bonnie_tests', {})
            for test_name, test_data in bonnie_tests.items():
                if test_data.get('status') == 'passed':
                    test_names_set.add(test_name)
                    
                    # Get output throughput
                    output_tp = test_data.get('sequential_output_block_mbps', 0)
                    if output_tp >= 0:  # Include zero values
                        if test_name not in output_data:
                            output_data[test_name] = {}
                        output_data[test_name][version_key] = output_tp
                    
                    # Get input throughput
                    input_tp = test_data.get('sequential_input_block_mbps', 0)
                    if input_tp >= 0:  # Include zero values
                        if test_name not in input_data:
                            input_data[test_name] = {}
                        input_data[test_name][version_key] = input_tp
        
        if not test_names_set:
            return None
        
        test_names = sorted(test_names_set)
        
        fig = go.Figure()
        
        # Add write throughput traces (sequential output)
        for version_key in versions:
            output_values = []
            x_labels = []
            for test_name in test_names:
                if test_name in output_data and version_key in output_data[test_name]:
                    x_labels.append(f"{test_name.replace('_', ' ').title()} (Write)")
                    output_values.append(output_data[test_name][version_key])
            
            if x_labels:
                fig.add_trace(go.Bar(
                    name=f"{version_key.replace('_', ' ').upper()} Write",
                    x=x_labels,
                    y=output_values,
                    marker_color='#3b82f6'
                ))
        
        # Add read throughput traces (sequential input)
        for version_key in versions:
            input_values = []
            x_labels = []
            for test_name in test_names:
                if test_name in input_data and version_key in input_data[test_name]:
                    x_labels.append(f"{test_name.replace('_', ' ').title()} (Read)")
                    input_values.append(input_data[test_name][version_key])
            
            if x_labels:
                fig.add_trace(go.Bar(
                    name=f"{version_key.replace('_', ' ').upper()} Read",
                    x=x_labels,
                    y=input_values,
                    marker_color='#10b981'
                ))
        
        fig.update_layout(
            title='Bonnie++ Sequential Block Throughput Comparison (Write & Read)',
            xaxis_title='Test Name',
            yaxis_title='Throughput (MB/s)',
            barmode='group',
            height=400
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def generate_all_single_version_charts(self, test_results: Dict[str, Dict]) -> str:
        """
        Generate all charts for single-version report.
        
        Args:
            test_results: Dictionary of test results by category
            
        Returns:
            HTML string with all charts
        """
        if not self.plotly_available:
            return ""
        
        charts_html = '<div class="section"><h2>📊 Performance Charts</h2>'
        
        # DD chart
        dd_chart = self.create_dd_chart(test_results.get('dd_tests', {}))
        if dd_chart:
            charts_html += f'<div class="chart-container">{dd_chart}</div>'
        
        # FIO chart
        fio_chart = self.create_fio_chart(test_results.get('fio_tests', {}))
        if fio_chart:
            charts_html += f'<div class="chart-container">{fio_chart}</div>'
        
        # IOzone chart
        iozone_chart = self.create_iozone_chart(test_results.get('iozone_tests', {}))
        if iozone_chart:
            charts_html += f'<div class="chart-container">{iozone_chart}</div>'
        
        # Bonnie++ charts
        bonnie_tp_chart = self.create_bonnie_throughput_chart(test_results.get('bonnie_tests', {}))
        if bonnie_tp_chart:
            charts_html += f'<div class="chart-container">{bonnie_tp_chart}</div>'
        
        bonnie_ops_chart = self.create_bonnie_file_ops_chart(test_results.get('bonnie_tests', {}))
        if bonnie_ops_chart:
            charts_html += f'<div class="chart-container">{bonnie_ops_chart}</div>'
        
        # DBench chart
        dbench_chart = self.create_dbench_chart(test_results.get('dbench_tests', {}))
        if dbench_chart:
            charts_html += f'<div class="chart-container">{dbench_chart}</div>'
        
        charts_html += '</div>'
        return charts_html
    
    def generate_all_multi_version_charts(self, results_by_version: Dict[str, Dict]) -> str:
        """
        Generate all charts for multi-version report.
        
        Args:
            results_by_version: Results organized by NFS version or test-id_version
            
        Returns:
            HTML string with all charts
        """
        if not self.plotly_available:
            return ""
        
        # Check if this is a comparison (keys contain test-id prefix)
        is_comparison = any('_nfsv' in key for key in results_by_version.keys())
        
        if is_comparison:
            return self.generate_comparison_charts(results_by_version)
        
        charts_html = '<div class="section"><h2>📊 Multi-Version Performance Comparison</h2>'
        
        # DD comparison
        dd_chart = self.create_multi_version_dd_chart(results_by_version)
        if dd_chart:
            charts_html += f'<div class="chart-container">{dd_chart}</div>'
        
        # FIO comparison
        fio_chart = self.create_multi_version_fio_chart(results_by_version)
        if fio_chart:
            charts_html += f'<div class="chart-container">{fio_chart}</div>'
        
        # IOzone comparison
        iozone_chart = self.create_multi_version_iozone_chart(results_by_version)
        if iozone_chart:
            charts_html += f'<div class="chart-container">{iozone_chart}</div>'
        
        # Bonnie++ comparison
        bonnie_chart = self.create_multi_version_bonnie_chart(results_by_version)
        if bonnie_chart:
            charts_html += f'<div class="chart-container">{bonnie_chart}</div>'
        
        # DBench comparison (NFSv3 only)
        dbench_chart = self.create_multi_version_dbench_chart(results_by_version)
        if dbench_chart:
            charts_html += f'<div class="chart-container">{dbench_chart}</div>'
        
        charts_html += '</div>'
        return charts_html
    
    def generate_comparison_charts(self, combined_results: Dict[str, Dict]) -> str:
        """
        Generate charts for test-id comparison reports.
        
        Args:
            combined_results: Results with keys like 'testid_nfsv3_tcp'
            
        Returns:
            HTML string with comparison charts
        """
        charts_html = '<div class="section"><h2>📊 Test-ID Performance Comparison</h2>'
        
        # DD comparison
        dd_chart = self.create_comparison_dd_chart(combined_results)
        if dd_chart:
            charts_html += f'<div class="chart-container">{dd_chart}</div>'
        
        # FIO comparison
        fio_chart = self.create_comparison_fio_chart(combined_results)
        if fio_chart:
            charts_html += f'<div class="chart-container">{fio_chart}</div>'
        
        # IOzone comparison
        iozone_chart = self.create_comparison_iozone_chart(combined_results)
        if iozone_chart:
            charts_html += f'<div class="chart-container">{iozone_chart}</div>'
        
        # Bonnie++ comparison
        bonnie_chart = self.create_comparison_bonnie_chart(combined_results)
        if bonnie_chart:
            charts_html += f'<div class="chart-container">{bonnie_chart}</div>'
        
        # DBench comparison
        dbench_chart = self.create_comparison_dbench_chart(combined_results)
        if dbench_chart:
            charts_html += f'<div class="chart-container">{dbench_chart}</div>'
        
        charts_html += '</div>'
        return charts_html
    
    
    def create_comparison_dd_chart(self, combined_results: Dict[str, Dict]) -> Optional[str]:
        """
        Create DD throughput comparison chart for test-id comparison.
        
        Args:
            combined_results: Results with keys like 'testid_nfsv3_tcp'
            
        Returns:
            HTML string for chart or None
        """
        if not self.plotly_available:
            return None
        
        # Extract data organized by test-id and version
        data_by_test = {}
        
        for key, result in combined_results.items():
            # Parse key: testid_nfsv3_tcp or testid_nfsv4.1_rdma
            parts = key.split('_nfsv')
            if len(parts) != 2:
                continue
            
            test_id = parts[0]
            version_transport = 'nfsv' + parts[1]
            
            if test_id not in data_by_test:
                data_by_test[test_id] = {}
            
            dd_tests = result.get('dd_tests', {})
            if not dd_tests:
                continue
            
            # Get write throughput
            write_test = dd_tests.get('sequential_write_direct', {})
            write_tp = write_test.get('throughput_mbps', 0)
            
            # Get read throughput
            read_test = dd_tests.get('sequential_read_direct', {})
            read_tp = read_test.get('throughput_mbps', 0)
            
            data_by_test[test_id][version_transport] = {
                'write': write_tp,
                'read': read_tp
            }
        
        if not data_by_test:
            return None
        
        # Create grouped bar chart
        fig = go.Figure()
        
        # Extract NFS versions (without transport) for x-axis
        nfs_versions = set()
        for test_data in data_by_test.values():
            for version_transport in test_data.keys():
                # Extract just the version part (nfsv3, nfsv4.0, etc.)
                nfs_version = version_transport.split('_')[0]
                nfs_versions.add(nfs_version)
        nfs_versions = sorted(nfs_versions)
        
        # Add traces for each test-id
        colors = ['#667eea', '#f59e0b', '#10b981', '#ef4444']
        for idx, (test_id, test_data) in enumerate(sorted(data_by_test.items())):
            write_values = []
            read_values = []
            x_labels = []
            
            for nfs_version in nfs_versions:
                # Find matching version_transport for this test_id
                found = False
                for version_transport, metrics in test_data.items():
                    if version_transport.startswith(nfs_version):
                        write_values.append(metrics['write'])
                        read_values.append(metrics['read'])
                        # Extract transport for label
                        transport = version_transport.split('_')[1] if '_' in version_transport else 'tcp'
                        x_labels.append(f"{nfs_version.replace('nfsv', 'v')} ({transport.upper()})")
                        found = True
                        break
                
                if not found:
                    write_values.append(0)
                    read_values.append(0)
                    x_labels.append(f"{nfs_version.replace('nfsv', 'v')}")
            
            # Add write trace
            fig.add_trace(go.Bar(
                name=f'{test_id} Write',
                x=x_labels,
                y=write_values,
                marker_color=colors[idx % len(colors)],
                opacity=0.8
            ))
            
            # Add read trace
            fig.add_trace(go.Bar(
                name=f'{test_id} Read',
                x=x_labels,
                y=read_values,
                marker_color=colors[idx % len(colors)],
                opacity=0.5,
                marker_pattern_shape="/"
            ))
        
        fig.update_layout(
            title='DD Test Throughput Comparison (Write & Read)',
            xaxis_title='NFS Version (Transport)',
            yaxis_title='Throughput (MB/s)',
            barmode='group',
            height=400,
            margin=dict(t=60, b=50, l=50, r=150),
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02)
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_comparison_fio_chart(self, combined_results: Dict[str, Dict]) -> Optional[str]:
        """
        Create FIO IOPS comparison chart for test-id comparison.
        
        Args:
            combined_results: Results with keys like 'testid_nfsv3_tcp'
            
        Returns:
            HTML string for chart or None
        """
        if not self.plotly_available:
            return None
        
        # Extract data organized by test-id and version
        data_by_test = {}
        
        for key, result in combined_results.items():
            parts = key.split('_nfsv')
            if len(parts) != 2:
                continue
            
            test_id = parts[0]
            version_transport = 'nfsv' + parts[1]
            
            if test_id not in data_by_test:
                data_by_test[test_id] = {}
            
            fio_tests = result.get('fio_tests', {})
            if not fio_tests:
                continue
            
            # Get sequential read/write IOPS
            seq_read = fio_tests.get('sequential_read', {})
            seq_write = fio_tests.get('sequential_write', {})
            
            data_by_test[test_id][version_transport] = {
                'read_iops': seq_read.get('read_iops', 0),
                'write_iops': seq_write.get('write_iops', 0)
            }
        
        if not data_by_test:
            return None
        
        fig = go.Figure()
        
        # Extract NFS versions for x-axis
        nfs_versions = set()
        for test_data in data_by_test.values():
            for version_transport in test_data.keys():
                nfs_version = version_transport.split('_')[0]
                nfs_versions.add(nfs_version)
        nfs_versions = sorted(nfs_versions)
        
        colors = ['#10b981', '#ef4444', '#3b82f6', '#f59e0b']
        for idx, (test_id, test_data) in enumerate(sorted(data_by_test.items())):
            read_values = []
            write_values = []
            x_labels = []
            
            for nfs_version in nfs_versions:
                found = False
                for version_transport, metrics in test_data.items():
                    if version_transport.startswith(nfs_version):
                        read_values.append(metrics['read_iops'])
                        write_values.append(metrics['write_iops'])
                        transport = version_transport.split('_')[1] if '_' in version_transport else 'tcp'
                        x_labels.append(f"{nfs_version.replace('nfsv', 'v')} ({transport.upper()})")
                        found = True
                        break
                
                if not found:
                    read_values.append(0)
                    write_values.append(0)
                    x_labels.append(f"{nfs_version.replace('nfsv', 'v')}")
            
            fig.add_trace(go.Bar(
                name=f'{test_id} Read',
                x=x_labels,
                y=read_values,
                marker_color=colors[idx % len(colors)],
                opacity=0.8
            ))
            
            fig.add_trace(go.Bar(
                name=f'{test_id} Write',
                x=x_labels,
                y=write_values,
                marker_color=colors[idx % len(colors)],
                opacity=0.5,
                marker_pattern_shape="/"
            ))
        
        fig.update_layout(
            title='FIO Sequential IOPS Comparison (Read & Write)',
            xaxis_title='NFS Version (Transport)',
            yaxis_title='IOPS',
            barmode='group',
            height=400,
            margin=dict(t=60, b=50, l=50, r=150),
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02)
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_comparison_iozone_chart(self, combined_results: Dict[str, Dict]) -> Optional[str]:
        """
        Create IOzone throughput comparison chart for test-id comparison.
        
        Args:
            combined_results: Results with keys like 'testid_nfsv3_tcp'
            
        Returns:
            HTML string for chart or None
        """
        if not self.plotly_available:
            return None
        
        data_by_test = {}
        
        for key, result in combined_results.items():
            parts = key.split('_nfsv')
            if len(parts) != 2:
                continue
            
            test_id = parts[0]
            version_transport = 'nfsv' + parts[1]
            
            if test_id not in data_by_test:
                data_by_test[test_id] = {}
            
            iozone_tests = result.get('iozone_tests', {})
            if not iozone_tests:
                continue
            
            baseline = iozone_tests.get('baseline_throughput', {})
            
            data_by_test[test_id][version_transport] = {
                'write': baseline.get('write_throughput_mbps', 0),
                'read': baseline.get('read_throughput_mbps', 0)
            }
        
        if not data_by_test:
            return None
        
        fig = go.Figure()
        
        # Extract NFS versions for x-axis
        nfs_versions = set()
        for test_data in data_by_test.values():
            for version_transport in test_data.keys():
                nfs_version = version_transport.split('_')[0]
                nfs_versions.add(nfs_version)
        nfs_versions = sorted(nfs_versions)
        
        colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']
        for idx, (test_id, test_data) in enumerate(sorted(data_by_test.items())):
            write_values = []
            read_values = []
            x_labels = []
            
            for nfs_version in nfs_versions:
                found = False
                for version_transport, metrics in test_data.items():
                    if version_transport.startswith(nfs_version):
                        write_values.append(metrics['write'])
                        read_values.append(metrics['read'])
                        transport = version_transport.split('_')[1] if '_' in version_transport else 'tcp'
                        x_labels.append(f"{nfs_version.replace('nfsv', 'v')} ({transport.upper()})")
                        found = True
                        break
                
                if not found:
                    write_values.append(0)
                    read_values.append(0)
                    x_labels.append(f"{nfs_version.replace('nfsv', 'v')}")
            
            fig.add_trace(go.Bar(
                name=f'{test_id} Write',
                x=x_labels,
                y=write_values,
                marker_color=colors[idx % len(colors)],
                opacity=0.8
            ))
            
            fig.add_trace(go.Bar(
                name=f'{test_id} Read',
                x=x_labels,
                y=read_values,
                marker_color=colors[idx % len(colors)],
                opacity=0.5,
                marker_pattern_shape="/"
            ))
        
        fig.update_layout(
            title='IOzone Baseline Throughput Comparison (Write & Read)',
            xaxis_title='NFS Version (Transport)',
            yaxis_title='Throughput (MB/s)',
            barmode='group',
            height=400,
            margin=dict(t=60, b=50, l=50, r=150),
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02)
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_comparison_bonnie_chart(self, combined_results: Dict[str, Dict]) -> Optional[str]:
        """
        Create Bonnie++ throughput comparison chart for test-id comparison.
        
        Args:
            combined_results: Results with keys like 'testid_nfsv3_tcp'
            
        Returns:
            HTML string for chart or None
        """
        if not self.plotly_available:
            return None
        
        data_by_test = {}
        
        for key, result in combined_results.items():
            parts = key.split('_nfsv')
            if len(parts) != 2:
                continue
            
            test_id = parts[0]
            version_transport = 'nfsv' + parts[1]
            
            if test_id not in data_by_test:
                data_by_test[test_id] = {}
            
            bonnie_tests = result.get('bonnie_tests', {})
            if not bonnie_tests:
                continue
            
            comprehensive = bonnie_tests.get('comprehensive_test', {})
            
            data_by_test[test_id][version_transport] = {
                'output': comprehensive.get('sequential_output_block_mbps', 0),
                'input': comprehensive.get('sequential_input_block_mbps', 0)
            }
        
        if not data_by_test:
            return None
        
        fig = go.Figure()
        
        # Extract NFS versions for x-axis
        nfs_versions = set()
        for test_data in data_by_test.values():
            for version_transport in test_data.keys():
                nfs_version = version_transport.split('_')[0]
                nfs_versions.add(nfs_version)
        nfs_versions = sorted(nfs_versions)
        
        colors = ['#f59e0b', '#8b5cf6', '#10b981', '#ef4444']
        for idx, (test_id, test_data) in enumerate(sorted(data_by_test.items())):
            output_values = []
            input_values = []
            x_labels = []
            
            for nfs_version in nfs_versions:
                found = False
                for version_transport, metrics in test_data.items():
                    if version_transport.startswith(nfs_version):
                        output_values.append(metrics['output'])
                        input_values.append(metrics['input'])
                        transport = version_transport.split('_')[1] if '_' in version_transport else 'tcp'
                        x_labels.append(f"{nfs_version.replace('nfsv', 'v')} ({transport.upper()})")
                        found = True
                        break
                
                if not found:
                    output_values.append(0)
                    input_values.append(0)
                    x_labels.append(f"{nfs_version.replace('nfsv', 'v')}")
            
            fig.add_trace(go.Bar(
                name=f'{test_id} Write',
                x=x_labels,
                y=output_values,
                marker_color=colors[idx % len(colors)],
                opacity=0.8
            ))
            
            fig.add_trace(go.Bar(
                name=f'{test_id} Read',
                x=x_labels,
                y=input_values,
                marker_color=colors[idx % len(colors)],
                opacity=0.5,
                marker_pattern_shape="/"
            ))
        
        fig.update_layout(
            title='Bonnie++ Sequential Block Throughput Comparison (Write & Read)',
            xaxis_title='NFS Version (Transport)',
            yaxis_title='Throughput (MB/s)',
            barmode='group',
            height=400,
            margin=dict(t=60, b=50, l=50, r=150),
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02)
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_comparison_dbench_chart(self, combined_results: Dict[str, Dict]) -> Optional[str]:
        """
        Create DBench throughput comparison chart for test-id comparison.
        
        Args:
            combined_results: Results with keys like 'testid_nfsv3_tcp'
            
        Returns:
            HTML string for chart or None
        """
        if not self.plotly_available:
            return None
        
        data_by_test = {}
        
        for key, result in combined_results.items():
            parts = key.split('_nfsv')
            if len(parts) != 2:
                continue
            
            test_id = parts[0]
            version_transport = 'nfsv' + parts[1]
            
            # DBench typically only runs on NFSv3
            if 'nfsv3' not in version_transport:
                continue
            
            if test_id not in data_by_test:
                data_by_test[test_id] = {}
            
            dbench_tests = result.get('dbench_tests', {})
            if not dbench_tests:
                continue
            
            # Get moderate client load throughput
            moderate = dbench_tests.get('moderate_client_load', {})
            
            data_by_test[test_id][version_transport] = {
                'throughput': moderate.get('throughput_mbps', 0)
            }
        
        if not data_by_test:
            return None
        
        fig = go.Figure()
        
        # Extract NFS versions for x-axis
        nfs_versions = set()
        for test_data in data_by_test.values():
            for version_transport in test_data.keys():
                nfs_version = version_transport.split('_')[0]
                nfs_versions.add(nfs_version)
        nfs_versions = sorted(nfs_versions)
        
        colors = ['#ec4899', '#10b981', '#3b82f6', '#f59e0b']
        for idx, (test_id, test_data) in enumerate(sorted(data_by_test.items())):
            throughput_values = []
            x_labels = []
            
            for nfs_version in nfs_versions:
                found = False
                for version_transport, metrics in test_data.items():
                    if version_transport.startswith(nfs_version):
                        throughput_values.append(metrics['throughput'])
                        transport = version_transport.split('_')[1] if '_' in version_transport else 'tcp'
                        x_labels.append(f"{nfs_version.replace('nfsv', 'v')} ({transport.upper()})")
                        found = True
                        break
                
                if not found:
                    throughput_values.append(0)
                    x_labels.append(f"{nfs_version.replace('nfsv', 'v')}")
            
            fig.add_trace(go.Bar(
                name=test_id,
                x=x_labels,
                y=throughput_values,
                marker_color=colors[idx % len(colors)]
            ))
        
        fig.update_layout(
            title='DBench Moderate Client Load Throughput Comparison',
            xaxis_title='NFS Version (Transport)',
            yaxis_title='Throughput (MB/s)',
            barmode='group',
            height=400,
            margin=dict(t=60, b=50, l=50, r=150),
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02)
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    # ========== Dimension-Based Chart Methods ==========
    
    def create_dimension_throughput_chart(self, test_results: Dict[str, Any]) -> Optional[str]:
        """
        Create combined throughput chart from all tools.
        
        Combines DD, FIO, IOzone, Bonnie++, and DBench throughput results
        into a single chart organized by test type.
        
        Args:
            test_results: Full test results dictionary
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available:
            return None
        
        dimension_data = dimension_mapper.extract_dimension_data(test_results, 'throughput')
        
        if not dimension_data:
            return None
        
        names = []
        throughputs = []
        colors = []
        
        # Color scheme by tool
        tool_colors = {
            'dd_tests': '#667eea',
            'fio_tests': '#10b981',
            'iozone_tests': '#3b82f6',
            'bonnie_tests': '#f59e0b',
            'dbench_tests': '#ec4899'
        }
        
        # Extract DD tests
        for test_name, test_data in dimension_data.get('dd_tests', {}).items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                names.append(f"DD: {test_name.replace('_', ' ').title()}")
                throughputs.append(test_data.get('throughput_mbps', 0))
                colors.append(tool_colors['dd_tests'])
        
        # Extract FIO tests
        for test_name, test_data in dimension_data.get('fio_tests', {}).items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                # FIO reports bandwidth in MB/s
                bw = test_data.get('write_bandwidth_mbps') or test_data.get('read_bandwidth_mbps', 0)
                if bw > 0:
                    names.append(f"FIO: {test_name.replace('_', ' ').title()}")
                    throughputs.append(bw)
                    colors.append(tool_colors['fio_tests'])
        
        # Extract IOzone tests
        for test_name, test_data in dimension_data.get('iozone_tests', {}).items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                # Use write throughput as primary metric
                tp = test_data.get('write_throughput_mbps', 0)
                if tp > 0:
                    names.append(f"IOzone: {test_name.replace('_', ' ').title()}")
                    throughputs.append(tp)
                    colors.append(tool_colors['iozone_tests'])
        
        # Extract Bonnie++ tests
        for test_name, test_data in dimension_data.get('bonnie_tests', {}).items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                # Use sequential output as primary metric
                tp = test_data.get('sequential_output_block_mbps', 0)
                if tp > 0:
                    names.append(f"Bonnie++: {test_name.replace('_', ' ').title()}")
                    throughputs.append(tp)
                    colors.append(tool_colors['bonnie_tests'])
        
        # Extract DBench tests
        for test_name, test_data in dimension_data.get('dbench_tests', {}).items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                if test_name == 'scalability_test' and 'results' in test_data:
                    # Skip scalability for this chart (shown in concurrency)
                    continue
                tp = test_data.get('throughput_mbps', 0)
                if tp > 0:
                    names.append(f"DBench: {test_name.replace('_', ' ').title()}")
                    throughputs.append(tp)
                    colors.append(tool_colors['dbench_tests'])
        
        if not names:
            return None
        
        fig = go.Figure(data=[
            go.Bar(x=names, y=throughputs, marker_color=colors)
        ])
        fig.update_layout(
            title='📊 Throughput Performance (All Tools)',
            xaxis_title='Test',
            yaxis_title='Throughput (MB/s)',
            height=500,
            xaxis={'tickangle': -45}
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_dimension_iops_chart(self, test_results: Dict[str, Any]) -> Optional[str]:
        """
        Create IOPS chart from FIO and IOzone.
        
        Args:
            test_results: Full test results dictionary
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available:
            return None
        
        dimension_data = dimension_mapper.extract_dimension_data(test_results, 'iops')
        
        if not dimension_data:
            return None
        
        names = []
        read_iops = []
        write_iops = []
        
        # Extract FIO tests
        for test_name, test_data in dimension_data.get('fio_tests', {}).items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                names.append(f"FIO: {test_name.replace('_', ' ').title()}")
                read_iops.append(test_data.get('read_iops', 0))
                write_iops.append(test_data.get('write_iops', 0))
        
        # Extract IOzone tests
        for test_name, test_data in dimension_data.get('iozone_tests', {}).items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                # IOzone reports IOPS for random tests
                r_iops = test_data.get('read_iops', 0)
                w_iops = test_data.get('write_iops', 0)
                if r_iops > 0 or w_iops > 0:
                    names.append(f"IOzone: {test_name.replace('_', ' ').title()}")
                    read_iops.append(r_iops)
                    write_iops.append(w_iops)
        
        if not names:
            return None
        
        fig = go.Figure(data=[
            go.Bar(name='Read IOPS', x=names, y=read_iops, marker_color='#10b981'),
            go.Bar(name='Write IOPS', x=names, y=write_iops, marker_color='#ef4444')
        ])
        fig.update_layout(
            title='⚡ IOPS Performance',
            xaxis_title='Test',
            yaxis_title='IOPS',
            barmode='group',
            height=400,
            xaxis={'tickangle': -45}
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_dimension_latency_chart(self, test_results: Dict[str, Any]) -> Optional[str]:
        """
        Create latency chart from FIO and DBench.
        
        Args:
            test_results: Full test results dictionary
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available:
            return None
        
        dimension_data = dimension_mapper.extract_dimension_data(test_results, 'latency')
        
        if not dimension_data:
            return None
        
        names = []
        latencies = []
        
        # Extract FIO tests
        for test_name, test_data in dimension_data.get('fio_tests', {}).items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                lat = test_data.get('avg_latency_ms') or test_data.get('write_latency_ms', 0)
                if lat > 0:
                    names.append(f"FIO: {test_name.replace('_', ' ').title()}")
                    latencies.append(lat)
        
        # Extract DBench tests
        for test_name, test_data in dimension_data.get('dbench_tests', {}).items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                lat = test_data.get('avg_latency_ms', 0)
                if lat > 0:
                    names.append(f"DBench: {test_name.replace('_', ' ').title()}")
                    latencies.append(lat)
        
        if not names:
            return None
        
        fig = go.Figure(data=[
            go.Bar(x=names, y=latencies, marker_color='#8b5cf6')
        ])
        fig.update_layout(
            title='⏱️ Latency Performance (Lower is Better)',
            xaxis_title='Test',
            yaxis_title='Latency (ms)',
            height=400,
            xaxis={'tickangle': -45}
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_dimension_metadata_chart(self, test_results: Dict[str, Any]) -> Optional[str]:
        """
        Create metadata operations chart from all tools.
        
        Args:
            test_results: Full test results dictionary
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available:
            return None
        
        dimension_data = dimension_mapper.extract_dimension_data(test_results, 'metadata')
        
        if not dimension_data:
            return None
        
        names = []
        ops_per_sec = []
        colors = []
        
        tool_colors = {
            'fio_tests': '#10b981',
            'iozone_tests': '#3b82f6',
            'bonnie_tests': '#f59e0b',
            'dbench_tests': '#ec4899'
        }
        
        # Extract FIO tests
        for test_name, test_data in dimension_data.get('fio_tests', {}).items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                ops = test_data.get('metadata_ops_per_sec', 0)
                if ops > 0:
                    names.append(f"FIO: {test_name.replace('_', ' ').title()}")
                    ops_per_sec.append(ops)
                    colors.append(tool_colors['fio_tests'])
        
        # Extract IOzone tests
        for test_name, test_data in dimension_data.get('iozone_tests', {}).items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                ops = test_data.get('metadata_ops_per_sec', 0)
                if ops > 0:
                    names.append(f"IOzone: {test_name.replace('_', ' ').title()}")
                    ops_per_sec.append(ops)
                    colors.append(tool_colors['iozone_tests'])
        
        # Extract Bonnie++ tests - these are metrics within tests
        for test_name, test_data in dimension_data.get('bonnie_tests', {}).items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                # Check for file operation metrics
                for metric in ['file_create_seq_per_sec', 'file_delete_seq_per_sec',
                              'file_stat_seq_per_sec', 'random_seeks_per_sec']:
                    ops = test_data.get(metric, 0)
                    if ops > 0:
                        metric_name = metric.replace('_', ' ').replace('per sec', '').title()
                        names.append(f"Bonnie++: {metric_name}")
                        ops_per_sec.append(ops)
                        colors.append(tool_colors['bonnie_tests'])
        
        # Extract DBench tests
        for test_name, test_data in dimension_data.get('dbench_tests', {}).items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                ops = test_data.get('metadata_ops_per_sec', 0)
                if ops > 0:
                    names.append(f"DBench: {test_name.replace('_', ' ').title()}")
                    ops_per_sec.append(ops)
                    colors.append(tool_colors['dbench_tests'])
        
        if not names:
            return None
        
        fig = go.Figure(data=[
            go.Bar(x=names, y=ops_per_sec, marker_color=colors)
        ])
        fig.update_layout(
            title='📁 Metadata Operations Performance',
            xaxis_title='Test',
            yaxis_title='Operations/sec',
            height=500,
            xaxis={'tickangle': -45}
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_dimension_cache_chart(self, test_results: Dict[str, Any]) -> Optional[str]:
        """
        Create cache effects comparison chart.
        
        Shows performance difference between cached and direct I/O.
        
        Args:
            test_results: Full test results dictionary
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available:
            return None
        
        dimension_data = dimension_mapper.extract_dimension_data(test_results, 'cache_effects')
        
        if not dimension_data:
            return None
        
        names = []
        cached_values = []
        direct_values = []
        
        # Extract DD cache comparisons
        for comparison_name, comparison_data in dimension_data.get('dd_tests', {}).items():
            if isinstance(comparison_data, dict) and 'cached' in comparison_data and 'direct' in comparison_data:
                cached = comparison_data['cached']
                direct = comparison_data['direct']
                
                if cached.get('status') == 'passed' and direct.get('status') == 'passed':
                    names.append(comparison_name.replace('_vs_', ' vs ').replace('_', ' ').title())
                    cached_values.append(cached.get('throughput_mbps', 0))
                    direct_values.append(direct.get('throughput_mbps', 0))
        
        # Extract IOzone cache behavior test
        for test_name, test_data in dimension_data.get('iozone_tests', {}).items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                # IOzone cache_behavior test shows cached vs direct performance
                cached_tp = test_data.get('cached_read_throughput_mbps', 0)
                direct_tp = test_data.get('direct_read_throughput_mbps', 0)
                if cached_tp > 0 and direct_tp > 0:
                    names.append(f"IOzone: {test_name.replace('_', ' ').title()}")
                    cached_values.append(cached_tp)
                    direct_values.append(direct_tp)
        
        if not names:
            return None
        
        fig = go.Figure(data=[
            go.Bar(name='Cached I/O', x=names, y=cached_values, marker_color='#10b981'),
            go.Bar(name='Direct I/O', x=names, y=direct_values, marker_color='#ef4444')
        ])
        fig.update_layout(
            title='💾 Cache Effects Comparison',
            xaxis_title='Test',
            yaxis_title='Throughput (MB/s)',
            barmode='group',
            height=400,
            xaxis={'tickangle': -45}
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_dimension_concurrency_chart(self, test_results: Dict[str, Any]) -> Optional[str]:
        """
        Create concurrency scaling chart.
        
        Shows how performance scales with concurrent clients/threads.
        
        Args:
            test_results: Full test results dictionary
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available:
            return None
        
        dimension_data = dimension_mapper.extract_dimension_data(test_results, 'concurrency')
        
        if not dimension_data:
            return None
        
        # Separate data by tool for line chart
        iozone_threads = []
        iozone_throughput = []
        dbench_clients = []
        dbench_throughput = []
        
        # Extract IOzone scaling tests
        for test_name, test_data in dimension_data.get('iozone_tests', {}).items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                if test_name == 'scaling_test' and 'scaling_results' in test_data:
                    for thread_name, thread_data in test_data['scaling_results'].items():
                        num_threads = thread_data.get('num_threads', 0)
                        tp = thread_data.get('write_throughput_mbps', 0)
                        if num_threads > 0 and tp > 0:
                            iozone_threads.append(num_threads)
                            iozone_throughput.append(tp)
                elif 'concurrency' in test_name:
                    # Extract thread count from name
                    import re
                    match = re.search(r'(\d+)', test_name)
                    if match:
                        threads = int(match.group(1))
                        tp = test_data.get('write_throughput_mbps', 0)
                        if tp > 0:
                            iozone_threads.append(threads)
                            iozone_throughput.append(tp)
        
        # Extract DBench scaling tests
        for test_name, test_data in dimension_data.get('dbench_tests', {}).items():
            if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                if test_name == 'scalability_test' and 'results' in test_data:
                    for client_count, client_data in test_data['results'].items():
                        num_clients = client_data.get('num_clients', 0)
                        tp = client_data.get('throughput_mbps', 0)
                        if num_clients > 0 and tp > 0:
                            dbench_clients.append(num_clients)
                            dbench_throughput.append(tp)
                else:
                    # Try to extract client count from test name or data
                    num_clients = test_data.get('num_clients', 0)
                    tp = test_data.get('throughput_mbps', 0)
                    if num_clients > 0 and tp > 0:
                        dbench_clients.append(num_clients)
                        dbench_throughput.append(tp)
        
        if not iozone_threads and not dbench_clients:
            return None
        
        fig = go.Figure()
        
        # Sort data for proper line chart
        if iozone_threads:
            sorted_data = sorted(zip(iozone_threads, iozone_throughput))
            iozone_threads, iozone_throughput = zip(*sorted_data)
            fig.add_trace(go.Scatter(
                x=list(iozone_threads),
                y=list(iozone_throughput),
                mode='lines+markers',
                name='IOzone',
                line=dict(color='#3b82f6', width=3),
                marker=dict(size=10)
            ))
        
        if dbench_clients:
            sorted_data = sorted(zip(dbench_clients, dbench_throughput))
            dbench_clients, dbench_throughput = zip(*sorted_data)
            fig.add_trace(go.Scatter(
                x=list(dbench_clients),
                y=list(dbench_throughput),
                mode='lines+markers',
                name='DBench',
                line=dict(color='#ec4899', width=3),
                marker=dict(size=10)
            ))
        
        fig.update_layout(
            title='👥 Concurrency Scaling Performance',
            xaxis_title='Number of Concurrent Clients/Threads',
            yaxis_title='Throughput (MB/s)',
            height=400,
            hovermode='x unified'
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def generate_all_dimension_charts(self, test_results: Dict[str, Dict]) -> str:
        """
        Generate all dimension-based charts.
        
        Args:
            test_results: Dictionary of test results by category
            
        Returns:
            HTML string with all dimension charts
        """
        if not self.plotly_available:
            return ""
        
        charts_html = '<div class="section"><h2>📊 Performance by Dimension</h2>'
        charts_html += '<p>Results organized by performance characteristics rather than tools.</p>'
        
        # Throughput chart
        throughput_chart = self.create_dimension_throughput_chart(test_results)
        if throughput_chart:
            charts_html += f'<div class="chart-container">{throughput_chart}</div>'
        
        # IOPS chart
        iops_chart = self.create_dimension_iops_chart(test_results)
        if iops_chart:
            charts_html += f'<div class="chart-container">{iops_chart}</div>'
        
        # Latency chart
        latency_chart = self.create_dimension_latency_chart(test_results)
        if latency_chart:
            charts_html += f'<div class="chart-container">{latency_chart}</div>'
        
        # Metadata chart
        metadata_chart = self.create_dimension_metadata_chart(test_results)
        if metadata_chart:
            charts_html += f'<div class="chart-container">{metadata_chart}</div>'
        
        # Cache effects chart
        cache_chart = self.create_dimension_cache_chart(test_results)
        if cache_chart:
            charts_html += f'<div class="chart-container">{cache_chart}</div>'
        
        # Concurrency chart
        concurrency_chart = self.create_dimension_concurrency_chart(test_results)
        if concurrency_chart:
            charts_html += f'<div class="chart-container">{concurrency_chart}</div>'
        
        charts_html += '</div>'
        return charts_html
    # ========== Multi-Version Dimension-Based Chart Methods ==========
    
    def create_multi_version_dimension_throughput_chart(self, results_by_version: Dict[str, Dict]) -> Optional[str]:
        """
        Create multi-version throughput comparison chart organized by dimension.
        
        Shows throughput tests from all tools, grouped by NFS version.
        
        Args:
            results_by_version: Results organized by NFS version
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available:
            return None
        
        versions = sorted(results_by_version.keys())
        
        # Extract throughput data for each version
        version_data = {}
        for version_key in versions:
            version_results = results_by_version[version_key]
            dimension_data = dimension_mapper.extract_dimension_data(version_results, 'throughput')
            version_data[version_key] = dimension_data
        
        if not version_data:
            return None
        
        # Collect all unique test names across all versions
        all_tests = set()
        for dim_data in version_data.values():
            for tool_key, tool_data in dim_data.items():
                for test_name in tool_data.keys():
                    all_tests.add(f"{tool_key}:{test_name}")
        
        if not all_tests:
            return None
        
        # Create traces for each version
        fig = go.Figure()
        for version_key in versions:
            test_names = []
            throughputs = []
            
            for test_key in sorted(all_tests):
                tool_key, test_name = test_key.split(':', 1)
                dim_data = version_data[version_key]
                
                if tool_key in dim_data and test_name in dim_data[tool_key]:
                    test_data = dim_data[tool_key][test_name]
                    if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                        # Extract throughput value
                        tp = (test_data.get('throughput_mbps') or 
                             test_data.get('write_bandwidth_mbps') or 
                             test_data.get('sequential_output_block_mbps') or 0)
                        
                        if tp > 0:
                            tool_name = tool_key.replace('_tests', '').upper()
                            # Format test name and replace Bonnie++ terminology
                            formatted_name = test_name.replace('_', ' ').title()
                            formatted_name = formatted_name.replace('Sequential Output', 'Sequential Write')
                            formatted_name = formatted_name.replace('Sequential Input', 'Sequential Read')
                            test_names.append(f"{tool_name}: {formatted_name}")
                            throughputs.append(tp)
            
            if test_names:
                fig.add_trace(go.Bar(
                    name=version_key.replace('_', ' ').upper(),
                    x=test_names,
                    y=throughputs
                ))
        
        fig.update_layout(
            title={
                'text': '📊 Throughput Performance Across NFS Versions',
                'font': {'size': 22, 'color': '#1f2937', 'family': 'Arial, sans-serif', 'weight': 'bold'},
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Test',
            yaxis_title='Throughput (MB/s)',
            barmode='group',
            height=500,
            margin=dict(t=80, b=80, l=60, r=180),
            xaxis={'tickangle': -45},
            legend={'orientation': 'v', 'yanchor': 'middle', 'y': 0.5, 'xanchor': 'left', 'x': 1.02}
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_multi_version_dimension_iops_chart(self, results_by_version: Dict[str, Dict]) -> Optional[str]:
        """
        Create multi-version IOPS comparison chart organized by dimension.
        
        Args:
            results_by_version: Results organized by NFS version
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available:
            return None
        
        versions = sorted(results_by_version.keys())
        
        # Extract IOPS data for each version
        version_data = {}
        for version_key in versions:
            version_results = results_by_version[version_key]
            dimension_data = dimension_mapper.extract_dimension_data(version_results, 'iops')
            version_data[version_key] = dimension_data
        
        if not version_data:
            return None
        
        # Collect test data
        fig = go.Figure()
        for version_key in versions:
            test_names = []
            read_iops = []
            write_iops = []
            
            dim_data = version_data[version_key]
            for tool_key, tool_data in dim_data.items():
                tool_name = tool_key.replace('_tests', '').upper()
                for test_name, test_data in tool_data.items():
                    if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                        r_iops = test_data.get('read_iops', 0)
                        w_iops = test_data.get('write_iops', 0)
                        if r_iops > 0 or w_iops > 0:
                            test_names.append(f"{tool_name}: {test_name.replace('_', ' ').title()}")
                            read_iops.append(r_iops)
                            write_iops.append(w_iops)
            
            if test_names:
                fig.add_trace(go.Bar(
                    name=f'{version_key.replace("_", " ").upper()} Read',
                    x=test_names,
                    y=read_iops
                ))
                fig.add_trace(go.Bar(
                    name=f'{version_key.replace("_", " ").upper()} Write',
                    x=test_names,
                    y=write_iops
                ))
        
        fig.update_layout(
            title={
                'text': '⚡ IOPS Performance Across NFS Versions',
                'font': {'size': 22, 'color': '#1f2937', 'family': 'Arial, sans-serif', 'weight': 'bold'},
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Test',
            yaxis_title='IOPS',
            barmode='group',
            height=500,
            margin=dict(t=80, b=80, l=60, r=180),
            xaxis={'tickangle': -45},
            legend={'orientation': 'v', 'yanchor': 'middle', 'y': 0.5, 'xanchor': 'left', 'x': 1.02}
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_multi_version_dimension_latency_chart(self, results_by_version: Dict[str, Dict]) -> Optional[str]:
        """
        Create multi-version latency comparison chart organized by dimension.
        
        Args:
            results_by_version: Results organized by NFS version
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available:
            return None
        
        versions = sorted(results_by_version.keys())
        
        # Extract latency data for each version
        version_data = {}
        for version_key in versions:
            version_results = results_by_version[version_key]
            dimension_data = dimension_mapper.extract_dimension_data(version_results, 'latency')
            version_data[version_key] = dimension_data
        
        if not version_data:
            return None
        
        fig = go.Figure()
        for version_key in versions:
            test_names = []
            latencies = []
            
            dim_data = version_data[version_key]
            for tool_key, tool_data in dim_data.items():
                tool_name = tool_key.replace('_tests', '').upper()
                for test_name, test_data in tool_data.items():
                    if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                        # Try multiple latency fields
                        lat = (test_data.get('avg_latency_ms') or
                               test_data.get('read_latency_ms') or
                               test_data.get('write_latency_ms', 0))
                        if lat > 0:
                            test_names.append(f"{tool_name}: {test_name.replace('_', ' ').title()}")
                            latencies.append(lat)
            
            if test_names:
                fig.add_trace(go.Bar(
                    name=version_key.replace('_', ' ').upper(),
                    x=test_names,
                    y=latencies
                ))
        
        fig.update_layout(
            title={
                'text': '⏱️ Latency Performance Across NFS Versions (Lower is Better)',
                'font': {'size': 22, 'color': '#1f2937', 'family': 'Arial, sans-serif', 'weight': 'bold'},
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Test',
            yaxis_title='Latency (ms)',
            barmode='group',
            height=500,
            margin=dict(t=80, b=80, l=60, r=180),
            xaxis={'tickangle': -45},
            legend={'orientation': 'v', 'yanchor': 'middle', 'y': 0.5, 'xanchor': 'left', 'x': 1.02}
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    def create_multi_version_dimension_metadata_chart(self, results_by_version: Dict[str, Dict]) -> Optional[str]:
        """
        Create multi-version metadata operations comparison chart.
        
        Args:
            results_by_version: Results organized by NFS version
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available:
            return None
        
        versions = sorted(results_by_version.keys())
        
        # Extract metadata data for each version
        version_data = {}
        for version_key in versions:
            version_results = results_by_version[version_key]
            dimension_data = dimension_mapper.extract_dimension_data(version_results, 'metadata')
            version_data[version_key] = dimension_data
        
        if not version_data:
            return None
        
        fig = go.Figure()
        for version_key in versions:
            test_names = []
            ops_values = []
            
            dim_data = version_data[version_key]
            
            # Extract FIO metadata tests
            for test_name, test_data in dim_data.get('fio_tests', {}).items():
                if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                    # Try metadata_ops_per_sec first, then fall back to IOPS for metadata-heavy tests
                    ops = (test_data.get('metadata_ops_per_sec') or
                           test_data.get('read_iops') or
                           test_data.get('write_iops', 0))
                    if ops > 0:
                        test_names.append(f"FIO: {test_name.replace('_', ' ').title()}")
                        ops_values.append(ops)
            
            # Extract Bonnie++ metadata metrics
            for test_name, test_data in dim_data.get('bonnie_tests', {}).items():
                if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                    for metric in ['file_create_seq_per_sec', 'file_delete_seq_per_sec',
                                  'file_stat_seq_per_sec', 'random_seeks_per_sec']:
                        ops = test_data.get(metric, 0)
                        if ops > 0:
                            metric_name = metric.replace('_', ' ').replace('per sec', '').title()
                            test_names.append(f"Bonnie++: {metric_name}")
                            ops_values.append(ops)
            
            if test_names:
                fig.add_trace(go.Bar(
                    name=version_key.replace('_', ' ').upper(),
                    x=test_names,
                    y=ops_values
                ))
        
        fig.update_layout(
            title={
                'text': '📁 Metadata Operations Performance Across NFS Versions',
                'font': {'size': 22, 'color': '#1f2937', 'family': 'Arial, sans-serif', 'weight': 'bold'},
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Test',
            yaxis_title='Operations/sec',
            barmode='group',
            height=500,
            margin=dict(t=80, b=80, l=60, r=180),
            xaxis={'tickangle': -45},
            legend={'orientation': 'v', 'yanchor': 'middle', 'y': 0.5, 'xanchor': 'left', 'x': 1.02}
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_multi_version_dimension_cache_chart(self, results_by_version: Dict[str, Dict]) -> Optional[str]:
        """
        Create multi-version cache effects comparison chart.
        
        Args:
            results_by_version: Results organized by NFS version
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available:
            return None
        
        versions = sorted(results_by_version.keys())
        
        # Extract cache data for each version
        version_data = {}
        for version_key in versions:
            version_results = results_by_version[version_key]
            dimension_data = dimension_mapper.extract_dimension_data(version_results, 'cache_effects')
            version_data[version_key] = dimension_data
        
        if not version_data:
            return None
        
        # Collect all unique test names
        all_tests = set()
        for dim_data in version_data.values():
            for tool_key, tool_data in dim_data.items():
                for test_name in tool_data.keys():
                    all_tests.add(f"{tool_key}:{test_name}")
        
        if not all_tests:
            return None
        
        fig = go.Figure()
        
        # Create traces for cached and direct I/O for each version
        for version_key in versions:
            cached_values = []
            direct_values = []
            test_labels = []
            
            dim_data = version_data[version_key]
            
            for test_key in sorted(all_tests):
                tool_key, test_name = test_key.split(':', 1)
                
                if tool_key in dim_data and test_name in dim_data[tool_key]:
                    comparison_data = dim_data[tool_key][test_name]
                    
                    if isinstance(comparison_data, dict) and 'cached' in comparison_data and 'direct' in comparison_data:
                        cached = comparison_data['cached']
                        direct = comparison_data['direct']
                        
                        if cached.get('status') == 'passed' and direct.get('status') == 'passed':
                            cached_tp = cached.get('throughput_mbps') or cached.get('cached_read_throughput_mbps', 0)
                            direct_tp = direct.get('throughput_mbps') or direct.get('direct_read_throughput_mbps', 0)
                            
                            if cached_tp > 0 and direct_tp > 0:
                                test_labels.append(test_name.replace('_vs_', ' vs ').replace('_', ' ').title())
                                cached_values.append(cached_tp)
                                direct_values.append(direct_tp)
            
            if test_labels:
                # Add cached trace
                fig.add_trace(go.Bar(
                    name=f"{version_key.replace('_', ' ').upper()} Cached",
                    x=test_labels,
                    y=cached_values,
                    legendgroup=version_key,
                    marker_pattern_shape="/"
                ))
                
                # Add direct trace
                fig.add_trace(go.Bar(
                    name=f"{version_key.replace('_', ' ').upper()} Direct",
                    x=test_labels,
                    y=direct_values,
                    legendgroup=version_key
                ))
        
        fig.update_layout(
            title={
                'text': '💾 Cache Effects Comparison Across NFS Versions',
                'font': {'size': 22, 'color': '#1f2937', 'family': 'Arial, sans-serif', 'weight': 'bold'},
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Test',
            yaxis_title='Throughput (MB/s)',
            barmode='group',
            height=500,
            margin=dict(t=80, b=80, l=60, r=180),
            xaxis={'tickangle': -45},
            legend={'orientation': 'v', 'yanchor': 'middle', 'y': 0.5, 'xanchor': 'left', 'x': 1.02}
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    def create_multi_version_dimension_concurrency_chart(self, results_by_version: Dict[str, Dict]) -> Optional[str]:
        """
        Create multi-version concurrency scaling comparison chart.
        
        Args:
            results_by_version: Results organized by NFS version
            
        Returns:
            HTML string for chart or None if no data
        """
        if not self.plotly_available:
            return None
        
        versions = sorted(results_by_version.keys())
        
        # Extract concurrency data for each version
        version_data = {}
        for version_key in versions:
            version_results = results_by_version[version_key]
            dimension_data = dimension_mapper.extract_dimension_data(version_results, 'concurrency')
            version_data[version_key] = dimension_data
        
        if not version_data:
            return None
        
        fig = go.Figure()
        colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
        
        for idx, version_key in enumerate(versions):
            dim_data = version_data[version_key]
            
            # Extract IOzone scaling data
            iozone_threads = []
            iozone_throughput = []
            for test_name, test_data in dim_data.get('iozone_tests', {}).items():
                if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                    # Handle scaling_test with nested results
                    if test_name == 'scaling_test' and 'scaling_results' in test_data:
                        for thread_name, thread_data in test_data['scaling_results'].items():
                            # Get threads from config or parse from thread_name
                            num_threads = thread_data.get('config', {}).get('threads', 0)
                            if num_threads == 0 and '_threads' in thread_name:
                                # Parse from name like "4_threads"
                                try:
                                    num_threads = int(thread_name.split('_')[0])
                                except:
                                    pass
                            tp = thread_data.get('write_throughput_mbps', 0)
                            if num_threads > 0 and tp > 0:
                                iozone_threads.append(num_threads)
                                iozone_throughput.append(tp)
                    # Handle individual concurrency tests like "concurrency_16_threads"
                    elif 'concurrency' in test_name or 'threads' in test_name:
                        num_threads = test_data.get('config', {}).get('threads', 0)
                        if num_threads == 0 and '_threads' in test_name:
                            # Parse from name
                            try:
                                parts = test_name.split('_')
                                for i, part in enumerate(parts):
                                    if part == 'threads' and i > 0:
                                        num_threads = int(parts[i-1])
                                        break
                            except:
                                pass
                        tp = test_data.get('write_throughput_mbps', 0)
                        if num_threads > 0 and tp > 0:
                            iozone_threads.append(num_threads)
                            iozone_throughput.append(tp)
            
            # Extract DBench scaling data
            dbench_clients = []
            dbench_throughput = []
            for test_name, test_data in dim_data.get('dbench_tests', {}).items():
                if isinstance(test_data, dict) and test_data.get('status') == 'passed':
                    num_clients = test_data.get('num_clients', 0)
                    tp = test_data.get('throughput_mbps', 0)
                    if num_clients > 0 and tp > 0:
                        dbench_clients.append(num_clients)
                        dbench_throughput.append(tp)
            
            # Add IOzone trace if data exists
            if iozone_threads:
                sorted_data = sorted(zip(iozone_threads, iozone_throughput))
                iozone_threads, iozone_throughput = zip(*sorted_data)
                fig.add_trace(go.Scatter(
                    x=list(iozone_threads),
                    y=list(iozone_throughput),
                    mode='lines+markers',
                    name=f"{version_key.replace('_', ' ').upper()} IOzone",
                    line=dict(color=colors[idx % len(colors)], width=2),
                    marker=dict(size=8)
                ))
            
            # Add DBench trace if data exists
            if dbench_clients:
                sorted_data = sorted(zip(dbench_clients, dbench_throughput))
                dbench_clients, dbench_throughput = zip(*sorted_data)
                fig.add_trace(go.Scatter(
                    x=list(dbench_clients),
                    y=list(dbench_throughput),
                    mode='lines+markers',
                    name=f"{version_key.replace('_', ' ').upper()} DBench",
                    line=dict(color=colors[idx % len(colors)], width=2, dash='dash'),
                    marker=dict(size=8, symbol='square')
                ))
        
        fig.update_layout(
            title={
                'text': '👥 Concurrency Scaling Performance Across NFS Versions',
                'font': {'size': 22, 'color': '#1f2937', 'family': 'Arial, sans-serif', 'weight': 'bold'},
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Number of Concurrent Clients/Threads',
            yaxis_title='Throughput (MB/s)',
            height=500,
            margin=dict(t=80, b=80, l=60, r=180),
            hovermode='x unified',
            legend={'orientation': 'v', 'yanchor': 'middle', 'y': 0.5, 'xanchor': 'left', 'x': 1.02}
        )
        
        return fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    
    def generate_all_multi_version_dimension_charts(self, results_by_version: Dict[str, Dict]) -> str:
        """
        Generate all dimension-based charts for multi-version report.
        
        Args:
            results_by_version: Results organized by NFS version
            
        Returns:
            HTML string with all dimension charts
        """
        if not self.plotly_available:
            return ""
        
        charts_html = '<div class="section"><h2>📊 Performance by Dimension Across Versions</h2>'
        charts_html += '<p>Results organized by performance characteristics, comparing NFS versions.</p>'
        
        # Throughput chart
        throughput_chart = self.create_multi_version_dimension_throughput_chart(results_by_version)
        if throughput_chart:
            charts_html += f'<div class="chart-container">{throughput_chart}</div>'
        
        # IOPS chart
        iops_chart = self.create_multi_version_dimension_iops_chart(results_by_version)
        if iops_chart:
            charts_html += f'<div class="chart-container">{iops_chart}</div>'
        
        # Latency chart
        latency_chart = self.create_multi_version_dimension_latency_chart(results_by_version)
        if latency_chart:
            charts_html += f'<div class="chart-container">{latency_chart}</div>'
        
        # Metadata chart
        metadata_chart = self.create_multi_version_dimension_metadata_chart(results_by_version)
        if metadata_chart:
            charts_html += f'<div class="chart-container">{metadata_chart}</div>'
        
        # Cache effects chart
        cache_chart = self.create_multi_version_dimension_cache_chart(results_by_version)
        if cache_chart:
            charts_html += f'<div class="chart-container">{cache_chart}</div>'
        
        # Concurrency chart
        concurrency_chart = self.create_multi_version_dimension_concurrency_chart(results_by_version)
        if concurrency_chart:
            charts_html += f'<div class="chart-container">{concurrency_chart}</div>'
        
        charts_html += '</div>'
        return charts_html


# Made with Bob
