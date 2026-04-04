#!/usr/bin/env python3
"""
Input Validation Utilities for NFS Performance Testing

This module provides comprehensive validation for:
- Mount paths (existence, type, NFS mount, permissions)
- Configuration files (structure, required fields, value ranges)
- Test parameters (timeouts, sizes, counts)

Prevents common issues like:
- Testing on wrong paths
- Invalid configurations
- Security vulnerabilities
- Data loss scenarios
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Try to import jsonschema for schema validation
try:
    from jsonschema import validate as json_validate, ValidationError as JsonSchemaValidationError
    from lib.config_schema import get_schema, get_schema_description
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    JsonSchemaValidationError = None


class ValidationError(Exception):
    """Exception raised when validation fails."""
    pass


class MountPathValidator:
    """
    Validates NFS mount paths to ensure they are safe and suitable for testing.
    
    Checks performed:
    - Path exists
    - Path is a directory
    - Path is an NFS mount
    - Write permissions available
    - Sufficient space available
    """
    
    @staticmethod
    def validate(mount_path: str, min_space_gb: float = 100.0) -> Tuple[Path, Dict[str, Any]]:
        """
        Validate NFS mount path for testing.
        
        Args:
            mount_path: Path to validate
            min_space_gb: Minimum required space in GB (default: 100GB)
            
        Returns:
            tuple: (validated_path, mount_info)
            
        Raises:
            ValidationError: If validation fails
            
        Example:
            >>> path, info = MountPathValidator.validate('/mnt/nfs1')
            >>> print(f"Mount: {info['mount_point']}, Free: {info['free_space_gb']}GB")
        """
        # Convert to Path object
        try:
            path = Path(mount_path).resolve()
        except Exception as e:
            raise ValidationError(
                f"❌ Invalid path format: {mount_path}\n"
                f"  Error: {e}\n"
                f"  Provide a valid filesystem path"
            )
        
        # Check if path exists
        if not path.exists():
            raise ValidationError(
                f"❌ Mount path does not exist: {mount_path}\n"
                f"  Possible causes:\n"
                f"  • Path not mounted\n"
                f"  • Typo in path\n"
                f"  • Mount failed\n"
                f"  Troublesoot:\n"
                f"  • Check mounts: mount | grep nfs\n"
                f"  • Verify path: ls -la {path.parent}\n"
                f"  • Mount if needed: sudo mount -t nfs server:/export {mount_path}"
            )
        
        # Check if path is a directory
        if not path.is_dir():
            raise ValidationError(
                f"❌ Mount path is not a directory: {mount_path}\n"
                f"  Path type: {path.stat().st_mode}\n"
                f"  Provide a directory path, not a file"
            )
        
        # Check if path is an NFS mount
        mount_info = MountPathValidator._check_nfs_mount(path)
        if not mount_info['is_nfs']:
            raise ValidationError(
                f"❌ Path is not an NFS mount: {mount_path}\n"
                f"  Mount type: {mount_info.get('fs_type', 'unknown')}\n"
                f"  This tool is designed for NFS performance testing\n"
                f"  Troubleshoot:\n"
                f"  • Check mounts: mount | grep {mount_path}\n"
                f"  • Mount NFS: sudo mount -t nfs server:/export {mount_path}"
            )
        
        # Check write permissions
        MountPathValidator._check_write_permission(path)
        
        # Check available space
        space_info = MountPathValidator._check_space(path, min_space_gb)
        mount_info.update(space_info)
        
        return path, mount_info
    
    @staticmethod
    def _check_nfs_mount(path: Path) -> Dict[str, Any]:
        """
        Check if path is an NFS mount.
        
        Args:
            path: Path to check
            
        Returns:
            dict: Mount information including is_nfs, fs_type, mount_point, server
        """
        mount_info = {
            'is_nfs': False,
            'fs_type': None,
            'mount_point': None,
            'server': None,
            'options': []
        }
        
        try:
            # Read /proc/mounts
            with open('/proc/mounts', 'r') as f:
                mounts = f.readlines()
            
            # Find matching mount
            path_str = str(path)
            for line in mounts:
                parts = line.split()
                if len(parts) >= 4:
                    device, mount_point, fs_type, options = parts[0], parts[1], parts[2], parts[3]
                    
                    # Check if this mount contains our path
                    if path_str.startswith(mount_point):
                        mount_info['mount_point'] = mount_point
                        mount_info['fs_type'] = fs_type
                        mount_info['options'] = options.split(',')
                        
                        # Check if NFS
                        if fs_type.startswith('nfs'):
                            mount_info['is_nfs'] = True
                            mount_info['server'] = device.split(':')[0] if ':' in device else device
                            break
        
        except Exception as e:
            # If we can't read /proc/mounts, try mount command
            try:
                import subprocess
                result = subprocess.run(['mount'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        if str(path) in line and 'nfs' in line.lower():
                            mount_info['is_nfs'] = True
                            break
            except:
                pass
        
        return mount_info
    
    @staticmethod
    def _check_write_permission(path: Path) -> None:
        """
        Check if we have write permission on the mount.
        
        Args:
            path: Path to check
            
        Raises:
            ValidationError: If no write permission
        """
        test_file = path / '.nfs_perf_test_write_check'
        
        try:
            # Try to create a test file
            test_file.touch()
            test_file.unlink()
        except PermissionError:
            raise ValidationError(
                f"❌ No write permission on mount: {path}\n"
                f"  Possible causes:\n"
                f"  • Mount is read-only\n"
                f"  • Insufficient user permissions\n"
                f"  • NFS export restrictions\n"
                f"  Troubleshoot:\n"
                f"  • Check mount options: mount | grep {path}\n"
                f"  • Verify permissions: ls -la {path}\n"
                f"  • Check NFS exports: showmount -e <server>\n"
                f"  • Remount with rw: sudo mount -o remount,rw {path}"
            )
        except Exception as e:
            raise ValidationError(
                f"❌ Cannot write to mount: {path}\n"
                f"  Error: {e}\n"
                f"  Verify mount is accessible and writable"
            )
    
    @staticmethod
    def _check_space(path: Path, min_space_gb: float) -> Dict[str, Any]:
        """
        Check available space on mount.
        
        Args:
            path: Path to check
            min_space_gb: Minimum required space in GB
            
        Returns:
            dict: Space information
            
        Raises:
            ValidationError: If insufficient space
        """
        try:
            stat = os.statvfs(path)
            
            # Calculate space in GB
            total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
            free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
            used_gb = total_gb - free_gb
            used_percent = (used_gb / total_gb * 100) if total_gb > 0 else 0
            
            space_info = {
                'total_space_gb': round(total_gb, 2),
                'free_space_gb': round(free_gb, 2),
                'used_space_gb': round(used_gb, 2),
                'used_percent': round(used_percent, 1)
            }
            
            # Check if sufficient space
            if free_gb < min_space_gb:
                raise ValidationError(
                    f"❌ Insufficient space on mount: {path}\n"
                    f"  Required: {min_space_gb}GB\n"
                    f"  Available: {free_gb:.1f}GB\n"
                    f"  Total: {total_gb:.1f}GB ({used_percent:.1f}% used)\n"
                    f"  Troubleshoot:\n"
                    f"  • Check space: df -h {path}\n"
                    f"  • Clean up old files\n"
                    f"  • Increase storage allocation\n"
                    f"  • Use --quick-test for smaller space requirements"
                )
            
            return space_info
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(
                f"❌ Cannot check space on mount: {path}\n"
                f"  Error: {e}\n"
                f"  Verify mount is accessible"
            )


class ConfigValidator:
    """
    Validates test configuration files.
    
    Checks performed:
    - YAML syntax
    - Required sections present
    - Value types correct
    - Value ranges valid
    - No dangerous configurations
    """
    
    # Required top-level sections
    REQUIRED_SECTIONS = ['dd_tests', 'fio_tests']
    
    # Optional sections
    OPTIONAL_SECTIONS = ['iozone_tests', 'bonnie_tests', 'dbench_tests', 'test_config']
    
    @staticmethod
    def validate(config_path: str) -> Dict[str, Any]:
        """
        Validate configuration file.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            dict: Validated configuration
            
        Raises:
            ValidationError: If validation fails
        """
        # Check file exists
        config_file = Path(config_path)
        if not config_file.exists():
            raise ValidationError(
                f"❌ Configuration file not found: {config_path}\n"
                f"  Provide a valid configuration file path\n"
                f"  Example configs:\n"
                f"  • config/config_quick_test.yaml\n"
                f"  • config/config_long_test.yaml\n"
                f"  • config/test_config.yaml"
            )
        
        # Load YAML
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValidationError(
                f"❌ Invalid YAML syntax in config: {config_path}\n"
                f"  Error: {e}\n"
                f"  Fix YAML syntax errors\n"
                f"  Validate with: yamllint {config_path}"
            )
        except Exception as e:
            raise ValidationError(
                f"❌ Cannot read configuration file: {config_path}\n"
                f"  Error: {e}"
            )
        
        if not isinstance(config, dict):
            raise ValidationError(
                f"❌ Configuration must be a dictionary\n"
                f"  Got: {type(config).__name__}\n"
                f"  Check YAML structure"
            )
        
        # Check required sections
        missing_sections = [s for s in ConfigValidator.REQUIRED_SECTIONS if s not in config]
        if missing_sections:
            raise ValidationError(
                f"❌ Missing required sections in config: {', '.join(missing_sections)}\n"
                f"  Required sections: {', '.join(ConfigValidator.REQUIRED_SECTIONS)}\n"
                f"  Add missing sections to configuration file"
            )
        
        # Perform JSON Schema validation if available
        if JSONSCHEMA_AVAILABLE:
            try:
                schema = get_schema()
                json_validate(instance=config, schema=schema)
            except JsonSchemaValidationError as e:
                # Format schema validation error
                error_path = " -> ".join(str(p) for p in e.path) if e.path else "root"
                raise ValidationError(
                    f"❌ Configuration schema validation failed\n"
                    f"  Location: {error_path}\n"
                    f"  Error: {e.message}\n"
                    f"  \n"
                    f"  Schema requirements:\n"
                    f"{get_schema_description()}\n"
                    f"  \n"
                    f"  Fix the configuration and try again"
                )
            except Exception as e:
                raise ValidationError(
                    f"❌ Schema validation error: {e}\n"
                    f"  Check configuration structure"
                )
        
        # Validate each section (additional custom validation)
        ConfigValidator._validate_dd_tests(config.get('dd_tests', {}))
        ConfigValidator._validate_fio_tests(config.get('fio_tests', {}))
        
        if 'iozone_tests' in config:
            ConfigValidator._validate_iozone_tests(config['iozone_tests'])
        
        if 'test_config' in config:
            ConfigValidator._validate_test_config(config['test_config'])
        
        return config
    
    @staticmethod
    def _validate_dd_tests(dd_config: Dict[str, Any]) -> None:
        """Validate DD test configuration."""
        if not isinstance(dd_config, dict):
            raise ValidationError("dd_tests must be a dictionary")
        
        for test_name, test_config in dd_config.items():
            if not isinstance(test_config, dict):
                continue
            
            # Validate block_size
            if 'block_size' in test_config:
                bs = test_config['block_size']
                if not isinstance(bs, str) or not any(bs.endswith(u) for u in ['K', 'M', 'G', 'k', 'm', 'g']):
                    raise ValidationError(
                        f"❌ Invalid block_size in {test_name}: {bs}\n"
                        f"  Must be string with K/M/G suffix (e.g., '1M', '4K')"
                    )
            
            # Validate count
            if 'count' in test_config:
                count = test_config['count']
                if not isinstance(count, int) or count <= 0:
                    raise ValidationError(
                        f"❌ Invalid count in {test_name}: {count}\n"
                        f"  Must be positive integer"
                    )
                if count > 1000000:
                    raise ValidationError(
                        f"⚠️  Very large count in {test_name}: {count}\n"
                        f"  This may take a very long time\n"
                        f"  Consider reducing count or using --quick-test"
                    )
    
    @staticmethod
    def _validate_fio_tests(fio_config: Dict[str, Any]) -> None:
        """Validate FIO test configuration."""
        if not isinstance(fio_config, dict):
            raise ValidationError("fio_tests must be a dictionary")
        
        for test_name, test_config in fio_config.items():
            if not isinstance(test_config, dict):
                continue
            
            # Validate size
            if 'size' in test_config:
                size = test_config['size']
                if not isinstance(size, str):
                    raise ValidationError(
                        f"❌ Invalid size in {test_name}: {size}\n"
                        f"  Must be string (e.g., '1G', '100M')"
                    )
            
            # Validate numjobs
            if 'numjobs' in test_config:
                numjobs = test_config['numjobs']
                if not isinstance(numjobs, int) or numjobs <= 0:
                    raise ValidationError(
                        f"❌ Invalid numjobs in {test_name}: {numjobs}\n"
                        f"  Must be positive integer"
                    )
                if numjobs > 256:
                    raise ValidationError(
                        f"⚠️  Very high numjobs in {test_name}: {numjobs}\n"
                        f"  This may cause system instability\n"
                        f"  Consider reducing numjobs"
                    )
    
    @staticmethod
    def _validate_iozone_tests(iozone_config: Dict[str, Any]) -> None:
        """Validate IOzone test configuration."""
        if not isinstance(iozone_config, dict):
            raise ValidationError("iozone_tests must be a dictionary")
        
        for test_name, test_config in iozone_config.items():
            if not isinstance(test_config, dict):
                continue
            
            # Validate threads
            if 'threads' in test_config:
                threads = test_config['threads']
                if isinstance(threads, int):
                    if threads <= 0 or threads > 256:
                        raise ValidationError(
                            f"❌ Invalid threads in {test_name}: {threads}\n"
                            f"  Must be between 1 and 256"
                        )
                elif isinstance(threads, list):
                    for t in threads:
                        if not isinstance(t, int) or t <= 0 or t > 256:
                            raise ValidationError(
                                f"❌ Invalid thread count in {test_name}: {t}\n"
                                f"  Must be between 1 and 256"
                            )
    
    @staticmethod
    def _validate_test_config(test_config: Dict[str, Any]) -> None:
        """Validate general test configuration."""
        if not isinstance(test_config, dict):
            raise ValidationError("test_config must be a dictionary")
        
        # Validate timeout
        if 'timeout' in test_config:
            timeout = test_config['timeout']
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                raise ValidationError(
                    f"❌ Invalid timeout: {timeout}\n"
                    f"  Must be positive number (seconds)"
                )
            if timeout > 7200:  # 2 hours
                raise ValidationError(
                    f"⚠️  Very long timeout: {timeout}s\n"
                    f"  Consider reducing timeout or splitting tests"
                )


def validate_mount_and_config(mount_path: str, config_path: Optional[str] = None, 
                              min_space_gb: float = 100.0) -> Tuple[Path, Dict[str, Any], Optional[Dict[str, Any]]]:
    """
    Validate both mount path and configuration file.
    
    This is a convenience function that validates both inputs in one call.
    
    Args:
        mount_path: NFS mount path to validate
        config_path: Optional configuration file path
        min_space_gb: Minimum required space in GB
        
    Returns:
        tuple: (validated_path, mount_info, config or None)
        
    Raises:
        ValidationError: If validation fails
        
    Example:
        >>> path, mount_info, config = validate_mount_and_config(
        ...     '/mnt/nfs1',
        ...     'config/test_config.yaml'
        ... )
    """
    # Validate mount path
    validated_path, mount_info = MountPathValidator.validate(mount_path, min_space_gb)
    
    # Validate config if provided
    config = None
    if config_path:
        config = ConfigValidator.validate(config_path)
    
    return validated_path, mount_info, config


# Made with Bob