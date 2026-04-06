# Sample Data and Reports

This directory contains sample test data and generated reports for demonstration and testing purposes.

## Directory Structure

```
samples/
├── logs/          # Sample JSON test result files (12 files)
└── reports/       # Sample HTML reports generated from test data (28 files)
```

## Sample Test Data (logs/)

### Test Scenarios Included:

1. **baseline_2026** - Complete test suite with all 4 NFS versions
   - `nfs_performance_baseline_2026_nfsv3_tcp_20260406_100000.json`
   - `nfs_performance_baseline_2026_nfsv4.0_tcp_20260406_100000.json`
   - `nfs_performance_baseline_2026_nfsv4.1_tcp_20260406_100000.json`
   - `nfs_performance_baseline_2026_nfsv4.2_tcp_20260406_100000.json`

2. **optimized_2026** - Optimized configuration with all 4 NFS versions
   - `nfs_performance_optimized_2026_nfsv3_tcp_20260406_110000.json`
   - `nfs_performance_optimized_2026_nfsv4.0_tcp_20260406_110000.json`
   - `nfs_performance_optimized_2026_nfsv4.1_tcp_20260406_110000.json`
   - `nfs_performance_optimized_2026_nfsv4.2_tcp_20260406_110000.json`

3. **single_test** - Single version test (NFSv4.2 only)
   - `nfs_performance_single_test_nfsv4.2_tcp_20260406_120000.json`

4. **multi_version_test** - Multi-version comparison (3 versions)
   - `nfs_performance_multi_version_test_nfsv3_tcp_20260406_130000.json`
   - `nfs_performance_multi_version_test_nfsv4.1_tcp_20260406_130000.json`
   - `nfs_performance_multi_version_test_nfsv4.2_tcp_20260406_130000.json`

## Sample Reports (reports/)

The reports directory contains HTML reports generated from the sample data, demonstrating:

- **Single-file reports** - Individual test results
- **Multi-version reports** - Comparing multiple NFS versions
- **Comparison reports** - Side-by-side comparison of different test-IDs
- **Both report styles** - Tool-based and dimension-based views

## Generating Reports from Sample Data

You can regenerate reports from the sample data using:

```bash
# Single file report (dimension-based, default)
python3 generate_html_report.py samples/logs/nfs_performance_single_test_nfsv4.2_tcp_20260406_120000.json

# Multi-version report (dimension-based, default)
python3 generate_html_report.py --test-id multi_version_test --directory samples/logs

# Comparison report (dimension-based, default)
python3 generate_html_report.py --test-id baseline_2026 --compare-with optimized_2026 --directory samples/logs

# Tool-based report (old style)
python3 generate_html_report.py --test-id baseline_2026 --directory samples/logs --report-style tool-based
```

## Creating New Sample Data

To create fresh sample data, run:

```bash
python3 create_sample_data.py
```

This will generate new JSON files with current timestamps in the current directory. You can then move them to `samples/logs/` if desired.

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