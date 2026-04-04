# NFS Benchmark Suite

A comprehensive benchmarking tool for evaluating NFS storage performance using industry-standard tools (DD, FIO, IOzone, Bonnie++, dbench).

## Table of Contents

1. [Why Use This Tool?](#why-use-this-tool)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Requirements](#requirements)
5. [Installation](#installation)
6. [Quick Start](#quick-start)
7. [Usage](#usage)
8. [Configuration](#configuration)
9. [Understanding Results](#understanding-results)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)
12. [Author](#author)

---

## Why Use This Tool?

This tool helps you **measure and validate NFS storage performance** through comprehensive benchmarking:

**When to Use:**
- **Before Production**: Validate NFS performance meets application requirements
- **After Changes**: Verify performance impact of configuration changes (mount options, NFS version, network upgrades)
- **Troubleshooting**: Identify performance bottlenecks (storage, network, or NFS layer)
- **Capacity Planning**: Understand throughput, IOPS, and latency characteristics under load
- **Regression Testing**: Track performance over time and detect degradations

**Key Benefits:**
- **Comprehensive**: Runs 5 industry-standard benchmarks (DD, FIO, IOzone, Bonnie++, dbench) in one command
- **NFS-Specific**: Collects NFS metrics (RPC stats, transport stats, retransmissions) alongside performance data
- **Baseline Comparison**: Compares results against expected performance for your network speed
- **Automated Analysis**: Identifies bottlenecks and provides actionable recommendations
- **Historical Tracking**: Detects performance regressions by comparing with previous test runs

---

## Features

- **Multiple Benchmarks**: DD, FIO, IOzone, Bonnie++, and dbench for comprehensive testing
- **NFS Metrics**: Collects NFS statistics including transport stats, RPC metrics, and per-operation timing
- **Performance Analysis**: Automatically identifies bottlenecks and suggests improvements
- **Historical Tracking**: Compares results with previous runs to detect performance regressions
- **Industry Baselines**: Shows how your results compare to expected performance
- **HTML Reports**: Interactive reports with charts, trends, and executive summary
- **Flexible Testing**: Quick (~15 min) or comprehensive (~60 min) test profiles

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         runtest.py                              │
│                    (Main Test Orchestrator)                     │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├─────────────────────────────────────────────────────┐
             │                                                     │
             v                                                     v
┌────────────────────────┐                        ┌────────────────────────┐
│   Input Validation     │                        │   Metrics Collection   │
│  ─────────────────     │                        │  ──────────────────    │
│  • Mount Path Check    │                        │  • System Metrics      │
│  • Config Validation   │                        │  • NFS Metrics         │
│  • Space Check         │                        │  • Network Stats       │
│  • Permission Check    │                        │  • xprt Statistics     │
└─────────┬──────────────┘                        └───────────┬-───────────┘
          │                                                   │
          v                                                   v
┌────────────────────────────────────────────────────────────-────┐
│                    Benchmark Modules                            │
│  ─────────────────────────────────────────────────────────      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │    DD    │  │   FIO    │  │  IOzone  │  │ Bonnie++ │         │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │
│  ┌──────────┐                                                   │
│  │  dbench  │  All inherit from BaseTestTool                    │
│  └──────────┘                                                   │
└────────────┬────────────────────────────────────────────────────┘
             │
             v
┌─────────────────────────────────────────────────────────────────┐
│                    Analysis & Reporting                         │
│  ─────────────────────────────────────────────────────────      │
│  • Performance Analyzer (Root Cause Detection)                  │
│  • Historical Comparison (Regression Detection)                 │
│  • HTML Report Generator (Interactive Charts)                   │
│  • Executive Summary (Intelligent Insights)                     │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌──────────────┐
│ User Input   │
│ (CLI Args)   │
└──────┬───────┘
       │
       v
┌──────────────────────┐
│ Validation Layer     │
│ • Mount Path         │
│ • Configuration      │
│ • Prerequisites      │
└──────┬───────────────┘
       │
       v
┌──────────────────────┐
│ Test Execution       │
│ ┌────────────────┐   │
│ │ Start Metrics  │   │
│ │ Run Test       │   │
│ │ Stop Metrics   │   │
│ │ Collect Results│   │
│ └────────────────┘   │
└──────┬───────────────┘
       │
       v
┌──────────────────────┐
│ Analysis Layer       │
│ • Performance        │
│ • Historical         │
│ • Root Cause         │
└──────┬───────────────┘
       │
       v
┌──────────────────────┐
│ Output Generation    │
│ • JSON Results       │
│ • HTML Report        │
│ • Console Summary    │
└──────────────────────┘
```

---

## Requirements

- **System**: Linux (kernel 4.x+), Python 3.6+, ~250GB free space
- **Network**: 1 Gbps or higher recommended
- **Tools**: fio, iozone, bonnie++, dbench, nfs-common

### Installing Prerequisites

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip fio iozone bonnie++ dbench libnsl2 nfs-common
```

#### RHEL/CentOS/Fedora
```bash
# Install core packages (always available)
sudo dnf install -y python3 python3-pip fio nfs-utils libnsl

# Optional benchmark tools (may need manual installation)
sudo dnf install -y iozone bonnie++ dbench
```

**Note for RHEL/CentOS users:** Some benchmark tools (iozone, bonnie++, dbench) may not be available in standard repositories. If installation fails, you can:

1. **Enable EPEL repository** (recommended):
   ```bash
   sudo dnf install -y epel-release
   sudo dnf install -y iozone bonnie++ dbench
   ```

**Note:** `libnsl` library is required for dbench to run properly.

2. **Install from source** (if EPEL doesn't have them):
   
   **IOzone:**
   ```bash
   # Download from official site
   wget http://www.iozone.org/src/current/iozone3_506.tar
   tar xf iozone3_506.tar
   cd iozone3_506/src/current
   make linux
   sudo cp iozone /usr/local/bin/
   ```
   - Official site: http://www.iozone.org/
   - GitHub mirror: https://github.com/chaos/iozone

   **Bonnie++:**
   ```bash
   # Install from source
   wget https://www.coker.com.au/bonnie++/bonnie++-2.00a.tgz
   tar xzf bonnie++-2.00a.tgz
   cd bonnie++-2.00a
   ./configure
   make
   sudo make install
   ```
   - Official site: https://www.coker.com.au/bonnie++/
   - GitHub: https://github.com/sbates130272/bonnie

   **dbench:**
   ```bash
   # Install from source
   git clone https://github.com/sahlberg/dbench.git
   cd dbench
   ./autogen.sh
   ./configure
   make
   sudo make install
   ```
   - GitHub: https://github.com/sahlberg/dbench

3. **Run tests without missing tools:**
   The benchmark suite will automatically skip tests for tools that aren't installed. You can run with available tools:
   ```bash
   # Skip specific tests if tools are missing
   python3 runtest.py --mount-path /mnt/nfs1 --skip-iozone --skip-bonnie --skip-dbench
   ```

### Python Dependencies
```bash
pip3 install --user -r requirements.txt
```

---

## Installation

```bash
git clone https://github.com/skmprabhu252/nfs-benchmark-suite.git
cd nfs-benchmark-suite
./setup_and_verify.sh --auto
```

---

## Quick Start

```bash
# Run quick test (~15 minutes)
python3 runtest.py --mount-path /mnt/nfs1 --quick-test

# Generate HTML report
python3 generate_html_report.py nfs_performance_test_*.json
```

---

## Usage

### Basic Usage

```bash
# Default test (~30 minutes)
python3 runtest.py --mount-path /mnt/nfs1

# Quick test (faster, less comprehensive)
python3 runtest.py --mount-path /mnt/nfs1 --quick-test

# Long test (comprehensive, ~60 minutes)
python3 runtest.py --mount-path /mnt/nfs1 --long-test

# Custom configuration
python3 runtest.py --mount-path /mnt/nfs1 --config my_config.yaml

# Verbose output
python3 runtest.py --mount-path /mnt/nfs1 --verbose
```

### Skip Specific Tests

```bash
python3 runtest.py --mount-path /mnt/nfs1 --skip-dd
python3 runtest.py --mount-path /mnt/nfs1 --skip-fio
python3 runtest.py --mount-path /mnt/nfs1 --skip-iozone
python3 runtest.py --mount-path /mnt/nfs1 --skip-bonnie
python3 runtest.py --mount-path /mnt/nfs1 --skip-dbench
```

### Common Scenarios

```bash
# Test different mount options
mount -t nfs -o vers=4.2,rsize=1048576,wsize=1048576 server:/export /mnt/nfs1
python3 runtest.py --mount-path /mnt/nfs1

# Compare NFSv3 vs NFSv4
mount -t nfs -o vers=3 server:/export /mnt/nfs3
mount -t nfs -o vers=4.2 server:/export /mnt/nfs4
python3 runtest.py --mount-path /mnt/nfs3
python3 runtest.py --mount-path /mnt/nfs4

# Disable history tracking (for testing)
python3 runtest.py --mount-path /mnt/nfs1 --no-save-history
```

---

## Configuration

### Custom Test Configuration

```bash
# Copy default config
cp config/test_config.yaml my_config.yaml

# Edit as needed
vim my_config.yaml

# Run with custom config
python3 runtest.py --mount-path /mnt/nfs1 --config my_config.yaml
```

### Example Configuration

```yaml
dd_tests:
  sequential_write_direct:
    enabled: true
    block_size: "1M"
    count: 100000

fio_tests:
  sequential_write:
    enabled: true
    bs: "1M"
    size: "4G"
    numjobs: 1
```

---

## Understanding Results

### Output Files

After running tests, you'll get:
- **JSON file**: `nfs_performance_test_YYYYMMDD_HHMMSS.json` - Raw results
- **Log file**: `nfs_performance_test_YYYYMMDD_HHMMSS.log` - Detailed logs
- **HTML report**: Generate with `python3 generate_html_report.py <json_file>`

### Key Metrics

**Throughput Tests (DD, FIO Sequential)**
- Measures: MB/s for large file transfers
- Good for: Evaluating bulk data transfer performance
- Look for: Close to network bandwidth limit (e.g., ~1,100 MB/s for 10 GbE)

**IOPS Tests (FIO Random)**
- Measures: Operations per second for small random I/O
- Good for: Database and application workloads
- Look for: Consistent IOPS without high latency

**Latency Tests**
- Measures: Response time in milliseconds
- Good for: Interactive applications
- Look for: Low and consistent latency (<5ms average)

**Metadata Tests (IOzone, Bonnie++)**
- Measures: File operations per second
- Good for: Applications with many small files
- Look for: High file creation/deletion rates

**Client Simulation (dbench)**
- Measures: Multi-client throughput and latency
- Good for: Understanding concurrent user performance
- Look for: Linear scaling up to 4-8 clients

### Performance Baselines (10 GbE)

| Test | Minimum | Good | Excellent |
|------|---------|------|-----------|
| Sequential Read | 500 MB/s | 800 MB/s | 1,100 MB/s |
| Sequential Write | 350 MB/s | 600 MB/s | 900 MB/s |
| Random Read (4K) | 8K IOPS | 20K IOPS | 40K IOPS |
| Random Write (4K) | 5K IOPS | 15K IOPS | 30K IOPS |
| Latency (avg) | <10ms | <5ms | <2ms |

*Note: Baselines vary by network speed. 1 GbE: ~100 MB/s, 25 GbE: ~2 GB/s, 100 GbE: ~8 GB/s*

### Historical Comparison

The tool automatically tracks performance over time:
- ✅ **Improved**: Performance increased (green)
- ❌ **Regressed**: Performance decreased >10% (red)
- ⚠️ **Warning**: Performance decreased 5-10% (yellow)
- ➡️ **Stable**: Performance within ±5% (gray)

---

## Best Practices

### Testing Guidelines

1. **Run During Maintenance Windows**: Tests generate significant load
2. **Avoid Concurrent Workloads**: Ensure no other processes using the NFS mount
3. **Run Multiple Iterations**: Run 3-5 times for consistent results
4. **Compare Apples to Apples**: Use same test profile when comparing configurations
5. **Check Network First**: Use `iperf3` to verify network performance before blaming NFS
6. **Monitor Server**: Check NFS server CPU, memory, and storage during tests
7. **Document Configuration**: Record mount options, NFS version, and server details

### Recommended NFS Mount Options

```bash
# NFSv4.2 (recommended for best performance)
mount -t nfs -o vers=4.2,rsize=1048576,wsize=1048576,hard,async,noatime server:/export /mnt/nfs1

# NFSv3 (for comparison or compatibility)
mount -t nfs -o vers=3,rsize=1048576,wsize=1048576,hard,async,noatime server:/export /mnt/nfs1
```

**Key Mount Options Explained:**
- `vers=4.2`: Use NFSv4.2 for best performance (10-30% faster than NFSv3)
- `rsize/wsize=1048576`: 1MB read/write buffer (optimal for 10 GbE networks)
- `hard`: Retry indefinitely on failure (prevents data loss, recommended for production)
- `async`: Better write performance (use `sync` for critical data requiring immediate persistence)
- `noatime`: Don't update file access times (reduces metadata operations by ~20%)

**Performance Tips:**
- For 1 GbE networks: Use `rsize/wsize=262144` (256KB)
- For 25+ GbE networks: Use `rsize/wsize=1048576` (1MB)
- For latency-sensitive apps: Consider `sync` instead of `async`
- For read-heavy workloads: Increase client cache with `actimeo=600`

---

## Troubleshooting

### Common Issues

**1. Permission Denied**
```bash
# Test write access
touch /mnt/nfs1/test && rm /mnt/nfs1/test

# Check mount options
mount | grep nfs

# Fix: Ensure export allows read/write
# On NFS server: /etc/exports
# /export client_ip(rw,sync,no_root_squash)
```

**2. Low Performance**
```bash
# Check network connectivity
ping -c 100 nfs-server
iperf3 -c nfs-server

# Check mount options
mount | grep nfs

# Common fixes:
# - Increase rsize/wsize to 1048576
# - Use NFSv4.2 instead of NFSv3
# - Enable async (if data loss acceptable)
# - Check storage backend performance
```

**3. Tool Not Found**
```bash
# Ubuntu/Debian
sudo apt-get install fio iozone bonnie++ dbench libnsl2

# RHEL/CentOS - try EPEL first
sudo dnf install -y epel-release
sudo dnf install fio iozone bonnie++ dbench libnsl

# If tools not available in repos, see Requirements section for manual installation
```

For detailed installation instructions including building from source, see the [Requirements](#requirements) section above.

**4. Test Hangs or Times Out**
```bash
# Check NFS server status
showmount -e nfs-server

# Check for NFS errors
dmesg | grep -i nfs

# The tool has built-in timeout protection
# Tests will automatically fail after timeout period
```

**5. Inconsistent Results**
```bash
# Run multiple iterations
for i in {1..3}; do
  python3 runtest.py --mount-path /mnt/nfs1 --quick-test
done

# Avoid concurrent workloads
# Run during maintenance windows
# Ensure no other processes using NFS mount
```

---

## Author

**Prabhu Murugesan**
Email: prabhu.murugesan1@ibm.com

**Version:** 1.0 | **Updated:** 2026-04-03
