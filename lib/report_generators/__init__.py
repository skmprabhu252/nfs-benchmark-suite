#!/usr/bin/env python3
"""
HTML Report Generators for NFS Benchmark Suite

This package provides modular report generation capabilities for different scenarios:
- Single file reports
- Multi-version aggregated reports  
- Test-ID comparison reports
"""

from .single_file_report import SingleFileReportGenerator
from .multi_version_report import MultiVersionReportGenerator
from .comparison_report import ComparisonReportGenerator

__all__ = [
    'SingleFileReportGenerator',
    'MultiVersionReportGenerator',
    'ComparisonReportGenerator',
]

# Made with Bob
