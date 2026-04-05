# NFS Benchmark Suite - Design Modifications Plan

## Overview
Transform the NFS benchmark suite from accepting pre-mounted paths to automatically managing NFS mounts with server-ip and mount-path parameters, supporting multiple NFS versions.

---

## Architecture Changes

### 1. **New Command-Line Interface**

**Current:**
```bash
python3 runtest.py --mount-path /mnt/nfs1 --quick-test
```

**New:**
```bash
# Quick test - NFSv3 only with TCP (default)
python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --quick-test

# Quick test - NFSv3 with RDMA
python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --transport rdma --quick-test

# Long test - All versions (v3, v4.0, v4.1, v4.2) with TCP
python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --long-test

# Long test - All versions with RDMA
python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --transport rdma --long-test

# Specify specific versions with TCP
python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --nfs-versions 3,4.2 --quick-test

# Specify specific versions with RDMA
python3 runtest.py --server-ip 192.168.1.100 --mount-path /export/data --nfs-versions 4.1,4.2 --transport rdma --long-test
```

### 2. **Mount Point Structure**

```
/mnt/nfs_benchmark_mount/
├── nfsv3_tcp/          # NFSv3 with TCP transport
├── nfsv3_rdma/         # NFSv3 with RDMA transport
├── nfsv4.0_tcp/        # NFSv4.0 with TCP transport
├── nfsv4.0_rdma/       # NFSv4.0 with RDMA transport
├── nfsv4.1_tcp/        # NFSv4.1 with TCP transport
├── nfsv4.1_rdma/       # NFSv4.1 with RDMA transport
├── nfsv4.2_tcp/        # NFSv4.2 with TCP transport
└── nfsv4.2_rdma/       # NFSv4.2 with RDMA transport
```

**Note**: Only directories for the selected transport will be created.

### 3. **New Module: `lib/nfs_mount_manager.py`**

**Responsibilities:**
- Server reachability validation (ping)
- NFS server validation (showmount -e)
- Mount path existence validation
- Automatic mounting with version-specific options
- Automatic unmounting and cleanup
- Error handling and rollback

**Key Classes:**
```python
class NFSMountManager:
    - validate_server_reachability(server_ip)
    - validate_nfs_server(server_ip)
    - validate_mount_path_exists(server_ip, mount_path)
    - validate_rdma_support(server_ip) # Check if RDMA is available
    - create_mount_points(base_dir, versions, transport)
    - mount_nfs(server_ip, mount_path, version, transport, local_mount_point)
    - unmount_nfs(local_mount_point)
    - cleanup_all_mounts()
    - get_mount_options(version, transport)
```

### 4. **Validation Flow**

```
Start
  ↓
Parse Arguments
  ↓
Validate Server IP → [Invalid] → Error: Invalid IP
  ↓ [Valid]
Ping Server → [Unreachable] → Error: Server Unreachable
  ↓ [Reachable]
Check NFS Service → [Not Available] → Error: NFS Not Running
  ↓ [Available]
Validate Mount Path → [Not Found] → Error: Path Not Exported
  ↓ [Found]
Create Local Mount Points
  ↓
Test Mode?
  ├─ [Quick] → Mount NFSv3 Only
  └─ [Long] → Mount All Versions
  ↓
Run Tests
  ↓
Unmount & Cleanup
  ↓
End
```

### 5. **Test Execution Flow**

**Quick Test Mode:**
1. Validate server and mount path
2. Validate transport (if RDMA, check RDMA support)
3. Determine versions (use --nfs-versions if specified, else default to NFSv3)
4. Create mount point(s) (e.g., `/mnt/nfs_benchmark_mount/nfsv3_tcp`)
5. **For each specified version:**
   - Mount with version and transport-specific options
   - Run **the same set of benchmark tests** (DD, FIO, IOzone, Bonnie++, dbench)
   - Collect results with version and transport tag
   - Unmount
6. Generate report comparing all tested versions
7. Cleanup all mount points

**Long Test Mode:**
1. Validate server and mount path
2. Validate transport (if RDMA, check RDMA support)
3. Determine versions (use --nfs-versions if specified, else all: v3, v4.0, v4.1, v4.2)
4. Create all version directories with transport suffix
5. **For each version:**
   - Mount with version and transport-specific options
   - Run **the same set of benchmark tests** (DD, FIO, IOzone, Bonnie++, dbench)
   - Collect results with version and transport tag
   - Unmount
6. Generate comparative report across all tested versions
7. Cleanup all mount points

**Key Point**: The same benchmark test suite runs for each NFS version. This allows direct performance comparison between versions (e.g., NFSv3 vs NFSv4.2 throughput, IOPS, latency).

### 6. **Mount Options by Version and Transport**

```python
# TCP Transport (default)
MOUNT_OPTIONS_TCP = {
    'nfsv3': 'vers=3,proto=tcp,rsize=1048576,wsize=1048576,hard,async,noatime',
    'nfsv4.0': 'vers=4.0,proto=tcp,rsize=1048576,wsize=1048576,hard,async,noatime',
    'nfsv4.1': 'vers=4.1,proto=tcp,rsize=1048576,wsize=1048576,hard,async,noatime',
    'nfsv4.2': 'vers=4.2,proto=tcp,rsize=1048576,wsize=1048576,hard,async,noatime'
}

# RDMA Transport (requires RDMA-capable hardware and drivers)
MOUNT_OPTIONS_RDMA = {
    'nfsv3': 'vers=3,proto=rdma,port=20049,rsize=1048576,wsize=1048576,hard,async,noatime',
    'nfsv4.0': 'vers=4.0,proto=rdma,port=20049,rsize=1048576,wsize=1048576,hard,async,noatime',
    'nfsv4.1': 'vers=4.1,proto=rdma,port=20049,rsize=1048576,wsize=1048576,hard,async,noatime',
    'nfsv4.2': 'vers=4.2,proto=rdma,port=20049,rsize=1048576,wsize=1048576,hard,async,noatime'
}
```

**RDMA Notes:**
- RDMA requires InfiniBand or RoCE hardware
- Default RDMA port is 20049 (configurable)
- Server must have NFS-RDMA support enabled
- Client must have RDMA kernel modules loaded

### 7. **Modified Files**

| File | Changes |
|------|---------|
| [`runtest.py`](runtest.py) | - Update argument parser<br>- Add version iteration logic<br>- Integrate NFSMountManager<br>- Update result aggregation |
| [`lib/validation.py`](lib/validation.py) | - Add server validation functions<br>- Modify mount path validation<br>- Add NFS export validation |
| `lib/nfs_mount_manager.py` | - **NEW FILE**<br>- Complete mount management |
| [`README.md`](README.md) | - Update usage examples<br>- Add new requirements<br>- Document version testing |
| `config/*.yaml` | - Add version-specific settings (optional) |

### 8. **Error Handling Strategy**

**Validation Errors:**
- Clear error messages with troubleshooting steps
- Exit before any mount operations

**Mount Errors:**
- Attempt unmount of any successful mounts
- Clean up created directories
- Provide detailed error information

**Test Errors:**
- Complete current version tests
- Unmount current version
- Continue with next version (if long-test)
- Mark failed version in results

**Cleanup Errors:**
- Log warnings but don't fail
- Provide manual cleanup instructions

### 9. **Result Structure for Multi-Version Tests**

```json
{
  "test_metadata": {
    "server_ip": "192.168.1.100",
    "mount_path": "/export/data",
    "transport": "tcp",
    "test_mode": "long",
    "versions_tested": ["nfsv3", "nfsv4.0", "nfsv4.1", "nfsv4.2"]
  },
  "results_by_version": {
    "nfsv3_tcp": { /* all test results */ },
    "nfsv4.0_tcp": { /* all test results */ },
    "nfsv4.1_tcp": { /* all test results */ },
    "nfsv4.2_tcp": { /* all test results */ }
  },
  "version_comparison": {
    "throughput": { /* comparison data */ },
    "iops": { /* comparison data */ },
    "latency": { /* comparison data */ }
  },
  "transport_info": {
    "protocol": "tcp",
    "rdma_available": false
  }
}
```

### 10. **Prerequisites & Requirements**

**System Requirements:**
- Root/sudo access (for mount operations)
- NFS client utilities installed (`nfs-common` or `nfs-utils`)
- Network connectivity to NFS server
- Sufficient local disk space for mount points

**NFS Server Requirements:**
- NFS service running
- Export path configured and accessible
- Appropriate permissions for client access
- Support for requested NFS versions
- For RDMA: NFS-RDMA module loaded and configured

**RDMA-Specific Requirements:**
- InfiniBand or RoCE network adapter
- RDMA kernel modules: `rdma_cm`, `ib_core`, `mlx4_ib` (or equivalent)
- Server NFS-RDMA support: `nfsd` with RDMA enabled
- RDMA port 20049 accessible (or custom port)

---

## Implementation Priority

1. **Phase 1: Core Infrastructure** (High Priority)
   - Create `nfs_mount_manager.py`
   - Implement validation functions
   - Implement mount/unmount functions

2. **Phase 2: Integration** (High Priority)
   - Update `runtest.py` argument parser
   - Integrate mount manager into test flow
   - Update `validation.py`

3. **Phase 3: Version Support** (Medium Priority)
   - Implement version iteration for long-test
   - Add version-specific result handling
   - Update result aggregation

4. **Phase 4: Documentation** (Medium Priority)
   - Update README.md
   - Add usage examples
   - Document troubleshooting

5. **Phase 5: Testing & Refinement** (Low Priority)
   - End-to-end testing
   - Error scenario testing
   - Performance validation

---

## Success Criteria

✅ Users can specify server-ip and mount-path instead of pre-mounted paths  
✅ Server reachability is validated before mounting  
✅ Mount path existence is validated on server  
✅ Quick-test automatically mounts NFSv3 and runs tests  
✅ Long-test automatically tests all 4 NFS versions sequentially  
✅ All mounts are automatically cleaned up after tests  
✅ Clear error messages guide users through issues  
✅ Results clearly indicate which NFS version was tested  
✅ Multi-version results enable performance comparison  

---

## Key Design Decisions

1. **Mount Point Location**: `/mnt/nfs_benchmark_mount/` with version and transport subdirectories
2. **User Privileges**: Script must run as root for mount operations
3. **Test Duration**: Long-test will run 4x longer (one full test per version)
4. **Version Selection**:
   - Quick-test: Uses --nfs-versions if specified, else defaults to NFSv3
   - Long-test: Uses --nfs-versions if specified, else all versions (v3, v4.0, v4.1, v4.2)
5. **Transport Support**:
   - Default: TCP (proto=tcp)
   - Optional: RDMA (proto=rdma, port=20049)
   - Transport validation before mounting
6. **Cleanup Strategy**: Automatic unmount and directory removal after tests

---

This design provides a complete transformation of the benchmark suite while maintaining the existing test logic and adding powerful multi-version comparison capabilities.