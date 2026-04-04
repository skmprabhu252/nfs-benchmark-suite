# NFS Benchmark Suite Library

Core library modules for the NFS Benchmark Suite. This directory contains benchmark tool implementations and supporting utilities.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Benchmark Tools](#benchmark-tools)
4. [Usage](#usage)
5. [Adding New Tools](#adding-new-tools)
6. [Best Practices](#best-practices)

---

## Overview

The library provides a modular architecture for running performance tests on NFS mounts. All benchmark tools inherit from `BaseTestTool`, ensuring consistency and making it easy to add new tools.

**Key Benefits:**
- **Modular Design**: Each tool is independent and self-contained
- **Consistent Interface**: All tools follow the same pattern
- **Built-in Metrics**: Automatic system metrics collection
- **Easy Extension**: Simple to add new benchmark tools

---

## Architecture

### Directory Structure

```
lib/
├── __init__.py                 # Package initialization
├── core.py                     # BaseTestTool (abstract base class)
├── command_utils.py            # Command execution utilities
├── validation.py               # Input validation
├── nfs_metrics.py             # NFS metrics collection
├── performance_analyzer.py     # Performance analysis
├── historical_comparison.py    # Trend analysis
├── dd_benchmark.py            # DD benchmark implementation
├── fio_benchmark.py           # FIO benchmark implementation
├── iozone_benchmark.py        # IOzone benchmark implementation
├── bonnie_benchmark.py        # Bonnie++ benchmark implementation
└── dbench_benchmark.py        # dbench benchmark implementation
```

### BaseTestTool Class

All benchmark tools inherit from `BaseTestTool` (in `core.py`):

**Required Methods** (must implement):
- `validate_tool()` - Check if tool is installed
- `run_tests()` - Execute all tests
- `cleanup()` - Clean up test files

**Provided Methods** (ready to use):
- `log()` - Logging with different levels
- `_start_metrics_collection()` - Start metrics
- `_stop_metrics_collection()` - Stop and get metrics
- `_validate_throughput()` - Validate against network capacity
- `_attach_metrics_to_result()` - Attach metrics to results
- `_check_test_enabled()` - Check if test is enabled
- `_handle_test_error()` - Handle errors consistently
- `_run_test_with_metrics()` - Run test with automatic metrics

---

## Benchmark Tools

### DD Test Tool (`dd_benchmark.py`)

**Purpose**: Basic sequential I/O performance testing

**Tests:**
- Sequential write (direct I/O)
- Sequential write (sync)
- Sequential read (direct I/O)
- Sequential read (cached)

**When to Use:**
- Quick baseline performance check
- Simple sequential I/O testing
- Verifying basic NFS functionality

**Configuration Example:**
```yaml
dd_tests:
  sequential_write_direct:
    block_size: "1M"
    count: 100000
    flags:
      direct: true
      sync: false
```

---

### FIO Test Tool (`fio_benchmark.py`)

**Purpose**: Comprehensive I/O testing with flexible workload patterns

**Tests:**
- Sequential write/read
- Random read/write (4K blocks)
- Mixed random read/write (70/30)
- Metadata operations
- Latency testing

**When to Use:**
- Detailed I/O performance analysis
- Testing specific workload patterns
- Measuring IOPS and latency
- Database or application workload simulation

**Configuration Example:**
```yaml
fio_tests:
  sequential_write:
    rw: "write"
    bs: "1M"
    size: "4G"
    numjobs: 1
    ioengine: "libaio"
    iodepth: 16
    direct: 1
```

---

### IOzone Test Tool (`iozone_benchmark.py`)

**Purpose**: Filesystem benchmark with comprehensive test scenarios

**Tests:**
1. Baseline throughput (sequential read/write)
2. Cache behavior testing
3. Random I/O (4K operations)
4. Concurrency testing (16 threads)
5. Metadata operations (32 threads)
6. Scaling test (4, 8, 16, 32 threads)
7. Mixed workload

**When to Use:**
- Comprehensive filesystem testing
- Thread scaling analysis
- Cache behavior evaluation
- Multi-threaded performance testing

**Configuration Example:**
```yaml
iozone_tests:
  baseline_throughput:
    file_size: "4g"
    record_size: "1m"
    test_types: [0, 1]  # 0=write, 1=read
    direct_io: true
```

---

### Bonnie++ Test Tool (`bonnie_benchmark.py`)

**Purpose**: Holistic filesystem performance testing

**Tests:**
1. Comprehensive test (full suite)
2. Fast test (block I/O and file operations)
3. File operations (metadata-intensive)

**When to Use:**
- Overall filesystem performance evaluation
- Metadata operation testing
- Comparing different NFS configurations

---

### dbench Test Tool (`dbench_benchmark.py`)

**Purpose**: Client/server simulation using NetBench traces

**Tests:**
1. Light client load (2 clients)
2. Moderate client load (8 clients)
3. Heavy client load (16 clients)
4. Scalability test (1-32 clients)
5. Latency-focused test
6. Sustained load test
7. Rate-limited test
8. Metadata-intensive test

**When to Use:**
- Multi-client performance testing
- Scalability analysis
- Real-world workload simulation
- Concurrent user testing

---

## Usage

### Basic Example

```python
from lib.fio_benchmark import FIOTestTool
from pathlib import Path
import logging

# Setup
mount_path = Path("/mnt/nfs1")
logger = logging.getLogger(__name__)
config = {
    "sequential_write": {
        "rw": "write",
        "bs": "1M",
        "size": "4G",
        "numjobs": 1,
        "ioengine": "libaio",
        "iodepth": 16,
        "direct": 1
    }
}

# Create and run tool
fio_tool = FIOTestTool(
    config=config,
    mount_path=mount_path,
    logger=logger
)

if fio_tool.validate_tool():
    results = fio_tool.run_tests()
    fio_tool.cleanup()
```

### Test Results Format

All tools return results in a consistent format:

```python
{
    "test_name": {
        "status": "passed",  # or "failed"
        "duration_seconds": 120.5,
        "throughput_mbps": 850.2,
        "config": { ... },
        "system_metrics": {
            "cpu": {"avg_percent": 45.2},
            "memory": {"avg_percent": 62.1}
        },
        "nfs_metrics": {
            "operations": { ... },
            "xprt_stats": { ... }
        }
    }
}
```

---

## Adding New Tools

To add a new benchmark tool:

### 1. Create New File

Create `lib/my_tool_benchmark.py`:

```python
from lib.core import BaseTestTool
from typing import Dict, Any

class MyToolTestTool(BaseTestTool):
    def __init__(self, config, mount_path, logger, 
                 metrics_collector=None, network_intel=None):
        super().__init__("mytool", config, mount_path, 
                        logger, metrics_collector, network_intel)
        self.test_dir = self.mount_path / "mytool_test"
        self.results = {}
    
    def validate_tool(self) -> bool:
        """Check if mytool is installed"""
        if not self._check_command("mytool"):
            self.log("mytool not found", "ERROR")
            return False
        return True
    
    def run_tests(self) -> Dict[str, Any]:
        """Run all mytool tests"""
        self.log("Starting MyTool tests", "INFO")
        self.test_dir.mkdir(exist_ok=True)
        
        # Run tests
        for test_name, test_config in self.config.items():
            if self._check_test_enabled(test_name, test_config):
                self._run_my_test(test_name, test_config)
        
        return self.results
    
    def cleanup(self):
        """Clean up test files"""
        self.log("Cleaning up MyTool test directory...", "INFO")
        if self.test_dir.exists():
            subprocess.run(['rm', '-rf', str(self.test_dir)], 
                          check=True)
    
    def _run_my_test(self, test_name: str, test_config: Dict):
        """Run a single test with metrics"""
        result = self._run_test_with_metrics(
            test_name,
            self._execute_test,
            test_config
        )
        self.results[test_name] = result
    
    def _execute_test(self, test_config: Dict) -> Dict[str, Any]:
        """Execute the actual test"""
        # Your test implementation here
        return {
            "throughput_mbps": 850.2,
            "iops": 25000
        }
```

### 2. Update Package

Add to `lib/__init__.py`:
```python
from .my_tool_benchmark import MyToolTestTool
```

### 3. Add Configuration

Add to `config/test_config.yaml`:
```yaml
mytool_tests:
  my_test:
    enabled: true
    # test parameters
```

### 4. Integrate

Add to `runtest.py`:
```python
from lib.my_tool_benchmark import MyToolTestTool

# In main test loop
if not args.skip_mytool:
    mytool = MyToolTestTool(config['mytool_tests'], ...)
    if mytool.validate_tool():
        results['mytool'] = mytool.run_tests()
        mytool.cleanup()
```

---

## Best Practices

### 1. Metrics Collection
Always wrap tests with metrics collection:
```python
def _my_test(self):
    self._start_metrics_collection()
    try:
        # Run test
        pass
    finally:
        metrics = self._stop_metrics_collection()
```

### 2. Error Handling
Use the provided error handler:
```python
try:
    # Run test
    pass
except Exception as e:
    return self._handle_test_error(test_name, e, duration)
```

### 3. Throughput Validation
Validate results against network capacity:
```python
self._validate_throughput(throughput_mbps, "sequential_write")
```

### 4. Logging
Use appropriate log levels:
```python
self.log("Starting test", "INFO")
self.log("Test completed successfully", "SUCCESS")
self.log("Warning: Low performance", "WARNING")
self.log("Test failed", "ERROR")
```

### 5. Cleanup
Always implement proper cleanup:
```python
def cleanup(self):
    if self.test_dir.exists():
        subprocess.run(['rm', '-rf', str(self.test_dir)], check=True)
```

### 6. Configuration
Make tests configurable and document parameters:
```yaml
my_test:
  enabled: true          # Enable/disable test
  file_size: "4G"       # Test file size
  block_size: "1M"      # I/O block size
  direct_io: true       # Use direct I/O
```

---

## Dependencies

**Required:**
- Python 3.7+
- PyYAML

**Optional:**
- psutil (for system metrics)

**Benchmark Tools:**
- dd (coreutils)
- fio
- iozone
- bonnie++
- dbench

**Install:**
```bash
# Ubuntu/Debian
sudo apt-get install coreutils fio iozone bonnie++ dbench

# RHEL/CentOS
sudo yum install coreutils fio iozone bonnie++ dbench

# Python dependencies
pip install pyyaml psutil
```

---

## Author

**Prabhu Murugesan**  
Email: prabhu.murugesan1@ibm.com

**Version:** 1.0 | **Updated:** 2026-04-04