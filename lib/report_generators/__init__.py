#!/usr/bin/env python3
"""
HTML Report Generators for NFS Benchmark Suite

This package provides modular report generation capabilities for different scenarios:
- Single file reports
- Multi-version aggregated reports
- Test-ID comparison reports

Report Styles:
- Tool-based: Organized by benchmark tool (DD, FIO, IOzone, Bonnie++, DBench)
- Dimension-based: Organized by performance dimension (Throughput, IOPS, Latency, etc.)
"""

from .single_file_report import SingleFileReportGenerator
from .multi_version_report import MultiVersionReportGenerator
from .comparison_report import ComparisonReportGenerator
from . import dimension_mapper

__all__ = [
    'SingleFileReportGenerator',
    'MultiVersionReportGenerator',
    'ComparisonReportGenerator',
    'dimension_mapper',
]

# Made with Bob
