# NFS Benchmark Suite

Comprehensive NFS performance testing suite that measures 6 critical performance dimensions: **Throughput**, **IOPS**, **Latency**, **Metadata Operations**, **Cache Effects**, and **Concurrency Scaling**.

---

## Why Use This Tool?

NFS performance can vary dramatically based on version, configuration, and workload. This suite helps you:

- **Validate NFS Setup** - Quickly verify your NFS configuration is working correctly
- **Compare NFS Versions** - Understand performance differences between NFSv3, v4.0, v4.1, and v4.2
- **Benchmark Production Systems** - Establish performance baselines for capacity planning and SLA verification
- **Identify Bottlenecks** - Pinpoint whether issues are in throughput, IOPS, latency, or metadata operations
- **Track Performance Over Time** - Detect regressions and improvements with historical comparison
- **Optimize Configurations** - Test different mount options and transport protocols (TCP vs RDMA)

---

## Features

- **Automatic NFS Mounting** - No pre-mounting required; just provide server IP and export path. Automatically validates server, mounts with optimal options, and cleans up after testing
- **Multi-Version Testing** - Test NFSv3, v4.0, v4.1, and v4.2 in a single run with automatic performance comparison
- **Two Test Modes** - Quick test (15 min) for validation, Stress test (30 min per version) for production benchmarking
- **Standardized Test Duration** - All stress tests run for consistent 30-minute duration for reliable, comparable results
- **Transport Protocol Support** - TCP (default) and RDMA for high-performance networks (InfiniBand, RoCE)
- **Comprehensive Metrics** - Measures 6 critical dimensions: Throughput, IOPS, Latency, Metadata Ops, Cache Effects, and Concurrency Scaling
- **Historical Tracking** - Automatic comparison with previous test runs to identify performance regressions
- **Interactive HTML Reports** - Generate visual reports with charts and analysis using `generate_html_report.py`

---

## Performance Dimensions Measured

### 1. Throughput (MB/s)
Sequential data transfer rate for large files. Critical for bulk operations, backups, and media streaming.
- **Tools:** DD, FIO (sequential), IOzone, Bonnie++
- **Quick test:** 500MB-2GB files | **Stress test:** 8GB-64GB files, 30-minute runtime

### 2. IOPS (Operations/Second)
Random I/O performance with small blocks (4K). Essential for databases and VMs.
- **Tools:** FIO (random 4K), IOzone (random I/O)
- **Quick test:** 60 seconds | **Stress test:** 30-minute runtime

### 3. Latency (milliseconds)
Response time for I/O operations. Critical for interactive applications and real-time systems.
- **Tools:** FIO (latency test), dbench (single client)
- **Quick test:** 30 seconds | **Stress test:** 30-minute runtime

### 4. Metadata Operations/Second
File creation, deletion, stat, rename operations. Important for build systems and applications with many small files.
- **Tools:** FIO (metadata), IOzone, Bonnie++, dbench
- **Quick test:** 1K-8K files | **Stress test:** 50K-256K files, 30-minute runtime

### 5. Cache Effects
Performance difference between cached and direct I/O. Helps understand and tune client-side caching.
- **Tools:** DD (cached vs direct), IOzone, FIO (direct vs buffered)
- **Quick test:** 500MB-1GB files | **Stress test:** 16GB-32GB files, 30-minute runtime

### 6. Concurrency Scaling
Performance scaling with multiple concurrent clients. Essential for multi-user environments and capacity planning.
- **Tools:** IOzone (scaling), FIO (numjobs), dbench (scalability)
- **Quick test:** 2-8 threads | **Stress test:** 8-128 threads, 30-minute runtime

---

## Architecture

```
runtest.py (Main Orchestrator)
    │
    ├── Input Validation (mount, config, space, permissions)
    │
    ├── Benchmark Modules
    │   ├── DD (basic sequential I/O)
    │   ├── FIO (comprehensive I/O testing)
    │   ├── IOzone (filesystem operations)
    │   ├── Bonnie++ (file operations)
    │   └── dbench (client simulation)
    │
    ├── Metrics Collection
    │   ├── System metrics
    │   ├── NFS metrics
    │   └── Network stats
    │
    └── Analysis & Reporting
        ├── Performance analyzer
        ├── Historical comparison
        ├── HTML report generator
        └── Executive summary
```

---

## Requirements

- **OS:** Linux (kernel 4.x+)
- **Python:** 3.6+
- **Access:** Root/sudo (for NFS mount operations)
- **Network:** 1 Gbps+ recommended (10 GbE for production benchmarks)
- **Disk Space:** 100GB (quick test) or 2TB (stress test)
- **NFS Server:** Configured exports with appropriate permissions

---

## Installation

### Install Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip fio iozone bonnie++ dbench nfs-common
pip3 install --user -r requirements.txt
```

**RHEL/CentOS/Fedora:**
```bash
sudo dnf install -y python3 python3-pip fio nfs-utils epel-release
sudo dnf install -y iozone bonnie++ dbench
pip3 install --user -r requirements.txt
```

**Automated Setup:**
```bash
./setup_and_verify.sh --auto
```

### RDMA Requirements (Optional)

To use `--transport rdma` for high-performance networks:

**Hardware:**
- InfiniBand or RoCE (RDMA over Converged Ethernet) network adapter
- RDMA-capable NFS server

**Software (Client):**
```bash
# Ubuntu/Debian
sudo apt-get install rdma-core libibverbs1 ibverbs-providers

# RHEL/CentOS
sudo dnf install rdma-core libibverbs

# Load RDMA kernel modules
sudo modprobe rdma_cm
sudo modprobe ib_core
sudo modprobe ib_uverbs
```

**Software (Server):**
```bash
# Enable NFS-RDMA on server
sudo modprobe svcrdma
echo "rdma 20049" >> /etc/nfs.conf
sudo systemctl restart nfs-server
```

**Verification:**
```bash
# Check RDMA devices
ls /sys/class/infiniband/

# Check RDMA modules
lsmod | grep rdma

# Test RDMA connectivity
rping -s -a 0.0.0.0 -v -C 10  # On server
rping -c -a <server-ip> -v -C 10  # On client
```

---

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/skmprabhu252/nfs-benchmark-suite.git
cd nfs-benchmark-suite
./setup_and_verify.sh --auto

# 2. Run quick validation test (15 minutes) - NFSv3 with TCP
sudo python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --test-id baseline --quick-test

# 3. Generate HTML report
python3 generate_html_report.py --test-id baseline
```

**Note:** The tool automatically mounts NFS and must run as root.

---

## Usage

### Two Test Modes

#### Quick Test (~15 minutes per version)
**Purpose:** Validation and smoke testing  
**Use for:** Initial setup, CI/CD, troubleshooting, verifying changes  
**Resources:** 50-100 GB disk space, ~20-30 GB data written  
**Configuration:** Small files (500MB-2GB), low concurrency (2-8 threads)  
**Default:** Tests NFSv3 only (use `--nfs-versions` to test specific versions)

#### Stress Test (~30 minutes per version)
**Purpose:** Production benchmarking and capacity planning  
**Use for:** Performance baselines, SLA verification, capacity planning  
**Resources:** 1-2 TB disk space per version, ~500GB-1TB data written  
**Configuration:** Large files (8GB-64GB), high concurrency (8-128 threads), **all tests run for 30 minutes**  
**Default:** Tests all versions (v3, v4.0, v4.1, v4.2) - total time: ~2 hours

Both modes measure the same 6 performance dimensions, but with different scale and duration. The tool automatically mounts each NFS version, runs tests, and unmounts before testing the next version.

### Basic Usage

**Important:** The tool requires `--server-ip` and `--mount-path` (server export path). It automatically handles mounting and unmounting.

```bash
# Quick test - NFSv3 with TCP (default, ~15 minutes)
sudo python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --test-id baseline --quick-test

# Stress test - All versions with TCP (v3, v4.0, v4.1, v4.2, ~2 hours)
sudo python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --test-id prod_2026 --stress-test

# Test specific NFS versions with test-id for comparison
sudo python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --test-id eval --nfs-versions 3,4.2 --quick-test

# Test with RDMA transport (requires RDMA hardware)
sudo python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --test-id rdma_test --transport rdma --quick-test

# Test each version separately (flexible comparison later)
sudo python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --test-id baseline --nfs-versions 3 --quick-test
sudo python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --test-id baseline --nfs-versions 4.2 --quick-test
```

### Common Scenarios

**Custom Configuration:**
```bash
cp config/test_config.yaml my_config.yaml
vim my_config.yaml
sudo python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --config my_config.yaml --quick-test
```

**Skip Missing Tools:**
```bash
sudo python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --skip-bonnie --skip-dbench --quick-test
```

**Compare NFS Versions:**
```bash
# Test multiple versions with same test-id for comparison
sudo python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --test-id comparison --nfs-versions 3,4.2 --quick-test

# Or test versions separately and compare later
sudo python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --test-id comparison --nfs-versions 3 --quick-test
sudo python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --test-id comparison --nfs-versions 4.2 --quick-test

# Generate comparison report
python3 generate_html_report.py --test-id comparison
```

**Test with RDMA for High-Performance Networks:**
```bash
# Quick test with RDMA
sudo python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --transport rdma --quick-test

# Stress test all versions with RDMA
sudo python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --transport rdma --stress-test
```

**Production Benchmark Workflow:**
```bash
# 1. Quick validation first
sudo python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --test-id prod_baseline --quick-test

# 2. If successful, run comprehensive benchmark
sudo python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --test-id prod_baseline --stress-test

# 3. Generate comparison report
python3 generate_html_report.py --test-id prod_baseline
```

---

## Configuration

### Configuration Files

- `config/config_quick_test.yaml` - Quick test (15 min)
- `config/config_stress_test.yaml` - Stress test (30 min per version, all tests standardized)
- `config/test_config.yaml` - Default balanced (30 min)

### Mount Options Used by the Tool

The tool automatically uses optimized mount options for each version and transport:

**TCP Transport:**
- NFSv3: `vers=3,proto=tcp,rsize=1048576,wsize=1048576,hard,async,noatime`
- NFSv4.x: `vers=4.x,proto=tcp,rsize=1048576,wsize=1048576,hard,async,noatime`

**RDMA Transport:**
- NFSv3: `vers=3,proto=rdma,port=20049,rsize=1048576,wsize=1048576,hard,async,noatime`
- NFSv4.x: `vers=4.x,proto=rdma,port=20049,rsize=1048576,wsize=1048576,hard,async,noatime`

### Key Options Explained
- `vers=X` - NFS protocol version
- `proto=tcp/rdma` - Transport protocol
- `port=20049` - RDMA port (default for NFS-RDMA)
- `rsize/wsize=1048576` - 1MB buffers for 10 GbE (optimal for high-speed networks)
- `hard` - Retry on failure (prevents data loss)
- `async` - Write to cache first (+30-50% write performance)
- `noatime` - Don't update access times (-20% metadata ops)

### Tuning by Workload

**Latency-Sensitive (databases):**
```bash
mount -t nfs -o vers=4.2,rsize=1048576,wsize=1048576,hard,sync,noatime server:/export /mnt/nfs1
```

**Read-Heavy (media, archives):**
```bash
mount -t nfs -o vers=4.2,rsize=1048576,wsize=1048576,hard,async,noatime,actimeo=600 server:/export /mnt/nfs1
```

**Write-Heavy (logs, backups):**
```bash
mount -t nfs -o vers=4.2,rsize=1048576,wsize=1048576,hard,async,noatime server:/export /mnt/nfs1
```

---

## Understanding Results

### Output Files

**Separate Files Per Version:**
- `nfs_performance_{test_id}_nfsv3_tcp_YYYYMMDD_HHMMSS.json` - NFSv3 results
- `nfs_performance_{test_id}_nfsv42_tcp_YYYYMMDD_HHMMSS.json` - NFSv4.2 results
- `nfs_performance_test_YYYYMMDD_HHMMSS.log` - Detailed execution logs
- HTML Report - Interactive charts and analysis (generate with `generate_html_report.py --test-id {test_id}`)

### Individual Result File Structure
```json
{
  "test_metadata": {
    "server_ip": "192.168.1.100",
    "mount_path": "/export/data",
    "transport": "tcp",
    "test_id": "baseline"
  },
  "nfs_version": "3",
  "transport": "tcp",
  "results": {
    "dd_tests": { /* DD test results */ },
    "fio_tests": { /* FIO test results */ },
    "iozone_tests": { /* IOzone test results */ },
    "bonnie_tests": { /* Bonnie++ test results */ },
    "dbench_tests": { /* dbench test results */ }
  }
}
```

### Performance Baselines (10 GbE Network)

**Good Performance Indicators:**
- Sequential Read: >800 MB/s
- Sequential Write: >600 MB/s
- Random Read (4K): >20K IOPS
- Random Write (4K): >15K IOPS
- Latency (avg): <5ms
- Metadata ops/sec: >5K

**Network Speed Reference:**
- 1 GbE: ~100 MB/s
- 10 GbE: ~1,000 MB/s
- 25 GbE: ~2,500 MB/s
- 100 GbE: ~10,000 MB/s

### Historical Tracking
The tool automatically compares results with previous runs:
- ✅ **Improved** - Performance increased
- ❌ **Regressed** - Performance decreased >10%
- ⚠️ **Warning** - Performance decreased 5-10%
- ➡️ **Stable** - Performance within ±5%

---

## Best Practices

1. **Run tests during maintenance windows** - Avoid production workloads during benchmarking
2. **Ensure no other workloads during testing** - Isolate the NFS mount for accurate results
3. **Run multiple iterations (3-5) for consistency** - Average results across runs
4. **Verify network with `iperf3` before testing** - Ensure network is not the bottleneck
5. **Monitor NFS server resources during tests** - Check CPU, memory, disk I/O on server
6. **Document mount options for comparisons** - Keep track of configuration changes
7. **Use same test profile when comparing** - Use consistent test modes (quick vs stress)
8. **Start with quick test** - Validate setup before running long stress tests
9. **Compare same NFS versions** - Use test-id to group related test runs
10. **Review HTML reports** - Visual analysis helps identify patterns and anomalies

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

**Permission Denied:**
- Check: `touch /mnt/nfs1/test`
- Fix: Server `/etc/exports` needs `(rw,sync,no_root_squash)`

**Low Performance:**
- Check: `iperf3 -c nfs-server`
- Fix: Increase rsize/wsize to 1048576, use NFSv4.2, enable async

**Tool Not Found:**
- Check: `which fio iozone`
- Fix: Install tools or use `--skip-iozone --skip-bonnie`

**Disk Space Error:**
- Check: `df -h /mnt/nfs1`
- Fix: Quick needs 100GB, Stress needs 2TB

**Mount Fails:**
- Check: `showmount -e <server-ip>`
- Fix: Verify NFS server is running and export is configured

**RDMA Not Working:**
- Check: `ls /sys/class/infiniband/`
- Fix: Install RDMA drivers and load kernel modules

---

## Author

**Prabhu Murugesan**  
Email: prabhu.murugesan1@ibm.com

**Version:** 1.0 | **Updated:** 2026-04-05
