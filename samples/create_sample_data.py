#!/usr/bin/env python3
"""
Create sample JSON data files for testing dimension-based reporting
This script generates data matching the actual NFS benchmark suite output format
"""

import json
from datetime import datetime
import random

def create_system_metrics(base_cpu=20, base_mem=34):
    """Create realistic system metrics."""
    return {
        "cpu": {
            "avg_percent": base_cpu + random.uniform(-5, 5),
            "max_percent": base_cpu + random.uniform(10, 20),
            "min_percent": max(0, base_cpu - random.uniform(5, 10))
        },
        "memory": {
            "avg_percent": base_mem + random.uniform(-2, 2),
            "max_percent": base_mem + random.uniform(0, 3),
            "min_percent": base_mem - random.uniform(0, 2)
        },
        "disk_io": {
            "read_rate_mbps": random.uniform(0, 600),
            "write_rate_mbps": random.uniform(0, 100)
        },
        "network_io": {
            "sent_rate_mbps": random.uniform(40, 300),
            "recv_rate_mbps": random.uniform(40, 300)
        },
        "samples_collected": random.randint(15, 120),
        "interface_stats": {
            "interface": "eth0",
            "duration_seconds": random.uniform(10, 120),
            "throughput": {
                "sent_mbps": 0.0,
                "recv_mbps": 0.0,
                "total_mbps": 0.0
            },
            "packets": {
                "sent_total": 0,
                "recv_total": random.randint(100, 3000),
                "sent_per_sec": 0.0,
                "recv_per_sec": random.uniform(10, 30)
            },
            "errors": {"total": 0, "per_sec": 0.0, "input": 0, "output": 0},
            "drops": {"total": 0, "per_sec": 0.0, "input": 0, "output": 0}
        }
    }

def create_nfs_metrics(test_type="write"):
    """Create realistic NFS metrics."""
    ops_count = random.randint(10000, 50000)
    return {
        "collection_available": True,
        "start_metrics": {
            "nfs_client": {
                "operations": {"readlink": 0, "write": 0, "mkdir": 0},
                "total_ops": 0
            },
            "rpc": {
                "calls": 0,
                "retransmissions": 0,
                "timeouts": 0,
                "invalid_replies": 0,
                "retrans_percent": 0.0
            },
            "mountstats": {
                "bytes_read": 0,
                "bytes_written": 0,
                "read_ops": 0,
                "write_ops": 0,
                "rpc_backlog": 0,
                "rpc_ops": {},
                "rpc_latency": {},
                "xprt": {
                    "protocol": "tcp",
                    "srcport": random.randint(600, 900),
                    "bind_count": 1,
                    "connect_count": 2,
                    "connect_time": 0,
                    "idle_time": 0,
                    "sends": random.randint(5, 20),
                    "recvs": random.randint(5, 20),
                    "bad_xids": 0,
                    "req_queue_time": random.randint(5, 20),
                    "resp_queue_time": 0,
                    "max_slots": 2,
                    "sending_queue": 0,
                    "pending_queue": 0
                }
            }
        },
        "end_metrics": {
            "nfs_client": {
                "operations": {"readlink": 0, "write": 0, "mkdir": ops_count},
                "total_ops": ops_count
            },
            "rpc": {
                "calls": 0,
                "retransmissions": 0,
                "timeouts": 0,
                "invalid_replies": 0,
                "retrans_percent": 0.0
            },
            "mountstats": {
                "bytes_read": 0 if test_type == "write" else ops_count * 1024 * 256,
                "bytes_written": ops_count * 1024 * 256 if test_type == "write" else 0,
                "read_ops": 0 if test_type == "write" else ops_count,
                "write_ops": ops_count if test_type == "write" else 0,
                "rpc_backlog": 0,
                "rpc_ops": {},
                "rpc_latency": {},
                "xprt": {
                    "protocol": "tcp",
                    "srcport": random.randint(600, 900),
                    "bind_count": 1,
                    "connect_count": 2,
                    "connect_time": 0,
                    "idle_time": 0,
                    "sends": ops_count + random.randint(100, 500),
                    "recvs": ops_count + random.randint(100, 500),
                    "bad_xids": 0,
                    "req_queue_time": random.randint(10000, 60000),
                    "resp_queue_time": 0,
                    "max_slots": 4,
                    "sending_queue": random.randint(10000, 30000),
                    "pending_queue": random.randint(10000, 30000)
                }
            }
        },
        "deltas": {
            "rpc": {
                "calls": 0,
                "retransmissions": 0,
                "timeouts": 0,
                "invalid_replies": 0
            },
            "mountstats": {
                "bytes_read": 0 if test_type == "write" else ops_count * 1024 * 256,
                "bytes_written": ops_count * 1024 * 256 if test_type == "write" else 0,
                "read_ops": 0 if test_type == "write" else ops_count,
                "write_ops": ops_count if test_type == "write" else 0
            },
            "xprt": {},
            "per_op_stats": {},
            "nfs_operations": {"mkdir": ops_count, "readlink": 0, "write": 0}
        },
        "rates": {
            "rpc": {
                "calls_per_sec": 0.0,
                "retransmissions_per_sec": 0.0,
                "timeouts_per_sec": 0.0,
                "invalid_replies_per_sec": 0.0
            },
            "throughput": {
                "read_mbps": 0.0 if test_type == "write" else random.uniform(100, 300),
                "write_mbps": random.uniform(30, 100) if test_type == "write" else 0.0,
                "read_iops": 0.0 if test_type == "write" else random.uniform(500, 2000),
                "write_iops": random.uniform(500, 1500) if test_type == "write" else 0.0
            },
            "xprt": {
                "connects_per_sec": 0.0,
                "sends_per_sec": random.uniform(500, 1500),
                "recvs_per_sec": random.uniform(500, 1500),
                "bad_xids_per_sec": 0.0,
                "protocol": "tcp",
                "max_slots": random.randint(400, 600),
                "sending_queue": random.randint(1000000, 3000000),
                "pending_queue": random.randint(400000, 500000)
            }
        },
        "issues": [],
        "sample_count": random.randint(15, 25),
        "collection_duration": random.uniform(15, 25)
    }

def create_comprehensive_test_data(test_id, nfs_version, transport="tcp"):
    """Create comprehensive test data matching actual benchmark suite format."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Performance boost for NFSv4.x
    v4_boost = 1.15 if "4" in nfs_version else 1.0
    
    return {
        "nfs_version": nfs_version,
        "transport": transport,
        "test_metadata": {
            "test_id": test_id,
            "server_ip": "10.11.28.193",
            "mount_path": f"/mnt/nfs_benchmark_mount/nfsv{nfs_version}_{transport}",
            "transport": transport,
            "test_mode": "comprehensive",
            "versions_tested": [nfs_version],
            "timestamp": datetime.now().isoformat()
        },
        "test_run": {
            "timestamp": datetime.now().isoformat(),
            "mount_path": f"/mnt/nfs_benchmark_mount/nfsv{nfs_version}_{transport}",
            "hostname": "nfbm1.fyre.ibm.com",
            "network_config": {
                "nfs_server_ip": "10.11.28.193",
                "local_ip": "10.11.28.193",
                "interface": "eth0",
                "interface_details": {
                    "speed_mbps": 1000,
                    "duplex": "Full",
                    "mtu": 1500,
                    "driver": "virtio_net"
                },
                "theoretical_max_throughput_mbps": 125.0
            }
        },
        "dd_tests": {
            "sequential_write_direct": {
                "status": "passed",
                "duration_seconds": random.uniform(100, 130),
                "throughput_mbps": round(35.0 * v4_boost + random.uniform(-5, 5), 1),
                "size_mb": 5000,
                "block_size": "1M",
                "count": 5000,
                "flags": {"direct_io": True, "synchronized": False},
                "system_metrics": create_system_metrics(20, 34),
                "nfs_metrics": create_nfs_metrics("write")
            },
            "sequential_write_sync": {
                "status": "passed",
                "duration_seconds": random.uniform(15, 25),
                "throughput_mbps": round(200.0 * v4_boost + random.uniform(-20, 20), 1),
                "size_mb": 5000,
                "block_size": "1M",
                "count": 5000,
                "flags": {"direct_io": False, "synchronized": True},
                "system_metrics": create_system_metrics(50, 35),
                "nfs_metrics": create_nfs_metrics("write")
            },
            "sequential_read_direct": {
                "status": "passed",
                "duration_seconds": random.uniform(15, 25),
                "throughput_mbps": round(210.0 * v4_boost + random.uniform(-20, 20), 1),
                "size_mb": 5000,
                "block_size": "1M",
                "count": 5000,
                "flags": {"direct_io": True, "cached": False},
                "system_metrics": create_system_metrics(55, 35),
                "nfs_metrics": create_nfs_metrics("read")
            },
            "sequential_read_cached": {
                "status": "passed",
                "duration_seconds": random.uniform(10, 20),
                "throughput_mbps": round(250.0 * v4_boost + random.uniform(-30, 30), 1),
                "size_mb": 5000,
                "block_size": "1M",
                "count": 5000,
                "flags": {"direct_io": False, "cached": True},
                "system_metrics": create_system_metrics(60, 36),
                "nfs_metrics": create_nfs_metrics("read")
            }
        },
        "fio_tests": {
            "sequential_write": {
                "status": "passed",
                "read_iops": 0,
                "write_iops": int(50000 * v4_boost + random.uniform(-5000, 5000)),
                "read_bandwidth_mbps": 0.0,
                "write_bandwidth_mbps": round(195.0 * v4_boost + random.uniform(-20, 20), 1),
                "read_latency_ms": 0.0,
                "write_latency_ms": round(0.02 / v4_boost + random.uniform(-0.005, 0.005), 3),
                "system_metrics": create_system_metrics(45, 35),
                "nfs_metrics": create_nfs_metrics("write")
            },
            "sequential_read": {
                "status": "passed",
                "read_iops": int(55000 * v4_boost + random.uniform(-5000, 5000)),
                "write_iops": 0,
                "read_bandwidth_mbps": round(215.0 * v4_boost + random.uniform(-20, 20), 1),
                "write_bandwidth_mbps": 0.0,
                "read_latency_ms": round(0.018 / v4_boost + random.uniform(-0.003, 0.003), 3),
                "write_latency_ms": 0.0,
                "system_metrics": create_system_metrics(50, 35),
                "nfs_metrics": create_nfs_metrics("read")
            },
            "random_read_4k": {
                "status": "passed",
                "read_iops": int(12000 * v4_boost + random.uniform(-1000, 1000)),
                "write_iops": 0,
                "read_bandwidth_mbps": round(47.0 * v4_boost + random.uniform(-5, 5), 1),
                "write_bandwidth_mbps": 0.0,
                "read_latency_ms": round(0.083 / v4_boost + random.uniform(-0.01, 0.01), 3),
                "write_latency_ms": 0.0,
                "system_metrics": create_system_metrics(40, 34),
                "nfs_metrics": create_nfs_metrics("read")
            },
            "random_write_4k": {
                "status": "passed",
                "read_iops": 0,
                "write_iops": int(10000 * v4_boost + random.uniform(-1000, 1000)),
                "read_bandwidth_mbps": 0.0,
                "write_bandwidth_mbps": round(39.0 * v4_boost + random.uniform(-5, 5), 1),
                "read_latency_ms": 0.0,
                "write_latency_ms": round(0.1 / v4_boost + random.uniform(-0.01, 0.01), 3),
                "system_metrics": create_system_metrics(35, 34),
                "nfs_metrics": create_nfs_metrics("write")
            },
            "mixed_randrw_70_30": {
                "status": "passed",
                "read_iops": int(8000 * v4_boost + random.uniform(-800, 800)),
                "write_iops": int(3500 * v4_boost + random.uniform(-350, 350)),
                "read_bandwidth_mbps": round(31.0 * v4_boost + random.uniform(-3, 3), 1),
                "write_bandwidth_mbps": round(14.0 * v4_boost + random.uniform(-2, 2), 1),
                "read_latency_ms": round(0.125 / v4_boost + random.uniform(-0.015, 0.015), 3),
                "write_latency_ms": round(0.286 / v4_boost + random.uniform(-0.03, 0.03), 3),
                "system_metrics": create_system_metrics(42, 35),
                "nfs_metrics": create_nfs_metrics("write")
            },
            "metadata_operations": {
                "status": "passed",
                "read_iops": int(5000 * v4_boost + random.uniform(-500, 500)),
                "write_iops": int(5000 * v4_boost + random.uniform(-500, 500)),
                "read_bandwidth_mbps": round(20.0 * v4_boost + random.uniform(-2, 2), 1),
                "write_bandwidth_mbps": round(20.0 * v4_boost + random.uniform(-2, 2), 1),
                "read_latency_ms": round(0.2 / v4_boost + random.uniform(-0.02, 0.02), 3),
                "write_latency_ms": round(0.2 / v4_boost + random.uniform(-0.02, 0.02), 3),
                "system_metrics": create_system_metrics(38, 34),
                "nfs_metrics": create_nfs_metrics("write")
            },
            "latency_test": {
                "status": "passed",
                "read_iops": int(15000 * v4_boost + random.uniform(-1500, 1500)),
                "write_iops": 0,
                "read_bandwidth_mbps": round(59.0 * v4_boost + random.uniform(-6, 6), 1),
                "write_bandwidth_mbps": 0.0,
                "read_latency_ms": round(0.067 / v4_boost + random.uniform(-0.008, 0.008), 3),
                "write_latency_ms": 0.0,
                "system_metrics": create_system_metrics(45, 35),
                "nfs_metrics": create_nfs_metrics("read")
            }
        },
        "iozone_tests": {
            "baseline_throughput": {
                "status": "passed",
                "duration_seconds": random.uniform(50, 80),
                "config": {"file_size_kb": 1048576, "record_size_kb": 16384},
                "write_throughput_mbps": round(180.0 * v4_boost + random.uniform(-20, 20), 1),
                "rewrite_throughput_mbps": round(185.0 * v4_boost + random.uniform(-20, 20), 1),
                "read_throughput_mbps": round(200.0 * v4_boost + random.uniform(-20, 20), 1),
                "reread_throughput_mbps": round(210.0 * v4_boost + random.uniform(-20, 20), 1),
                "file_size_kb": 1048576,
                "record_size_kb": 16384,
                "system_metrics": create_system_metrics(50, 35),
                "nfs_metrics": create_nfs_metrics("write")
            },
            "cache_behavior": {
                "status": "passed",
                "duration_seconds": random.uniform(40, 70),
                "config": {"file_size_kb": 524288, "record_size_kb": 4096},
                "write_throughput_mbps": round(175.0 * v4_boost + random.uniform(-20, 20), 1),
                "rewrite_throughput_mbps": round(180.0 * v4_boost + random.uniform(-20, 20), 1),
                "read_throughput_mbps": round(195.0 * v4_boost + random.uniform(-20, 20), 1),
                "reread_throughput_mbps": round(205.0 * v4_boost + random.uniform(-20, 20), 1),
                "file_size_kb": 524288,
                "record_size_kb": 4096,
                "system_metrics": create_system_metrics(48, 35),
                "nfs_metrics": create_nfs_metrics("write")
            },
            "random_io_4k": {
                "status": "passed",
                "duration_seconds": random.uniform(60, 90),
                "config": {"file_size_kb": 262144, "record_size_kb": 4},
                "write_throughput_mbps": round(35.0 * v4_boost + random.uniform(-5, 5), 1),
                "rewrite_throughput_mbps": round(38.0 * v4_boost + random.uniform(-5, 5), 1),
                "read_throughput_mbps": round(42.0 * v4_boost + random.uniform(-5, 5), 1),
                "reread_throughput_mbps": round(45.0 * v4_boost + random.uniform(-5, 5), 1),
                "random_read_throughput_mbps": round(40.0 * v4_boost + random.uniform(-5, 5), 1),
                "file_size_kb": 262144,
                "record_size_kb": 4,
                "system_metrics": create_system_metrics(42, 34),
                "nfs_metrics": create_nfs_metrics("write")
            },
            "concurrency_16_threads": {
                "status": "passed",
                "duration_seconds": random.uniform(70, 100),
                "config": {"threads": 16, "file_size_kb": 131072, "record_size_kb": 16384},
                "write_throughput_mbps": round(320.0 * v4_boost + random.uniform(-30, 30), 1),
                "read_throughput_mbps": round(350.0 * v4_boost + random.uniform(-35, 35), 1),
                "system_metrics": create_system_metrics(75, 38),
                "nfs_metrics": create_nfs_metrics("write")
            },
            "metadata_operations": {
                "status": "passed",
                "duration_seconds": random.uniform(30, 50),
                "config": {"file_size_kb": 4096, "record_size_kb": 4},
                "write_throughput_mbps": round(25.0 * v4_boost + random.uniform(-3, 3), 1),
                "read_throughput_mbps": round(30.0 * v4_boost + random.uniform(-3, 3), 1),
                "system_metrics": create_system_metrics(35, 34),
                "nfs_metrics": create_nfs_metrics("write")
            },
            "scaling_test": {
                "status": "passed",
                "scaling_results": {
                    "1_threads": {
                        "status": "passed",
                        "duration_seconds": random.uniform(15, 25),
                        "config": {"file_size": "256m", "record_size": "1m", "threads": 1, "direct_io": True, "test_types": [0, 1]},
                        "write_throughput_mbps": round(180.0 * v4_boost, 1),
                        "read_throughput_mbps": round(200.0 * v4_boost, 1),
                        "system_metrics": create_system_metrics(30, 34),
                        "nfs_metrics": create_nfs_metrics("write")
                    },
                    "2_threads": {
                        "status": "passed",
                        "duration_seconds": random.uniform(15, 25),
                        "config": {"file_size": "256m", "record_size": "1m", "threads": 2, "direct_io": True, "test_types": [0, 1]},
                        "write_throughput_mbps": round(280.0 * v4_boost, 1),
                        "read_throughput_mbps": round(310.0 * v4_boost, 1),
                        "system_metrics": create_system_metrics(45, 35),
                        "nfs_metrics": create_nfs_metrics("write")
                    },
                    "4_threads": {
                        "status": "passed",
                        "duration_seconds": random.uniform(15, 25),
                        "config": {"file_size": "256m", "record_size": "1m", "threads": 4, "direct_io": True, "test_types": [0, 1]},
                        "write_throughput_mbps": round(350.0 * v4_boost, 1),
                        "read_throughput_mbps": round(380.0 * v4_boost, 1),
                        "system_metrics": create_system_metrics(60, 36),
                        "nfs_metrics": create_nfs_metrics("write")
                    },
                    "8_threads": {
                        "status": "passed",
                        "duration_seconds": random.uniform(15, 25),
                        "config": {"file_size": "256m", "record_size": "1m", "threads": 8, "direct_io": True, "test_types": [0, 1]},
                        "write_throughput_mbps": round(420.0 * v4_boost, 1),
                        "read_throughput_mbps": round(450.0 * v4_boost, 1),
                        "system_metrics": create_system_metrics(75, 38),
                        "nfs_metrics": create_nfs_metrics("write")
                    }
                }
            },
            "mixed_workload": {
                "status": "passed",
                "duration_seconds": random.uniform(50, 80),
                "config": {"file_size_kb": 524288, "record_size_kb": 8192},
                "write_throughput_mbps": round(160.0 * v4_boost + random.uniform(-20, 20), 1),
                "read_throughput_mbps": round(185.0 * v4_boost + random.uniform(-20, 20), 1),
                "system_metrics": create_system_metrics(52, 35),
                "nfs_metrics": create_nfs_metrics("write")
            }
        },
        "bonnie_tests": {
            "comprehensive_test": {
                "status": "passed",
                "duration_seconds": random.uniform(200, 300),
                "sequential_output_char_kbps": int(180000 * v4_boost + random.uniform(-20000, 20000)),
                "sequential_output_char_mbps": round(175.0 * v4_boost + random.uniform(-20, 20), 1),
                "sequential_output_block_kbps": int(190000 * v4_boost + random.uniform(-20000, 20000)),
                "sequential_output_block_mbps": round(185.0 * v4_boost + random.uniform(-20, 20), 1),
                "sequential_rewrite_kbps": int(195000 * v4_boost + random.uniform(-20000, 20000)),
                "sequential_rewrite_mbps": round(190.0 * v4_boost + random.uniform(-20, 20), 1),
                "sequential_input_char_kbps": int(200000 * v4_boost + random.uniform(-20000, 20000)),
                "sequential_input_char_mbps": round(195.0 * v4_boost + random.uniform(-20, 20), 1),
                "sequential_input_block_kbps": int(210000 * v4_boost + random.uniform(-20000, 20000)),
                "sequential_input_block_mbps": round(205.0 * v4_boost + random.uniform(-20, 20), 1),
                "random_seeks_per_sec": round(450.0 * v4_boost + random.uniform(-50, 50), 1),
                "file_create_seq_per_sec": int(8000 * v4_boost + random.uniform(-800, 800)),
                "file_stat_seq_per_sec": int(12000 * v4_boost + random.uniform(-1200, 1200)),
                "file_delete_seq_per_sec": int(7000 * v4_boost + random.uniform(-700, 700)),
                "file_create_random_per_sec": int(7500 * v4_boost + random.uniform(-750, 750)),
                "file_stat_random_per_sec": int(11000 * v4_boost + random.uniform(-1100, 1100)),
                "system_metrics": create_system_metrics(55, 36),
                "config": {"size": "2G", "num_files": 16},
                "network_validation": {"valid": None, "message": "Network capacity unknown, cannot validate"}
            },
            "fast_test": {
                "status": "passed",
                "duration_seconds": random.uniform(100, 150),
                "sequential_output_char_kbps": int(185000 * v4_boost + random.uniform(-20000, 20000)),
                "sequential_output_char_mbps": round(180.0 * v4_boost + random.uniform(-20, 20), 1),
                "sequential_output_block_kbps": int(195000 * v4_boost + random.uniform(-20000, 20000)),
                "sequential_output_block_mbps": round(190.0 * v4_boost + random.uniform(-20, 20), 1),
                "sequential_rewrite_kbps": int(200000 * v4_boost + random.uniform(-20000, 20000)),
                "sequential_rewrite_mbps": round(195.0 * v4_boost + random.uniform(-20, 20), 1),
                "sequential_input_char_kbps": int(205000 * v4_boost + random.uniform(-20000, 20000)),
                "sequential_input_char_mbps": round(200.0 * v4_boost + random.uniform(-20, 20), 1),
                "random_seeks_per_sec": round(460.0 * v4_boost + random.uniform(-50, 50), 1),
                "file_create_seq_per_sec": int(8200 * v4_boost + random.uniform(-800, 800)),
                "file_delete_seq_per_sec": int(7200 * v4_boost + random.uniform(-700, 700)),
                "file_create_random_per_sec": int(7700 * v4_boost + random.uniform(-750, 750)),
                "file_stat_random_per_sec": int(11500 * v4_boost + random.uniform(-1100, 1100)),
                "config": {"size": "1G", "num_files": 8},
                "system_metrics": create_system_metrics(52, 35),
                "nfs_metrics": create_nfs_metrics("write")
            },
            "file_operations": {
                "status": "passed",
                "duration_seconds": random.uniform(150, 200),
                "sequential_output_char_kbps": int(182000 * v4_boost + random.uniform(-20000, 20000)),
                "sequential_output_char_mbps": round(177.0 * v4_boost + random.uniform(-20, 20), 1),
                "sequential_output_block_kbps": int(192000 * v4_boost + random.uniform(-20000, 20000)),
                "sequential_output_block_mbps": round(187.0 * v4_boost + random.uniform(-20, 20), 1),
                "sequential_rewrite_kbps": int(197000 * v4_boost + random.uniform(-20000, 20000)),
                "sequential_rewrite_mbps": round(192.0 * v4_boost + random.uniform(-20, 20), 1),
                "sequential_input_char_kbps": int(202000 * v4_boost + random.uniform(-20000, 20000)),
                "sequential_input_char_mbps": round(197.0 * v4_boost + random.uniform(-20, 20), 1),
                "sequential_input_block_kbps": int(212000 * v4_boost + random.uniform(-20000, 20000)),
                "sequential_input_block_mbps": round(207.0 * v4_boost + random.uniform(-20, 20), 1),
                "random_seeks_per_sec": round(455.0 * v4_boost + random.uniform(-50, 50), 1),
                "file_create_seq_per_sec": int(8100 * v4_boost + random.uniform(-800, 800)),
                "file_stat_seq_per_sec": int(12200 * v4_boost + random.uniform(-1200, 1200)),
                "file_delete_seq_per_sec": int(7100 * v4_boost + random.uniform(-700, 700)),
                "file_create_random_per_sec": int(7600 * v4_boost + random.uniform(-750, 750)),
                "file_stat_random_per_sec": int(11200 * v4_boost + random.uniform(-1100, 1100)),
                "config": {"size": "1.5G", "num_files": 12},
                "system_metrics": create_system_metrics(54, 36),
                "nfs_metrics": create_nfs_metrics("write")
            }
        },
        "dbench_tests": {
            "light_client_load": {
                "throughput_mbps": round(120.0 * v4_boost + random.uniform(-15, 15), 1),
                "num_clients": 2,
                "num_procs": 2,
                "max_latency_ms": round(50.0 / v4_boost + random.uniform(-5, 5), 2),
                "operations": {"total": 10000, "per_sec": round(500.0 * v4_boost, 1)},
                "total_operations": 10000,
                "avg_latency_ms": round(4.0 / v4_boost + random.uniform(-0.5, 0.5), 2),
                "status": "passed",
                "duration_seconds": random.uniform(15, 25),
                "config": {"clients": 2, "duration": 20},
                "system_metrics": create_system_metrics(30, 34),
                "nfs_metrics": create_nfs_metrics("write"),
                "network_validation": {"valid": None, "message": "Network capacity unknown, cannot validate"}
            },
            "moderate_client_load": {
                "throughput_mbps": round(180.0 * v4_boost + random.uniform(-20, 20), 1),
                "num_clients": 4,
                "num_procs": 4,
                "max_latency_ms": round(80.0 / v4_boost + random.uniform(-8, 8), 2),
                "operations": {"total": 20000, "per_sec": round(800.0 * v4_boost, 1)},
                "total_operations": 20000,
                "avg_latency_ms": round(5.0 / v4_boost + random.uniform(-0.5, 0.5), 2),
                "status": "passed",
                "duration_seconds": random.uniform(20, 30),
                "config": {"clients": 4, "duration": 25},
                "system_metrics": create_system_metrics(45, 35),
                "nfs_metrics": create_nfs_metrics("write"),
                "network_validation": {"valid": None, "message": "Network capacity unknown, cannot validate"}
            },
            "heavy_client_load": {
                "throughput_mbps": round(220.0 * v4_boost + random.uniform(-25, 25), 1),
                "num_clients": 8,
                "num_procs": 8,
                "max_latency_ms": round(120.0 / v4_boost + random.uniform(-12, 12), 2),
                "operations": {"total": 40000, "per_sec": round(1200.0 * v4_boost, 1)},
                "total_operations": 40000,
                "avg_latency_ms": round(6.5 / v4_boost + random.uniform(-0.7, 0.7), 2),
                "status": "passed",
                "duration_seconds": random.uniform(30, 40),
                "config": {"clients": 8, "duration": 35},
                "system_metrics": create_system_metrics(65, 37),
                "nfs_metrics": create_nfs_metrics("write"),
                "network_validation": {"valid": None, "message": "Network capacity unknown, cannot validate"}
            },
            "scalability_test": {
                "status": "passed",
                "client_counts": [1, 2, 4, 8],
                "results": {
                    "1": {
                        "throughput_mbps": round(80.0 * v4_boost, 1),
                        "num_clients": 1,
                        "num_procs": 1,
                        "max_latency_ms": round(230.0 / v4_boost, 2),
                        "operations": {"write3": {"count": 100000, "avg_latency_ms": round(0.16 / v4_boost, 3), "max_latency_ms": round(11.0 / v4_boost, 2)}},
                        "total_operations": 100000,
                        "avg_latency_ms": round(0.25 / v4_boost, 3),
                        "status": "passed",
                        "duration_seconds": random.uniform(30, 40),
                        "config": {"duration": 30, "loadfile": "nfs_3.load", "target_rate": 0, "fsync": False},
                        "system_metrics": create_system_metrics(45, 28),
                        "nfs_metrics": create_nfs_metrics("write")
                    },
                    "2": {
                        "throughput_mbps": round(140.0 * v4_boost, 1),
                        "num_clients": 2,
                        "num_procs": 2,
                        "max_latency_ms": round(260.0 / v4_boost, 2),
                        "operations": {"write3": {"count": 200000, "avg_latency_ms": round(0.17 / v4_boost, 3), "max_latency_ms": round(12.0 / v4_boost, 2)}},
                        "total_operations": 200000,
                        "avg_latency_ms": round(0.28 / v4_boost, 3),
                        "status": "passed",
                        "duration_seconds": random.uniform(30, 40),
                        "config": {"duration": 30, "loadfile": "nfs_3.load", "target_rate": 0, "fsync": False},
                        "system_metrics": create_system_metrics(60, 29),
                        "nfs_metrics": create_nfs_metrics("write")
                    },
                    "4": {
                        "throughput_mbps": round(200.0 * v4_boost, 1),
                        "num_clients": 4,
                        "num_procs": 4,
                        "max_latency_ms": round(290.0 / v4_boost, 2),
                        "operations": {"write3": {"count": 350000, "avg_latency_ms": round(0.18 / v4_boost, 3), "max_latency_ms": round(13.0 / v4_boost, 2)}},
                        "total_operations": 350000,
                        "avg_latency_ms": round(0.30 / v4_boost, 3),
                        "status": "passed",
                        "duration_seconds": random.uniform(30, 40),
                        "config": {"duration": 30, "loadfile": "nfs_3.load", "target_rate": 0, "fsync": False},
                        "system_metrics": create_system_metrics(70, 30),
                        "nfs_metrics": create_nfs_metrics("write")
                    },
                    "8": {
                        "throughput_mbps": round(240.0 * v4_boost, 1),
                        "num_clients": 8,
                        "num_procs": 8,
                        "max_latency_ms": round(320.0 / v4_boost, 2),
                        "operations": {"write3": {"count": 450000, "avg_latency_ms": round(0.20 / v4_boost, 3), "max_latency_ms": round(15.0 / v4_boost, 2)}},
                        "total_operations": 450000,
                        "avg_latency_ms": round(0.35 / v4_boost, 3),
                        "status": "passed",
                        "duration_seconds": random.uniform(30, 40),
                        "config": {"duration": 30, "loadfile": "nfs_3.load", "target_rate": 0, "fsync": False},
                        "system_metrics": create_system_metrics(80, 31),
                        "nfs_metrics": create_nfs_metrics("write")
                    }
                }
            },
            "latency_test": {
                "throughput_mbps": round(100.0 * v4_boost + random.uniform(-12, 12), 1),
                "num_clients": 1,
                "num_procs": 1,
                "max_latency_ms": round(30.0 / v4_boost + random.uniform(-3, 3), 2),
                "operations": {"total": 5000, "per_sec": round(400.0 * v4_boost, 1)},
                "total_operations": 5000,
                "avg_latency_ms": round(2.5 / v4_boost + random.uniform(-0.3, 0.3), 2),
                "status": "passed",
                "duration_seconds": random.uniform(10, 15),
                "config": {"clients": 1, "duration": 12},
                "system_metrics": create_system_metrics(25, 34),
                "nfs_metrics": create_nfs_metrics("write"),
                "network_validation": {"valid": None, "message": "Network capacity unknown, cannot validate"}
            },
            "sustained_load": {
                "throughput_mbps": round(190.0 * v4_boost + random.uniform(-20, 20), 1),
                "num_clients": 4,
                "num_procs": 4,
                "max_latency_ms": round(90.0 / v4_boost + random.uniform(-9, 9), 2),
                "operations": {"total": 60000, "per_sec": round(1000.0 * v4_boost, 1)},
                "total_operations": 60000,
                "avg_latency_ms": round(4.0 / v4_boost + random.uniform(-0.4, 0.4), 2),
                "status": "passed",
                "duration_seconds": random.uniform(55, 65),
                "config": {"clients": 4, "duration": 60},
                "system_metrics": create_system_metrics(50, 35),
                "nfs_metrics": create_nfs_metrics("write"),
                "network_validation": {"valid": None, "message": "Network capacity unknown, cannot validate"}
            },
            "rate_limited_test": {
                "throughput_mbps": round(150.0 * v4_boost + random.uniform(-18, 18), 1),
                "num_clients": 3,
                "num_procs": 3,
                "max_latency_ms": round(70.0 / v4_boost + random.uniform(-7, 7), 2),
                "operations": {"total": 30000, "per_sec": round(750.0 * v4_boost, 1)},
                "total_operations": 30000,
                "avg_latency_ms": round(4.5 / v4_boost + random.uniform(-0.5, 0.5), 2),
                "status": "passed",
                "duration_seconds": random.uniform(35, 45),
                "config": {"clients": 3, "duration": 40, "rate_limit": "50MB/s"},
                "system_metrics": create_system_metrics(40, 35),
                "nfs_metrics": create_nfs_metrics("write"),
                "network_validation": {"valid": None, "message": "Network capacity unknown, cannot validate"}
            },
            "metadata_intensive": {
                "throughput_mbps": round(80.0 * v4_boost + random.uniform(-10, 10), 1),
                "num_clients": 4,
                "num_procs": 4,
                "max_latency_ms": round(100.0 / v4_boost + random.uniform(-10, 10), 2),
                "operations": {"total": 50000, "per_sec": round(2000.0 * v4_boost, 1)},
                "total_operations": 50000,
                "avg_latency_ms": round(2.0 / v4_boost + random.uniform(-0.2, 0.2), 2),
                "status": "passed",
                "duration_seconds": random.uniform(20, 30),
                "config": {"clients": 4, "duration": 25, "workload": "metadata"},
                "system_metrics": create_system_metrics(55, 36),
                "nfs_metrics": create_nfs_metrics("write"),
                "network_validation": {"valid": None, "message": "Network capacity unknown, cannot validate"}
            }
        },
        "summary": {
            "total_duration": random.uniform(2000, 2500),
            "tests_passed": 29,
            "tests_failed": 0,
            "errors": [],
            "performance_validation": []
        },
        "nfs_stats": {
            "before_tests": {
                "nfs_version": f"NFSv{nfs_version}",
                "operations": {},
                "rpc_stats": {}
            },
            "after_tests": {
                "nfs_version": f"NFSv{nfs_version}",
                "operations": {},
                "rpc_stats": {}
            }
        }
    }

def main():
    import os
    from pathlib import Path
    
    # Determine the correct logs directory based on current location
    script_dir = Path(__file__).parent
    logs_dir = script_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Convert to string for compatibility
    logs_dir = str(logs_dir)
    
    print("Creating sample JSON files matching actual benchmark suite format...\n")
    
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
        data["dd_tests"]["sequential_write_direct"]["throughput_mbps"] += 15
        data["fio_tests"]["sequential_read"]["read_bandwidth_mbps"] += 25
        data["fio_tests"]["random_read_4k"]["read_iops"] += 2000
        data["iozone_tests"]["baseline_throughput"]["write_throughput_mbps"] += 20
        data["bonnie_tests"]["comprehensive_test"]["sequential_output_block_mbps"] += 18
        data["dbench_tests"]["moderate_client_load"]["throughput_mbps"] += 30
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
    print("python3 generate_html_report.py samples/logs/nfs_performance_single_test_nfsv4.2_tcp_20260406_120000.json")
    
    print("\n# Test 2: Multi-version report (dimension-based, default)")
    print("python3 generate_html_report.py --test-id multi_version_test --directory samples/logs")
    
    print("\n# Test 3: Comparison report (dimension-based, default)")
    print("python3 generate_html_report.py --test-id baseline_2026 --compare-with optimized_2026 --directory samples/logs")
    
    print("\n# Test 4: Tool-based report (old style)")
    print("python3 generate_html_report.py --test-id baseline_2026 --report-style tool-based --directory samples/logs")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()

# Made with Bob
