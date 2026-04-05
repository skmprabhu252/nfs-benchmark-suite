#!/usr/bin/env python3
"""
NFS Mount Manager for NFS Benchmark Suite

This module handles all NFS mounting operations including:
- Server reachability validation
- NFS service validation
- Mount path existence validation
- RDMA support validation
- Automatic mounting with version and transport-specific options
- Automatic unmounting and cleanup
- Error handling and rollback
"""

import subprocess
import os
import time
import socket
import ipaddress
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


class NFSMountError(Exception):
    """Exception raised when NFS mount operations fail."""
    pass


class NFSMountManager:
    """
    Manages NFS mount operations for benchmark testing.
    
    Supports:
    - Multiple NFS versions (v3, v4.0, v4.1, v4.2)
    - Multiple transports (TCP, RDMA)
    - Automatic validation and cleanup
    """
    
    # Base directory for all NFS benchmark mounts
    BASE_MOUNT_DIR = "/mnt/nfs_benchmark_mount"
    
    # Mount options by version and transport
    MOUNT_OPTIONS = {
        'tcp': {
            '3': 'vers=3,proto=tcp,rsize=1048576,wsize=1048576,hard,async,noatime',
            '4.0': 'vers=4.0,proto=tcp,rsize=1048576,wsize=1048576,hard,async,noatime',
            '4.1': 'vers=4.1,proto=tcp,rsize=1048576,wsize=1048576,hard,async,noatime',
            '4.2': 'vers=4.2,proto=tcp,rsize=1048576,wsize=1048576,hard,async,noatime'
        },
        'rdma': {
            '3': 'vers=3,proto=rdma,port=20049,rsize=1048576,wsize=1048576,hard,async,noatime',
            '4.0': 'vers=4.0,proto=rdma,port=20049,rsize=1048576,wsize=1048576,hard,async,noatime',
            '4.1': 'vers=4.1,proto=rdma,port=20049,rsize=1048576,wsize=1048576,hard,async,noatime',
            '4.2': 'vers=4.2,proto=rdma,port=20049,rsize=1048576,wsize=1048576,hard,async,noatime'
        }
    }
    
    # Supported NFS versions
    SUPPORTED_VERSIONS = ['3', '4.0', '4.1', '4.2']
    
    # Supported transports
    SUPPORTED_TRANSPORTS = ['tcp', 'rdma']
    
    def __init__(self, server_ip: str, mount_path: str, transport: str = 'tcp'):
        """
        Initialize NFS Mount Manager.
        
        Args:
            server_ip: NFS server IP address
            mount_path: Export path on server (e.g., /export/data)
            transport: Transport protocol ('tcp' or 'rdma')
        """
        self.server_ip = server_ip
        self.mount_path = mount_path
        self.transport = transport.lower()
        self.mounted_paths = []  # Track mounted paths for cleanup
        
        # Validate inputs
        self._validate_inputs()
    
    def _validate_inputs(self):
        """Validate server IP, mount path, and transport."""
        # Validate IP address
        try:
            ipaddress.ip_address(self.server_ip)
        except ValueError:
            raise NFSMountError(
                f"❌ Invalid IP address: {self.server_ip}\n"
                f"  Provide a valid IPv4 or IPv6 address\n"
                f"  Example: 192.168.1.100"
            )
        
        # Validate mount path format
        if not self.mount_path.startswith('/'):
            raise NFSMountError(
                f"❌ Invalid mount path: {self.mount_path}\n"
                f"  Mount path must be absolute (start with /)\n"
                f"  Example: /export/data"
            )
        
        # Validate transport
        if self.transport not in self.SUPPORTED_TRANSPORTS:
            raise NFSMountError(
                f"❌ Invalid transport: {self.transport}\n"
                f"  Supported transports: {', '.join(self.SUPPORTED_TRANSPORTS)}\n"
                f"  Use --transport tcp or --transport rdma"
            )
    
    def validate_server_reachability(self) -> bool:
        """
        Validate that the NFS server is reachable via ping.
        
        Returns:
            bool: True if server is reachable
            
        Raises:
            NFSMountError: If server is unreachable
        """
        print(f"🔍 Checking server reachability: {self.server_ip}")
        
        try:
            # Ping with 3 packets, 2 second timeout
            result = subprocess.run(
                ['ping', '-c', '3', '-W', '2', self.server_ip],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"✅ Server is reachable: {self.server_ip}")
                return True
            else:
                raise NFSMountError(
                    f"❌ Server unreachable: {self.server_ip}\n"
                    f"  Ping failed with exit code {result.returncode}\n"
                    f"  Troubleshoot:\n"
                    f"  • Check network connectivity: ping {self.server_ip}\n"
                    f"  • Verify server is powered on\n"
                    f"  • Check firewall rules (ICMP)\n"
                    f"  • Verify IP address is correct"
                )
        
        except subprocess.TimeoutExpired:
            raise NFSMountError(
                f"❌ Server ping timeout: {self.server_ip}\n"
                f"  Server did not respond within 10 seconds\n"
                f"  Check network connectivity and server status"
            )
        except Exception as e:
            raise NFSMountError(
                f"❌ Failed to check server reachability: {e}\n"
                f"  Verify network configuration"
            )
    
    def validate_nfs_server(self) -> bool:
        """
        Validate that NFS service is running on the server.
        
        Returns:
            bool: True if NFS service is available
            
        Raises:
            NFSMountError: If NFS service is not available
        """
        print(f"🔍 Checking NFS service: {self.server_ip}")
        
        try:
            # Use showmount to check NFS exports
            result = subprocess.run(
                ['showmount', '-e', self.server_ip],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"✅ NFS service is running: {self.server_ip}")
                return True
            else:
                raise NFSMountError(
                    f"❌ NFS service not available: {self.server_ip}\n"
                    f"  showmount failed with exit code {result.returncode}\n"
                    f"  Error: {result.stderr[:200] if result.stderr else 'Unknown'}\n"
                    f"  Troubleshoot:\n"
                    f"  • Check NFS server is running: systemctl status nfs-server\n"
                    f"  • Verify exports are configured: cat /etc/exports\n"
                    f"  • Check firewall allows NFS (ports 2049, 111)\n"
                    f"  • Restart NFS service if needed"
                )
        
        except subprocess.TimeoutExpired:
            raise NFSMountError(
                f"❌ NFS service check timeout: {self.server_ip}\n"
                f"  showmount did not respond within 30 seconds\n"
                f"  NFS service may be hung or not running"
            )
        except FileNotFoundError:
            raise NFSMountError(
                f"❌ showmount command not found\n"
                f"  Install NFS client utilities:\n"
                f"  • Ubuntu/Debian: sudo apt-get install nfs-common\n"
                f"  • RHEL/CentOS: sudo dnf install nfs-utils"
            )
        except Exception as e:
            raise NFSMountError(
                f"❌ Failed to check NFS service: {e}\n"
                f"  Verify NFS server configuration"
            )
    
    def validate_mount_path_exists(self) -> bool:
        """
        Validate that the mount path is exported by the NFS server.
        
        Returns:
            bool: True if mount path exists in exports
            
        Raises:
            NFSMountError: If mount path is not exported
        """
        print(f"🔍 Checking mount path exists: {self.server_ip}:{self.mount_path}")
        
        try:
            # Get list of exports
            result = subprocess.run(
                ['showmount', '-e', self.server_ip],
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            
            # Parse exports
            exports = []
            for line in result.stdout.splitlines()[1:]:  # Skip header
                parts = line.split()
                if parts:
                    exports.append(parts[0])
            
            # Check if our mount path is in exports
            if self.mount_path in exports:
                print(f"✅ Mount path is exported: {self.mount_path}")
                return True
            else:
                # Show available exports
                exports_list = '\n  • '.join(exports) if exports else 'None'
                raise NFSMountError(
                    f"❌ Mount path not exported: {self.mount_path}\n"
                    f"  Server: {self.server_ip}\n"
                    f"  Available exports:\n  • {exports_list}\n"
                    f"  Troubleshoot:\n"
                    f"  • Check /etc/exports on server\n"
                    f"  • Add export: echo '{self.mount_path} *(rw,sync,no_root_squash)' >> /etc/exports\n"
                    f"  • Reload exports: exportfs -ra\n"
                    f"  • Verify: showmount -e {self.server_ip}"
                )
        
        except subprocess.CalledProcessError as e:
            raise NFSMountError(
                f"❌ Failed to get exports from server: {self.server_ip}\n"
                f"  Error: {e.stderr[:200] if e.stderr else 'Unknown'}\n"
                f"  Check NFS server configuration"
            )
        except Exception as e:
            raise NFSMountError(
                f"❌ Failed to validate mount path: {e}"
            )
    
    def validate_rdma_support(self) -> bool:
        """
        Validate RDMA support if RDMA transport is requested.
        
        Returns:
            bool: True if RDMA is supported
            
        Raises:
            NFSMountError: If RDMA is not supported
        """
        if self.transport != 'rdma':
            return True  # Not using RDMA, skip validation
        
        print(f"🔍 Checking RDMA support")
        
        # Check for RDMA kernel modules
        rdma_modules = ['rdma_cm', 'ib_core', 'ib_uverbs']
        missing_modules = []
        
        try:
            result = subprocess.run(
                ['lsmod'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            loaded_modules = result.stdout
            for module in rdma_modules:
                if module not in loaded_modules:
                    missing_modules.append(module)
            
            if missing_modules:
                raise NFSMountError(
                    f"❌ RDMA kernel modules not loaded: {', '.join(missing_modules)}\n"
                    f"  Required modules: {', '.join(rdma_modules)}\n"
                    f"  Load modules:\n"
                    f"  • modprobe rdma_cm\n"
                    f"  • modprobe ib_core\n"
                    f"  • modprobe ib_uverbs\n"
                    f"  Or install RDMA packages:\n"
                    f"  • Ubuntu/Debian: sudo apt-get install rdma-core\n"
                    f"  • RHEL/CentOS: sudo dnf install rdma-core"
                )
            
            print(f"✅ RDMA kernel modules loaded")
            
            # Check for RDMA devices
            if Path('/sys/class/infiniband').exists():
                devices = list(Path('/sys/class/infiniband').iterdir())
                if devices:
                    print(f"✅ RDMA devices found: {len(devices)}")
                    return True
                else:
                    raise NFSMountError(
                        f"❌ No RDMA devices found\n"
                        f"  RDMA requires InfiniBand or RoCE hardware\n"
                        f"  Check: ls /sys/class/infiniband/\n"
                        f"  Verify RDMA hardware is installed and configured"
                    )
            else:
                raise NFSMountError(
                    f"❌ RDMA subsystem not available\n"
                    f"  /sys/class/infiniband does not exist\n"
                    f"  Install and configure RDMA hardware"
                )
        
        except subprocess.TimeoutExpired:
            raise NFSMountError(f"❌ Timeout checking RDMA support")
        except Exception as e:
            if isinstance(e, NFSMountError):
                raise
            raise NFSMountError(f"❌ Failed to validate RDMA support: {e}")
    
    def create_mount_point(self, version: str) -> Path:
        """
        Create mount point directory for a specific NFS version and transport.
        
        Args:
            version: NFS version (e.g., '3', '4.2')
            
        Returns:
            Path: Created mount point path
            
        Raises:
            NFSMountError: If directory creation fails
        """
        # Create mount point name: nfsv{version}_{transport}
        mount_name = f"nfsv{version}_{self.transport}"
        mount_point = Path(self.BASE_MOUNT_DIR) / mount_name
        
        try:
            # Create base directory if it doesn't exist
            Path(self.BASE_MOUNT_DIR).mkdir(parents=True, exist_ok=True)
            
            # Create version-specific mount point
            mount_point.mkdir(parents=True, exist_ok=True)
            
            print(f"✅ Created mount point: {mount_point}")
            return mount_point
        
        except PermissionError:
            raise NFSMountError(
                f"❌ Permission denied creating mount point: {mount_point}\n"
                f"  This script must run as root for mount operations\n"
                f"  Run with: sudo python3 runtest.py ..."
            )
        except Exception as e:
            raise NFSMountError(
                f"❌ Failed to create mount point {mount_point}: {e}"
            )
    
    def mount_nfs(self, version: str, mount_point: Path) -> bool:
        """
        Mount NFS with specified version and transport.
        
        Args:
            version: NFS version (e.g., '3', '4.2')
            mount_point: Local mount point path
            
        Returns:
            bool: True if mount successful
            
        Raises:
            NFSMountError: If mount fails
        """
        # Validate version
        if version not in self.SUPPORTED_VERSIONS:
            raise NFSMountError(
                f"❌ Unsupported NFS version: {version}\n"
                f"  Supported versions: {', '.join(self.SUPPORTED_VERSIONS)}"
            )
        
        # Get mount options
        options = self.MOUNT_OPTIONS[self.transport][version]
        
        # Build mount command
        nfs_source = f"{self.server_ip}:{self.mount_path}"
        mount_cmd = [
            'mount',
            '-t', 'nfs',
            '-o', options,
            nfs_source,
            str(mount_point)
        ]
        
        print(f"🔧 Mounting NFS v{version} with {self.transport.upper()}")
        print(f"   Source: {nfs_source}")
        print(f"   Target: {mount_point}")
        print(f"   Options: {options}")
        
        try:
            result = subprocess.run(
                mount_cmd,
                capture_output=True,
                text=True,
                timeout=60,
                check=True
            )
            
            # Verify mount
            time.sleep(2)  # Give mount time to settle
            if self._verify_mount(mount_point):
                print(f"✅ Successfully mounted: {mount_point}")
                self.mounted_paths.append(mount_point)
                return True
            else:
                raise NFSMountError(f"Mount verification failed for {mount_point}")
        
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            raise NFSMountError(
                f"❌ Mount failed: {nfs_source} → {mount_point}\n"
                f"  NFS version: {version}\n"
                f"  Transport: {self.transport}\n"
                f"  Error: {error_msg[:300]}\n"
                f"  Troubleshoot:\n"
                f"  • Check server exports: showmount -e {self.server_ip}\n"
                f"  • Verify version support on server\n"
                f"  • Check firewall rules\n"
                f"  • For RDMA: Verify port 20049 is accessible\n"
                f"  • Check server logs: journalctl -u nfs-server"
            )
        except subprocess.TimeoutExpired:
            raise NFSMountError(
                f"❌ Mount timeout: {nfs_source} → {mount_point}\n"
                f"  Mount operation did not complete within 60 seconds\n"
                f"  Server may be unresponsive or network issues"
            )
        except Exception as e:
            raise NFSMountError(f"❌ Unexpected mount error: {e}")
    
    def _verify_mount(self, mount_point: Path) -> bool:
        """
        Verify that a mount point is actually mounted.
        
        Args:
            mount_point: Path to verify
            
        Returns:
            bool: True if mounted
        """
        try:
            # Check /proc/mounts
            with open('/proc/mounts', 'r') as f:
                mounts = f.read()
                return str(mount_point) in mounts
        except:
            # Fallback: check with mount command
            try:
                result = subprocess.run(
                    ['mount'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return str(mount_point) in result.stdout
            except:
                return False
    
    def unmount_nfs(self, mount_point: Path, force: bool = False) -> bool:
        """
        Unmount NFS mount point.
        
        Args:
            mount_point: Path to unmount
            force: Use force unmount if normal unmount fails
            
        Returns:
            bool: True if unmount successful
        """
        if not self._verify_mount(mount_point):
            print(f"ℹ️  Not mounted (skipping): {mount_point}")
            return True
        
        print(f"🔧 Unmounting: {mount_point}")
        
        try:
            # Try normal unmount first
            result = subprocess.run(
                ['umount', str(mount_point)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"✅ Unmounted: {mount_point}")
                # Remove from tracked mounts
                if mount_point in self.mounted_paths:
                    self.mounted_paths.remove(mount_point)
                return True
            
            # If normal unmount failed and force is requested
            if force:
                print(f"⚠️  Normal unmount failed, trying force unmount...")
                result = subprocess.run(
                    ['umount', '-f', str(mount_point)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    print(f"✅ Force unmounted: {mount_point}")
                    if mount_point in self.mounted_paths:
                        self.mounted_paths.remove(mount_point)
                    return True
            
            # Unmount failed
            print(f"⚠️  Failed to unmount: {mount_point}")
            print(f"   Error: {result.stderr[:200] if result.stderr else 'Unknown'}")
            print(f"   Manual cleanup may be required: sudo umount -f {mount_point}")
            return False
        
        except subprocess.TimeoutExpired:
            print(f"⚠️  Unmount timeout: {mount_point}")
            print(f"   Mount may be busy or hung")
            print(f"   Manual cleanup: sudo umount -f {mount_point}")
            return False
        except Exception as e:
            print(f"⚠️  Unmount error: {e}")
            return False
    
    def cleanup_mount_point(self, mount_point: Path) -> bool:
        """
        Remove mount point directory after unmounting.
        
        Args:
            mount_point: Path to remove
            
        Returns:
            bool: True if cleanup successful
        """
        try:
            if mount_point.exists():
                mount_point.rmdir()
                print(f"✅ Removed mount point: {mount_point}")
            return True
        except OSError as e:
            print(f"⚠️  Failed to remove mount point {mount_point}: {e}")
            print(f"   Manual cleanup: sudo rmdir {mount_point}")
            return False
    
    def cleanup_all(self, force: bool = False) -> None:
        """
        Unmount all tracked mounts and clean up directories.
        
        Args:
            force: Use force unmount if needed
        """
        print(f"\n{'='*60}")
        print(f"Cleaning up NFS mounts...")
        print(f"{'='*60}")
        
        # Unmount all tracked mounts
        for mount_point in list(self.mounted_paths):
            self.unmount_nfs(mount_point, force=force)
            self.cleanup_mount_point(mount_point)
        
        # Try to remove base directory if empty
        try:
            base_path = Path(self.BASE_MOUNT_DIR)
            if base_path.exists() and not any(base_path.iterdir()):
                base_path.rmdir()
                print(f"✅ Removed base directory: {base_path}")
        except:
            pass  # Ignore errors removing base directory
        
        print(f"{'='*60}\n")
    
    def validate_all(self) -> bool:
        """
        Run all validation checks.
        
        Returns:
            bool: True if all validations pass
            
        Raises:
            NFSMountError: If any validation fails
        """
        print(f"\n{'='*60}")
        print(f"Validating NFS Server Configuration")
        print(f"{'='*60}")
        print(f"Server IP: {self.server_ip}")
        print(f"Mount Path: {self.mount_path}")
        print(f"Transport: {self.transport.upper()}")
        print(f"{'='*60}\n")
        
        # Run all validations
        self.validate_server_reachability()
        self.validate_nfs_server()
        self.validate_mount_path_exists()
        self.validate_rdma_support()
        
        print(f"\n{'='*60}")
        print(f"✅ All validations passed")
        print(f"{'='*60}\n")
        
        return True


# Made with Bob