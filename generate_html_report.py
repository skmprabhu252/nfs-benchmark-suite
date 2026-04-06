#!/usr/bin/env python3
"""
Generate HTML Report from NFS Benchmark Suite Results

Simplified main script that delegates to specialized report generators.
Supports three scenarios:
1. Single JSON file report
2. Multi-version aggregated report (by test-id)
3. Test-ID comparison report

Usage:
    # Single file
    python3 generate_html_report.py <json_file>
    python3 generate_html_report.py nfs_performance_test_20240403_120000.json
    
    # Multiple files by test-id
    python3 generate_html_report.py --test-id baseline_2026
    python3 generate_html_report.py --test-id prod_test
    
    # Compare two test-ids
    python3 generate_html_report.py --test-id baseline_2026 --compare-with prod_2026
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# Import specialized report generators
from lib.report_generators import (
    SingleFileReportGenerator,
    MultiVersionReportGenerator,
    ComparisonReportGenerator
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for report generation."""
    
    parser = argparse.ArgumentParser(
        description='Generate HTML report from NFS benchmark results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Generate report from single JSON file
  python3 generate_html_report.py nfs_performance_nfsv3_tcp_20240403_120000.json
  
  # Generate report from all files with test-id
  python3 generate_html_report.py --test-id baseline_2026
  
  # Compare two different test-ids (e.g., different OS versions, software versions)
  python3 generate_html_report.py --test-id baseline_2026 --compare-with prod_2026
  
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
        '--compare-with',
        dest='compare_test_id',
        help='Second test-id to compare with (for comparing different OS/software versions)'
    )
    
    parser.add_argument(
        '--directory',
        default='.',
        help='Directory to search for JSON files (default: current directory)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='report',
        help='Output directory for HTML reports (default: ./report)'
    )
    
    args = parser.parse_args()
    
    # Determine which scenario and create appropriate generator
    try:
        # Scenario 1: Single file
        if args.json_file:
            logger.info(f"Scenario: Single file report")
            logger.info(f"Loading results from: {args.json_file}")
            
            generator = SingleFileReportGenerator(
                json_file=Path(args.json_file),
                output_dir=Path(args.output_dir)
            )
        
        # Scenario 2: Test-ID comparison
        elif args.test_id and args.compare_test_id:
            logger.info(f"Scenario: Test-ID comparison")
            logger.info(f"Comparing: {args.test_id} vs {args.compare_test_id}")
            
            generator = ComparisonReportGenerator(
                test_id_1=args.test_id,
                test_id_2=args.compare_test_id,
                directory=Path(args.directory),
                output_dir=Path(args.output_dir)
            )
        
        # Scenario 3: Multi-version aggregation
        elif args.test_id:
            logger.info(f"Scenario: Multi-version aggregation")
            logger.info(f"Test ID: {args.test_id}")
            
            generator = MultiVersionReportGenerator(
                test_id=args.test_id,
                directory=Path(args.directory),
                output_dir=Path(args.output_dir)
            )
        
        else:
            parser.print_help()
            sys.exit(1)
        
        # Generate report
        logger.info("Generating HTML report...")
        output_file = generator.generate()
        
        # Success
        logger.info("✓ Report generated successfully!")
        logger.info(f"Report saved to: {output_file}")
        logger.info(f"Open in browser: file://{output_file.absolute()}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
