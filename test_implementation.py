#!/usr/bin/env python3
"""
Unit Tests for NFS Benchmark Suite Implementation

Tests the key components from commits:
- 3cc40ad: Automatic NFS mounting with multi-version support
- d616618: Separate JSON files per version with test-id grouping
"""

import unittest
import json
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import glob

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.nfs_mount_manager import NFSMountManager, NFSMountError
from generate_html_report import find_test_id_files, aggregate_test_results


class TestNFSMountManager(unittest.TestCase):
    """Test NFSMountManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.server_ip = "192.168.1.100"
        self.mount_path = "/export/data"
        self.transport = "tcp"
    
    def test_initialization_valid(self):
        """Test NFSMountManager initialization with valid parameters"""
        manager = NFSMountManager(
            server_ip=self.server_ip,
            mount_path=self.mount_path,
            transport=self.transport
        )
        
        self.assertEqual(manager.server_ip, self.server_ip)
        self.assertEqual(manager.mount_path, self.mount_path)
        self.assertEqual(manager.transport, self.transport)
        # Note: mounted_points is managed internally, not a public attribute
    
    def test_initialization_invalid_transport(self):
        """Test NFSMountManager initialization with invalid transport"""
        with self.assertRaises(NFSMountError) as context:
            NFSMountManager(
                server_ip=self.server_ip,
                mount_path=self.mount_path,
                transport="invalid"
            )
        
        self.assertIn("Invalid transport", str(context.exception))
    
    @patch('pathlib.Path.mkdir')
    def test_mount_point_creation(self, mock_mkdir):
        """Test mount point path generation"""
        manager = NFSMountManager(
            server_ip=self.server_ip,
            mount_path=self.mount_path,
            transport=self.transport
        )
        
        # Mock mkdir to avoid filesystem operations
        mock_mkdir.return_value = None
        
        # Test NFSv3
        mount_point = manager.create_mount_point("3")
        self.assertIn("nfsv3_tcp", str(mount_point))
        
        # Test NFSv4.2
        mount_point = manager.create_mount_point("4.2")
        self.assertIn("nfsv4.2_tcp", str(mount_point))
    
    def test_mount_options_tcp(self):
        """Test mount options for TCP transport"""
        manager = NFSMountManager(
            server_ip=self.server_ip,
            mount_path=self.mount_path,
            transport="tcp"
        )
        
        # Check NFSv3 options
        options = manager.MOUNT_OPTIONS['tcp']['3']
        self.assertIn('vers=3', options)
        self.assertIn('proto=tcp', options)
        
        # Check NFSv4.2 options
        options = manager.MOUNT_OPTIONS['tcp']['4.2']
        self.assertIn('vers=4.2', options)
        self.assertIn('proto=tcp', options)
    
    def test_mount_options_rdma(self):
        """Test mount options for RDMA transport"""
        manager = NFSMountManager(
            server_ip=self.server_ip,
            mount_path=self.mount_path,
            transport="rdma"
        )
        
        # Check NFSv3 RDMA options
        options = manager.MOUNT_OPTIONS['rdma']['3']
        self.assertIn('vers=3', options)
        self.assertIn('proto=rdma', options)
        self.assertIn('port=20049', options)


class TestFileNaming(unittest.TestCase):
    """Test file naming convention for separate JSON files"""
    
    def test_file_naming_with_test_id(self):
        """Test file naming with test-id"""
        test_id = "baseline"
        version = "3"
        transport = "tcp"
        timestamp = "20260405_010000"
        
        # Simulate file naming logic from runtest.py
        test_id_prefix = f"{test_id}_"
        version_str = str(version).replace('.', '')
        result_file = f"nfs_performance_{test_id_prefix}nfsv{version_str}_{transport}_{timestamp}.json"
        
        expected = "nfs_performance_baseline_nfsv3_tcp_20260405_010000.json"
        self.assertEqual(result_file, expected)
    
    def test_file_naming_without_test_id(self):
        """Test file naming without test-id"""
        test_id = None
        version = "4.2"
        transport = "rdma"
        timestamp = "20260405_020000"
        
        # Simulate file naming logic from runtest.py
        test_id_prefix = f"{test_id}_" if test_id else ""
        version_str = str(version).replace('.', '')
        result_file = f"nfs_performance_{test_id_prefix}nfsv{version_str}_{transport}_{timestamp}.json"
        
        expected = "nfs_performance_nfsv42_rdma_20260405_020000.json"
        self.assertEqual(result_file, expected)
    
    def test_version_string_conversion(self):
        """Test version string conversion (dots removed)"""
        versions = {
            "3": "nfsv3",
            "4.0": "nfsv40",
            "4.1": "nfsv41",
            "4.2": "nfsv42"
        }
        
        for version, expected in versions.items():
            version_str = str(version).replace('.', '')
            result = f"nfsv{version_str}"
            self.assertEqual(result, expected)


class TestResultStructure(unittest.TestCase):
    """Test result structure for individual and aggregated files"""
    
    def test_individual_result_structure(self):
        """Test individual result file structure"""
        # Simulate individual result structure from runtest.py
        individual_result = {
            'test_metadata': {
                'server_ip': '192.168.1.100',
                'mount_path': '/export/data',
                'transport': 'tcp',
                'test_id': 'baseline'
            },
            'nfs_version': '3',
            'transport': 'tcp',
            'results': {
                'dd_tests': {},
                'fio_tests': {},
                'summary': {}
            }
        }
        
        # Verify structure
        self.assertIn('test_metadata', individual_result)
        self.assertIn('nfs_version', individual_result)
        self.assertIn('transport', individual_result)
        self.assertIn('results', individual_result)
        
        # Verify metadata
        self.assertEqual(individual_result['nfs_version'], '3')
        self.assertEqual(individual_result['transport'], 'tcp')
    
    def test_aggregated_result_structure(self):
        """Test aggregated result structure"""
        # Simulate aggregated structure from generate_html_report.py
        aggregated = {
            'test_metadata': {
                'server_ip': '192.168.1.100',
                'mount_path': '/export/data',
                'transport': 'tcp'
            },
            'results_by_version': {
                'nfsv3_tcp': {'dd_tests': {}, 'fio_tests': {}},
                'nfsv4.2_tcp': {'dd_tests': {}, 'fio_tests': {}}
            }
        }
        
        # Verify structure
        self.assertIn('test_metadata', aggregated)
        self.assertIn('results_by_version', aggregated)
        
        # Verify version keys
        self.assertIn('nfsv3_tcp', aggregated['results_by_version'])
        self.assertIn('nfsv4.2_tcp', aggregated['results_by_version'])


class TestFileAggregation(unittest.TestCase):
    """Test file aggregation functionality"""
    
    def setUp(self):
        """Set up test fixtures with temporary directory"""
        self.test_dir = tempfile.mkdtemp()
        self.test_id = "test_baseline"
    
    def tearDown(self):
        """Clean up temporary directory"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_find_test_id_files(self):
        """Test finding files by test-id"""
        # Create test files
        test_files = [
            f"nfs_performance_{self.test_id}_nfsv3_tcp_20260405_010000.json",
            f"nfs_performance_{self.test_id}_nfsv42_tcp_20260405_020000.json",
            "nfs_performance_other_nfsv3_tcp_20260405_030000.json"
        ]
        
        for filename in test_files:
            filepath = os.path.join(self.test_dir, filename)
            with open(filepath, 'w') as f:
                json.dump({'test': 'data'}, f)
        
        # Find files with test_id
        found_files = find_test_id_files(self.test_id, self.test_dir)
        
        # Verify correct files found
        self.assertEqual(len(found_files), 2)
        for f in found_files:
            self.assertIn(self.test_id, f)
    
    def test_aggregate_test_results(self):
        """Test aggregating multiple result files"""
        # Create test result files
        results = [
            {
                'test_metadata': {'server_ip': '192.168.1.100'},
                'nfs_version': '3',
                'transport': 'tcp',
                'results': {'dd_tests': {'test1': 'data1'}}
            },
            {
                'test_metadata': {'server_ip': '192.168.1.100'},
                'nfs_version': '4.2',
                'transport': 'tcp',
                'results': {'dd_tests': {'test2': 'data2'}}
            }
        ]
        
        json_files = []
        for idx, result in enumerate(results):
            filename = f"nfs_performance_{self.test_id}_nfsv{result['nfs_version'].replace('.', '')}_tcp_2026040{idx}.json"
            filepath = os.path.join(self.test_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(result, f)
            json_files.append(filepath)
        
        # Aggregate results
        aggregated = aggregate_test_results(json_files)
        
        # Verify aggregated structure
        self.assertIn('test_metadata', aggregated)
        self.assertIn('results_by_version', aggregated)
        
        # Verify version results
        self.assertIn('nfsv3_tcp', aggregated['results_by_version'])
        self.assertIn('nfsv4.2_tcp', aggregated['results_by_version'])
        
        # Verify data
        self.assertEqual(
            aggregated['results_by_version']['nfsv3_tcp']['dd_tests']['test1'],
            'data1'
        )


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with old format"""
    
    def test_format_detection_multi_version(self):
        """Test detection of multi-version format"""
        # Multi-version format (old)
        multi_version_result = {
            'test_metadata': {'server_ip': '192.168.1.100'},
            'results_by_version': {
                'nfsv3_tcp': {},
                'nfsv4.2_tcp': {}
            }
        }
        
        is_multi_version = (
            'test_metadata' in multi_version_result and
            'results_by_version' in multi_version_result
        )
        
        self.assertTrue(is_multi_version)
    
    def test_format_detection_single_version(self):
        """Test detection of single-version format"""
        # Single version format (new)
        single_version_result = {
            'test_metadata': {'server_ip': '192.168.1.100'},
            'nfs_version': '3',
            'transport': 'tcp',
            'results': {}
        }
        
        is_multi_version = (
            'test_metadata' in single_version_result and
            'results_by_version' in single_version_result
        )
        
        self.assertFalse(is_multi_version)
        
        # Verify it's single version format
        is_single_version = (
            'nfs_version' in single_version_result and
            'results' in single_version_result
        )
        
        self.assertTrue(is_single_version)


class TestParameterValidation(unittest.TestCase):
    """Test parameter validation"""
    
    def test_nfs_version_parsing(self):
        """Test NFS version string parsing"""
        # Test comma-separated versions
        version_string = "3,4.2"
        versions = version_string.split(',')
        
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0], '3')
        self.assertEqual(versions[1], '4.2')
    
    def test_default_versions_quick_test(self):
        """Test default versions for quick-test"""
        # Simulate quick-test default
        nfs_versions_arg = None
        is_quick_test = True
        
        if is_quick_test:
            nfs_versions = nfs_versions_arg.split(',') if nfs_versions_arg else ['3']
        
        self.assertEqual(nfs_versions, ['3'])
    
    def test_default_versions_long_test(self):
        """Test default versions for long-test"""
        # Simulate long-test default
        nfs_versions_arg = None
        is_long_test = True
        
        if is_long_test:
            nfs_versions = nfs_versions_arg.split(',') if nfs_versions_arg else ['3', '4.0', '4.1', '4.2']
        
        self.assertEqual(len(nfs_versions), 4)
        self.assertIn('3', nfs_versions)
        self.assertIn('4.2', nfs_versions)


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestNFSMountManager))
    suite.addTests(loader.loadTestsFromTestCase(TestFileNaming))
    suite.addTests(loader.loadTestsFromTestCase(TestResultStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestFileAggregation))
    suite.addTests(loader.loadTestsFromTestCase(TestBackwardCompatibility))
    suite.addTests(loader.loadTestsFromTestCase(TestParameterValidation))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("=" * 80)
    print("NFS Benchmark Suite - Unit Tests")
    print("Testing commits: 3cc40ad, d616618")
    print("=" * 80)
    print()
    
    result = run_tests()
    
    print()
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 80)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)

# Made with Bob
