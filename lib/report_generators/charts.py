#!/usr/bin/env python3
"""
Chart generation utilities for HTML reports

Provides Plotly chart generation for all benchmark types with proper
NFSv3-only filtering for dbench and correct field names for all tests.
"""

import logging
from typing import Dict, Any, List, Optional

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
            title='DD Test Throughput',
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
            title='FIO Test IOPS',
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
            go.Bar(name='Output', x=names, y=output_throughputs, marker_color='#f59e0b'),
            go.Bar(name='Input', x=names, y=input_throughputs, marker_color='#8b5cf6')
        ])
        fig.update_layout(
            title='Bonnie++ Test Throughput',
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
                if test_name == 'scalability_test' and 'client_results' in test_data:
                    for client_data in test_data['client_results']:
                        num_clients = client_data.get('num_clients', 0)
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
            results_by_version: Results organized by NFS version
            
        Returns:
            HTML string with all charts
        """
        if not self.plotly_available:
            return ""
        
        charts_html = '<div class="section"><h2>📊 Multi-Version Performance Comparison</h2>'
        
        # DD comparison
        dd_chart = self.create_multi_version_dd_chart(results_by_version)
        if dd_chart:
            charts_html += f'<div class="chart-container">{dd_chart}</div>'
        
        # FIO comparison
        fio_chart = self.create_multi_version_fio_chart(results_by_version)
        if fio_chart:
            charts_html += f'<div class="chart-container">{fio_chart}</div>'
        
        # DBench comparison (NFSv3 only)
        dbench_chart = self.create_multi_version_dbench_chart(results_by_version)
        if dbench_chart:
            charts_html += f'<div class="chart-container">{dbench_chart}</div>'
        
        charts_html += '</div>'
        return charts_html

# Made with Bob
