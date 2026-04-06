#!/usr/bin/env python3
"""
Create sample JSON data files for testing dimension-based reporting
"""

import json
from datetime import datetime

def create_comprehensive_test_data(test_id, nfs_version, transport="tcp"):
    """Create comprehensive test data with all benchmark results."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return {
        "test_metadata": {
            "server_ip": "192.168.1.100",
            "mount_path": "/export/test",
            "transport": transport,
            "test_mode": "stress_test",
            "versions_tested": [nfs_version],
            "timestamp": datetime.now().isoformat()
        },
        "nfs_version": nfs_version,
        "transport": transport,
        "results": {
            "dd_tests": {
                "write": {"throughput_mbps": 850.5 + (10 if "4" in nfs_version else 0), "time_seconds": 12.3},
                "read": {"throughput_mbps": 920.2 + (15 if "4" in nfs_version else 0), "time_seconds": 11.1},
                "write_direct": {"throughput_mbps": 780.3 + (8 if "4" in nfs_version else 0), "time_seconds": 13.5},
                "read_direct": {"throughput_mbps": 810.7 + (12 if "4" in nfs_version else 0), "time_seconds": 12.8}
            },
            "fio_tests": {
                "sequential_read": {
                    "bandwidth_mbps": 900.5 + (20 if "4" in nfs_version else 0),
                    "iops": 230000 + (5000 if "4" in nfs_version else 0),
                    "latency_ms": 0.45 - (0.05 if "4" in nfs_version else 0)
                },
                "sequential_write": {
                    "bandwidth_mbps": 820.3 + (18 if "4" in nfs_version else 0),
                    "iops": 210000 + (4000 if "4" in nfs_version else 0),
                    "latency_ms": 0.52 - (0.04 if "4" in nfs_version else 0)
                },
                "random_read_4k": {
                    "bandwidth_mbps": 85.2 + (5 if "4" in nfs_version else 0),
                    "iops": 21800 + (500 if "4" in nfs_version else 0),
                    "latency_ms": 2.3 - (0.2 if "4" in nfs_version else 0)
                },
                "random_write_4k": {
                    "bandwidth_mbps": 72.5 + (4 if "4" in nfs_version else 0),
                    "iops": 18560 + (400 if "4" in nfs_version else 0),
                    "latency_ms": 2.8 - (0.15 if "4" in nfs_version else 0)
                },
                "latency_test": {
                    "avg_latency_ms": 1.5 - (0.1 if "4" in nfs_version else 0),
                    "p95_latency_ms": 3.2 - (0.2 if "4" in nfs_version else 0),
                    "p99_latency_ms": 5.8 - (0.3 if "4" in nfs_version else 0)
                }
            },
            "iozone_tests": {
                "write": 850.2 + (12 if "4" in nfs_version else 0),
                "rewrite": 880.5 + (15 if "4" in nfs_version else 0),
                "read": 920.8 + (18 if "4" in nfs_version else 0),
                "reread": 950.3 + (20 if "4" in nfs_version else 0),
                "random_read": 780.5 + (10 if "4" in nfs_version else 0),
                "random_write": 720.3 + (8 if "4" in nfs_version else 0),
                "scaling_results": {
                    "2_threads": 1200.5,
                    "4_threads": 2100.3,
                    "8_threads": 3500.7,
                    "16_threads": 5200.2
                }
            },
            "bonnie_tests": {
                "sequential_output_char": 890.5 + (15 if "4" in nfs_version else 0),
                "sequential_output_block": 920.3 + (18 if "4" in nfs_version else 0),
                "sequential_input_char": 950.2 + (20 if "4" in nfs_version else 0),
                "sequential_input_block": 980.7 + (22 if "4" in nfs_version else 0),
                "random_seeks": 450.5 + (25 if "4" in nfs_version else 0),
                "sequential_create": 8500 + (500 if "4" in nfs_version else 0),
                "sequential_delete": 7200 + (400 if "4" in nfs_version else 0)
            },
            "dbench_tests": {
                "throughput_mbps": 520.3 + (30 if "4" in nfs_version else 0),
                "operations_per_sec": 1250.5 + (100 if "4" in nfs_version else 0),
                "latency_ms": 3.2 - (0.3 if "4" in nfs_version else 0),
                "scalability_results": {
                    "1_client": 520.3,
                    "2_clients": 980.5,
                    "4_clients": 1750.2,
                    "8_clients": 2900.8
                }
            }
        }
    }

def main():
    import os
    
    # Ensure logs directory exists
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    print("Creating sample JSON files for dimension-based reporting tests...\n")
    
    # Scenario 1: Two test-IDs with all NFS versions (for comparison)
    print("1. Creating Test-ID 'baseline_2026' with all NFS versions...")
    for version in ["3", "4.0", "4.1", "4.2"]:
        data = create_comprehensive_test_data("baseline_2026", version)
        filename = f"{logs_dir}/nfs_performance_baseline_2026_nfsv{version}_tcp_20260406_100000.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"   Created: {filename}")
    
    print("\n2. Creating Test-ID 'optimized_2026' with all NFS versions...")
    for version in ["3", "4.0", "4.1", "4.2"]:
        data = create_comprehensive_test_data("optimized_2026", version)
        # Boost performance for optimized version
        data["results"]["dd_tests"]["write"]["throughput_mbps"] += 50
        data["results"]["fio_tests"]["sequential_read"]["bandwidth_mbps"] += 80
        data["results"]["fio_tests"]["random_read_4k"]["iops"] += 2000
        filename = f"{logs_dir}/nfs_performance_optimized_2026_nfsv{version}_tcp_20260406_110000.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"   Created: {filename}")
    
    # Scenario 2: Single version report
    print("\n3. Creating single version report (NFSv4.2 only)...")
    data = create_comprehensive_test_data("single_test", "4.2")
    filename = f"{logs_dir}/nfs_performance_single_test_nfsv4.2_tcp_20260406_120000.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"   Created: {filename}")
    
    # Scenario 3: Multi-version report (one test-ID, multiple versions)
    print("\n4. Creating multi-version report (Test-ID 'multi_version_test')...")
    for version in ["3", "4.1", "4.2"]:
        data = create_comprehensive_test_data("multi_version_test", version)
        filename = f"{logs_dir}/nfs_performance_multi_version_test_nfsv{version}_tcp_20260406_130000.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"   Created: {filename}")
    
    print("\n" + "="*80)
    print("Sample data creation complete!")
    print("="*80)
    print("\nYou can now test the reports with:")
    print("\n# Test 1: Single file report (dimension-based, default)")
    print("python3 generate_html_report.py nfs_performance_single_test_nfsv4.2_tcp_20260406_120000.json")
    
    print("\n# Test 2: Multi-version report (dimension-based, default)")
    print("python3 generate_html_report.py --test-id multi_version_test")
    
    print("\n# Test 3: Comparison report (dimension-based, default)")
    print("python3 generate_html_report.py --test-id baseline_2026 --compare-with optimized_2026")
    
    print("\n# Test 4: Tool-based report (old style)")
    print("python3 generate_html_report.py --test-id baseline_2026 --report-style tool-based")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()

# Made with Bob
