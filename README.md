# NFS Benchmark Suite

**Automated NFS performance testing with actionable insights**

Validates NFS storage performance across 6 critical dimensions: Throughput, IOPS, Latency, Metadata ops, Cache behavior, and Concurrency scaling.

---

## 🚀 Quick Start

```bash
# 1. Clone and setup (one-time)
git clone https://github.com/skmprabhu252/nfs-benchmark-suite.git
cd nfs-benchmark-suite
./setup_and_verify.sh --auto

# 2. Run validation test (15 minutes)
python3 runtest.py --mount-path /mnt/nfs1 --quick-test

# 3. View results
python3 generate_html_report.py nfs_performance_test_*.json
```

**First time?** Start with the [Quick Test](#running-tests) to validate your setup.
**Production ready?** Run the [Long Test](#two-test-modes) for comprehensive benchmarking.

---

## 📋 Table of Contents

- [What Problem Does This Solve?](#what-problem-does-this-solve)
- [Two Test Modes](#two-test-modes)
- [Installation](#installation)
- [Running Tests](#running-tests)
- [Reading Results](#reading-results)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)

---

## What Problem Does This Solve?

### The Challenge
Validating NFS performance is complex:
- ❌ Multiple tools needed (DD, FIO, IOzone, Bonnie++, dbench)
- ❌ Raw output is hard to interpret
- ❌ No baseline comparisons
- ❌ Manual tracking of performance over time
- ❌ Unclear what the numbers mean

### The Solution
**One command. Complete analysis. Actionable insights.**

| What It Does | How It Helps |
|--------------|--------------|
| **Automates 5 benchmarks** | No need to learn each tool |
| **Measures 6 dimensions** | Throughput, IOPS, latency, metadata, cache, scaling |
| **Compares to baselines** | Know if your 800 MB/s is good or bad |
| **Tracks history** | Automatic regression detection |
| **HTML reports** | Charts, trends, recommendations |
| **NFS metrics** | RPC stats, retransmissions, transport stats |

### Use Cases

| When | Why |
|------|-----|
| **Before Production** | Validate performance meets requirements |
| **After Changes** | Verify impact of mount options, NFS version, network upgrades |
| **Troubleshooting** | Identify bottlenecks (storage vs network vs NFS) |
| **Capacity Planning** | Understand limits under load |
| **Regression Testing** | Detect performance degradation |

---

## Two Test Modes

### Mode Comparison

| | Quick Test | Long Test |
|---|-----------|-----------|
| **Duration** | 15 minutes | 4-8 hours |
| **Purpose** | Validation | Production Benchmark |
| **When to Use** | • Initial setup<br>• Smoke testing<br>• CI/CD<br>• Troubleshooting | • Production validation<br>• Capacity planning<br>• SLA verification<br>• Performance baselines |
| **Disk Space** | 50-100 GB | 1-2 TB |
| **Data Written** | ~20-30 GB | ~500 GB - 1 TB |
| **File Sizes** | 500 MB - 2 GB | 8 GB - 64 GB |
| **Concurrency** | 2-8 threads/clients | 8-128 threads/clients |

### What Gets Measured (Both Modes)

Both test profiles measure these **6 critical performance dimensions**:

**1. Throughput (MB/s)**
- **What it measures:** Sequential data transfer rate for large files
- **Why it matters:** Critical for bulk data operations, backups, large file transfers, media streaming
- **Tools used:** DD, FIO (sequential), IOzone (baseline), Bonnie++
- **Quick test:** 500MB-2GB files | **Long test:** 8GB-64GB files

**2. IOPS (Input/Output Operations Per Second)**
- **What it measures:** Random I/O performance with small block sizes (4K)
- **Why it matters:** Database workloads, virtual machines, application servers with random access patterns
- **Tools used:** FIO (random 4K), IOzone (random I/O)
- **Quick test:** 60 seconds runtime | **Long test:** 60 minutes runtime

**3. Latency (milliseconds)**
- **What it measures:** Response time for I/O operations
- **Why it matters:** Interactive applications, real-time systems, user experience, transaction processing
- **Tools used:** FIO (latency test with queue depth 1), dbench (single client)
- **Quick test:** 30 seconds | **Long test:** 30 minutes

**4. Metadata Operations Per Second**
- **What it measures:** File creation, deletion, stat, rename operations
- **Why it matters:** Applications with many small files, build systems, source code repositories, compilation
- **Tools used:** FIO (metadata ops), IOzone (metadata), Bonnie++ (file operations), dbench
- **Quick test:** 1,000-8,000 files | **Long test:** 50,000-256,000 files

**5. Cache Effects**
- **What it measures:** Performance difference between cached and direct I/O
- **Why it matters:** Understanding client-side caching behavior, tuning cache parameters for optimal performance
- **Tools used:** DD (cached vs direct), IOzone (cache behavior), FIO (direct vs buffered)
- **Quick test:** 500MB-1GB files | **Long test:** 16GB-32GB files

**6. Concurrency Scaling**
- **What it measures:** Performance scaling with multiple concurrent clients/threads
- **Why it matters:** Multi-user environments, parallel workloads, capacity planning, understanding system limits
- **Tools used:** IOzone (scaling test), FIO (numjobs), dbench (scalability test)
- **Quick test:** 2-8 threads/clients | **Long test:** 8-128 threads/clients

---

## Installation

### Prerequisites

| Component | Requirement |
|-----------|-------------|
| OS | Linux (kernel 4.x+) |
| Python | 3.6+ |
| Network | 1 Gbps+ recommended |
| Disk Space | Quick: 100GB, Long: 2TB |

### Install Tools

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip fio iozone bonnie++ dbench nfs-common
pip3 install --user -r requirements.txt
```

**RHEL/CentOS/Fedora:**
```bash
sudo dnf install -y python3 python3-pip fio nfs-utils
sudo dnf install -y epel-release  # For optional tools
sudo dnf install -y iozone bonnie++ dbench
pip3 install --user -r requirements.txt
```

**Automated Setup:**
```bash
git clone https://github.com/skmprabhu252/nfs-benchmark-suite.git
cd nfs-benchmark-suite
./setup_and_verify.sh --auto
```

> **Note:** If tools aren't available, skip them with `--skip-iozone --skip-bonnie --skip-dbench`

---

## Running Tests

### Basic Commands

```bash
# Quick test (15 minutes) - validation
python3 runtest.py --mount-path /mnt/nfs1 --quick-test

# Long test (4-8 hours) - production benchmark
python3 runtest.py --mount-path /mnt/nfs1 --long-test

# Default test (30 minutes) - balanced
python3 runtest.py --mount-path /mnt/nfs1
```

### Common Scenarios

**Custom Configuration:**
```bash
# Copy and modify
cp config/test_config.yaml my_config.yaml
vim my_config.yaml
python3 runtest.py --mount-path /mnt/nfs1 --config my_config.yaml
```

**Skip Missing Tools:**
```bash
# If bonnie++ or dbench not installed
python3 runtest.py --mount-path /mnt/nfs1 --skip-bonnie --skip-dbench
```

**Compare NFS Versions:**
```bash
# Test NFSv3
mount -t nfs -o vers=3,rsize=1048576,wsize=1048576 server:/export /mnt/nfs3
python3 runtest.py --mount-path /mnt/nfs3 --quick-test

# Test NFSv4.2
mount -t nfs -o vers=4.2,rsize=1048576,wsize=1048576 server:/export /mnt/nfs4
python3 runtest.py --mount-path /mnt/nfs4 --quick-test

# Compare results in HTML reports
```

**Test Mount Option Changes:**
```bash
# Baseline
python3 runtest.py --mount-path /mnt/nfs1 --quick-test

# Remount with different options
umount /mnt/nfs1
mount -t nfs -o vers=4.2,rsize=262144,wsize=262144 server:/export /mnt/nfs1
python3 runtest.py --mount-path /mnt/nfs1 --quick-test

# Compare results
```

### Configuration Files

| File | Purpose | Duration | Use When |
|------|---------|----------|----------|
| `config/config_quick_test.yaml` | Validation | 15 min | Setup, CI/CD, troubleshooting |
| `config/config_long_test.yaml` | Production benchmark | 4-8 hours | Baselines, capacity planning |
| `config/test_config.yaml` | Default balanced | 30 min | Regular testing |

---

## Reading Results

### Output Files

After each test run, you get:

| File | Content | Action |
|------|---------|--------|
| `nfs_performance_test_YYYYMMDD_HHMMSS.json` | Raw performance data | Archive for historical tracking |
| `nfs_performance_test_YYYYMMDD_HHMMSS.log` | Detailed execution logs | Use for troubleshooting |
| HTML Report | Interactive charts & analysis | `python3 generate_html_report.py <json_file>` |

### Performance Baselines

**Is your performance good?** Compare against these baselines for 10 GbE networks:

| Metric | 🔴 Needs Work | 🟡 Acceptable | 🟢 Excellent |
|--------|--------------|--------------|--------------|
| Sequential Read | <500 MB/s | 500-800 MB/s | >800 MB/s |
| Sequential Write | <350 MB/s | 350-600 MB/s | >600 MB/s |
| Random Read (4K) | <8K IOPS | 8K-20K IOPS | >20K IOPS |
| Random Write (4K) | <5K IOPS | 5K-15K IOPS | >15K IOPS |
| Latency (avg) | >10ms | 5-10ms | <5ms |
| Metadata ops/sec | <1K | 1K-5K | >5K |

**Adjust for Your Network:**

| Network Speed | Expected Sequential Throughput |
|---------------|-------------------------------|
| 1 GbE | ~100 MB/s |
| 10 GbE | ~1,000 MB/s |
| 25 GbE | ~2,500 MB/s |
| 100 GbE | ~10,000 MB/s |

> **Note:** Actual performance depends on storage backend, server load, and NFS configuration.

### Understanding the Metrics

**Throughput Tests (DD, FIO Sequential)**
- Measures MB/s for large file transfers
- Good for evaluating bulk data transfer performance
- Look for results close to network bandwidth limit (e.g., ~1,100 MB/s for 10 GbE)

**IOPS Tests (FIO Random)**
- Measures operations per second for small random I/O (4K blocks)
- Good for database and application workloads
- Look for consistent IOPS without high latency spikes

**Latency Tests**
- Measures response time in milliseconds
- Good for interactive applications and real-time systems
- Look for low and consistent latency (<5ms average is excellent)

**Metadata Tests (IOzone, Bonnie++)**
- Measures file operations per second (create, delete, stat, rename)
- Good for applications with many small files
- Look for high file creation/deletion rates (>5K ops/sec is excellent)

**Client Simulation (dbench)**
- Measures multi-client throughput and latency
- Good for understanding concurrent user performance
- Look for linear scaling up to 4-8 clients, then plateau

### Historical Tracking

The tool automatically compares results with previous test runs:
- ✅ **Improved** - Performance increased (shown in green)
- ❌ **Regressed** - Performance decreased >10% (shown in red)
- ⚠️ **Warning** - Performance decreased 5-10% (shown in yellow)
- ➡️ **Stable** - Performance within ±5% (shown in gray)

This helps you detect performance degradation over time and validate that configuration changes have the expected impact.

---

## Performance Tuning

### Recommended Mount Options

**Start with these proven settings:**

```bash
# NFSv4.2 (recommended - 10-30% faster than NFSv3)
mount -t nfs -o vers=4.2,rsize=1048576,wsize=1048576,hard,async,noatime server:/export /mnt/nfs1

# NFSv3 (if NFSv4 not available)
mount -t nfs -o vers=3,rsize=1048576,wsize=1048576,hard,async,noatime server:/export /mnt/nfs1
```

### Key Mount Options Explained

- **`vers=4.2`** - Use NFSv4.2 protocol (10-30% faster than NFSv3). Use `vers=3` only if compatibility required.
- **`rsize=1048576`** - 1MB read buffer, optimal for 10 GbE networks. Use `262144` (256KB) for 1 GbE.
- **`wsize=1048576`** - 1MB write buffer, optimal for 10 GbE networks. Use `262144` (256KB) for 1 GbE.
- **`hard`** - Retry indefinitely on failure (prevents data loss). Always use in production.
- **`async`** - Write to cache first (+30-50% write performance). Use `sync` for critical data requiring immediate persistence.
- **`noatime`** - Don't update file access times (-20% metadata operations). Use unless access times needed.

### Tuning by Network Speed

**1 GbE Networks:**
```bash
mount -t nfs -o vers=4.2,rsize=262144,wsize=262144,hard,async,noatime server:/export /mnt/nfs1
```

**10 GbE Networks (most common):**
```bash
mount -t nfs -o vers=4.2,rsize=1048576,wsize=1048576,hard,async,noatime server:/export /mnt/nfs1
```

**25+ GbE Networks:**
```bash
mount -t nfs -o vers=4.2,rsize=1048576,wsize=1048576,hard,async,noatime server:/export /mnt/nfs1
```

### Tuning by Workload

**Latency-Sensitive (databases, real-time apps):**
```bash
mount -t nfs -o vers=4.2,rsize=1048576,wsize=1048576,hard,sync,noatime server:/export /mnt/nfs1
```
Use `sync` to ensure immediate data persistence at the cost of write performance.

**Read-Heavy (media streaming, archives):**
```bash
mount -t nfs -o vers=4.2,rsize=1048576,wsize=1048576,hard,async,noatime,actimeo=600 server:/export /mnt/nfs1
```
Add `actimeo=600` to cache file attributes for 10 minutes, reducing metadata operations.

**Write-Heavy (logs, backups):**
```bash
mount -t nfs -o vers=4.2,rsize=1048576,wsize=1048576,hard,async,noatime server:/export /mnt/nfs1
```
Use `async` for maximum write performance when immediate persistence isn't critical.

### Best Practices

1. ✅ Run tests during maintenance windows (especially long tests)
2. ✅ Ensure no other workloads on NFS mount during testing
3. ✅ Run multiple iterations (3-5) for consistency
4. ✅ Verify network first with `iperf3` before blaming NFS
5. ✅ Monitor NFS server resources during tests
6. ✅ Document mount options and NFS version for comparisons
7. ✅ Use same test profile when comparing configurations

---

## Troubleshooting

### Quick Diagnostics

```bash
# Test write access
touch /mnt/nfs1/test && rm /mnt/nfs1/test

# Check mount
mount | grep nfs

# Test network
ping -c 100 nfs-server
iperf3 -c nfs-server

# Check NFS server
showmount -e nfs-server

# Check errors
dmesg | grep -i nfs

# Check space
df -h /mnt/nfs1
```

### Common Issues

| Problem | Check | Solution |
|---------|-------|----------|
| **Permission Denied** | `touch /mnt/nfs1/test` | Server `/etc/exports` needs `(rw,sync,no_root_squash)` |
| **Low Performance** | `iperf3 -c nfs-server` | • Increase rsize/wsize to 1048576<br>• Use NFSv4.2<br>• Enable async<br>• Check storage backend |
| **Tool Not Found** | `which fio iozone` | Install: `apt-get install fio iozone bonnie++ dbench`<br>Or skip: `--skip-iozone --skip-bonnie` |
| **Test Hangs** | `showmount -e server` | Check NFS server status and network<br>Tool has timeout protection |
| **Disk Space Error** | `df -h /mnt/nfs1` | Quick: need 100GB<br>Long: need 2TB<br>Clean: `rm -rf /mnt/nfs1/*_test` |
| **Inconsistent Results** | Run 3-5 times | • No concurrent workloads<br>• Run during maintenance<br>• Check server load |

---

## Technical Details

### Architecture

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
│  • Mount Path Check    │                        │  • System Metrics      │
│  • Config Validation   │                        │  • NFS Metrics         │
│  • Space Check         │                        │  • Network Stats       │
│  • Permission Check    │                        │  • xprt Statistics     │
└─────────┬──────────────┘                        └───────────┬────────────┘
          │                                                   │
          v                                                   v
┌────────────────────────────────────────────────────────────────┐
│                    Benchmark Modules                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │    DD    │  │   FIO    │  │  IOzone  │  │ Bonnie++ │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│  ┌──────────┐                                                 │
│  │  dbench  │  All inherit from BaseTestTool                  │
│  └──────────┘                                                 │
└────────────┬───────────────────────────────────────────────────┘
             │
             v
┌─────────────────────────────────────────────────────────────────┐
│                    Analysis & Reporting                         │
│  • Performance Analyzer (Root Cause Detection)                  │
│  • Historical Comparison (Regression Detection)                 │
│  • HTML Report Generator (Interactive Charts)                   │
│  • Executive Summary (Intelligent Insights)                     │
└─────────────────────────────────────────────────────────────────┘
```

### Long Test Breakdown

| Tool | Duration | What It Tests |
|------|----------|---------------|
| **DD** | 5 min | Basic sequential I/O sanity check |
| **FIO** | 4.5 hours | • Sequential write: 30 min<br>• Sequential read: 30 min<br>• Random read 4K: 60 min<br>• Random write 4K: 60 min<br>• Mixed randrw: 60 min<br>• Metadata ops: 30 min<br>• Latency: 30 min |
| **IOzone** | 1-2 hours | Filesystem operations and scaling |
| **Bonnie++** | 6-8 hours | • Comprehensive: 4 hours<br>• Fast test: 2 hours<br>• File operations: 1-2 hours |
| **dbench** | 2-3 hours | • Scalability: 80 min<br>• Sustained load: 2 hours<br>• Other tests: 30-40 min |

### Manual Tool Installation

If tools aren't in your repos:

**IOzone:**
```bash
wget http://www.iozone.org/src/current/iozone3_506.tar
tar xf iozone3_506.tar && cd iozone3_506/src/current
make linux && sudo cp iozone /usr/local/bin/
```

**Bonnie++:**
```bash
wget https://www.coker.com.au/bonnie++/bonnie++-2.00a.tgz
tar xzf bonnie++-2.00a.tgz && cd bonnie++-2.00a
./configure && make && sudo make install
```

**dbench:**
```bash
git clone https://github.com/sahlberg/dbench.git && cd dbench
./autogen.sh && ./configure && make && sudo make install
```

---

## Author

**Prabhu Murugesan**  
Email: prabhu.murugesan1@ibm.com

**Version:** 1.0 | **Updated:** 2026-04-04
