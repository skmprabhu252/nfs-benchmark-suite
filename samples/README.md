# Sample Data Generator

This directory contains the `create_sample_data.py` script for generating sample test data for demonstration and testing purposes.

## Quick Start

Generate sample data with:

```bash
cd samples
python3 create_sample_data.py
```

This creates sample JSON files in `samples/logs/` and generates HTML reports in `samples/reports/`.

## Directory Structure

```
samples/
├── create_sample_data.py  # Script to generate sample data
├── logs/                   # Generated JSON test results (not in git)
└── reports/                # Generated HTML reports (not in git)
```


## Generated Test Scenarios

The script creates 4 test scenarios:

1. **baseline_2026** - Complete test suite with all 4 NFS versions
   - NFSv3, NFSv4.0, NFSv4.1, NFSv4.2 (4 files)

2. **optimized_2026** - Optimized configuration with all 4 NFS versions
   - NFSv3, NFSv4.0, NFSv4.1, NFSv4.2 (4 files)
   - Shows ~15-20% performance improvement over baseline

3. **single_test** - Single version test
   - NFSv4.2 only (1 file)

4. **multi_version_test** - Multi-version comparison
   - NFSv3, NFSv4.1, NFSv4.2 (3 files)

**Total**: 12 JSON files with comprehensive benchmark results

## Generating Reports from Sample Data

After generating sample data, create reports with:

```bash
# From repository root directory

# Single file report (dimension-based, default)
python3 generate_html_report.py samples/logs/nfs_performance_single_test_nfsv4.2_tcp_*.json

# Multi-version report (dimension-based, default)
python3 generate_html_report.py --test-id multi_version_test --directory samples/logs

# Comparison report (dimension-based, default)
python3 generate_html_report.py --test-id baseline_2026 --compare-with optimized_2026 --directory samples/logs

# Tool-based report (old style)
python3 generate_html_report.py --test-id baseline_2026 --directory samples/logs --report-style tool-based
```

## Report Types

### Dimension-Based Reports (Default)
Organizes results by 6 performance dimensions:
- **Throughput** - Sequential data transfer rates
- **IOPS** - Random I/O operations per second
- **Latency** - Response times for I/O operations
- **Metadata Operations** - File creation, deletion, stat operations
- **Cache Effects** - Performance differences between cached and direct I/O
- **Concurrency Scaling** - Performance with multiple concurrent clients

### Tool-Based Reports
Organizes results by benchmark tool:
- DD, FIO, IOzone, Bonnie++, DBench

## Notes

- All sample data uses synthetic test results for demonstration purposes
- The optimized_2026 test-ID shows improved performance compared to baseline_2026
- Reports are interactive HTML files with charts powered by Plotly
- Sample data includes comprehensive benchmark results from all 5 tools