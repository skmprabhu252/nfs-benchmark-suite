#!/usr/bin/env python3
"""
Configuration Schema for NFS Performance Testing

This module defines JSON schemas for validating test configuration files.
Provides comprehensive validation with clear error messages.
"""

# Configuration schema for NFS performance tests
CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "NFS Performance Test Configuration",
    "description": "Configuration schema for NFS performance testing suite",
    "type": "object",
    "required": ["dd_tests", "fio_tests"],
    "properties": {
        "dd_tests": {
            "type": "object",
            "description": "DD (Data Duplicator) test configurations",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Enable/disable all DD tests"
                }
            },
            "patternProperties": {
                "^(?!enabled$).*$": {
                    "type": "object",
                    "properties": {
                        "enabled": {
                            "type": "boolean",
                            "description": "Enable/disable this test"
                        },
                        "block_size": {
                            "type": "string",
                            "pattern": "^[0-9]+[KMGkmg]$",
                            "description": "Block size (e.g., '1M', '4K')"
                        },
                        "count": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10000000,
                            "description": "Number of blocks to transfer"
                        },
                        "flags": {
                            "type": "object",
                            "properties": {
                                "direct": {
                                    "type": "boolean",
                                    "description": "Use direct I/O (bypass cache)"
                                },
                                "sync": {
                                    "type": "boolean",
                                    "description": "Use synchronized I/O"
                                }
                            }
                        }
                    }
                }
            },
            "additionalProperties": False
        },
        "fio_tests": {
            "type": "object",
            "description": "FIO (Flexible I/O Tester) test configurations",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Enable/disable all FIO tests"
                },
                "common": {
                    "type": "object",
                    "description": "Common FIO parameters",
                    "properties": {
                        "time_based": {
                            "type": "boolean"
                        },
                        "group_reporting": {
                            "type": "boolean"
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["json", "normal", "terse"]
                        }
                    }
                }
            },
            "patternProperties": {
                "^(?!enabled|common).*$": {
                    "type": "object",
                    "properties": {
                        "enabled": {
                            "type": "boolean"
                        },
                        "rw": {
                            "type": "string",
                            "enum": ["read", "write", "randread", "randwrite", "randrw", "readwrite"]
                        },
                        "rwmixread": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 100
                        },
                        "bs": {
                            "type": "string",
                            "pattern": "^[0-9]+[KMGkmg]?$"
                        },
                        "size": {
                            "type": "string",
                            "pattern": "^[0-9]+[KMGkmg]?$"
                        },
                        "filesize": {
                            "type": "string",
                            "pattern": "^[0-9]+[KMGkmg]?$"
                        },
                        "nrfiles": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100000
                        },
                        "numjobs": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 256
                        },
                        "ioengine": {
                            "type": "string",
                            "enum": ["sync", "psync", "libaio", "posixaio", "mmap"]
                        },
                        "iodepth": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 1024
                        },
                        "direct": {
                            "type": "integer",
                            "enum": [0, 1]
                        },
                        "runtime": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 7200
                        },
                        "randrepeat": {
                            "type": "integer",
                            "enum": [0, 1]
                        },
                        "create_on_open": {
                            "type": "integer",
                            "enum": [0, 1]
                        },
                        "lat_percentiles": {
                            "type": "integer",
                            "enum": [0, 1]
                        }
                    }
                }
            }
        },
        "iozone_tests": {
            "type": "object",
            "description": "IOzone test configurations",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Enable/disable all IOzone tests"
                }
            },
            "patternProperties": {
                "^(?!enabled$).*$": {
                    "type": "object",
                    "properties": {
                        "enabled": {
                            "type": "boolean"
                        },
                        "file_size_mb": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 1000000
                        },
                        "record_size_kb": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 16384
                        },
                        "threads": {
                            "oneOf": [
                                {
                                    "type": "integer",
                                    "minimum": 1,
                                    "maximum": 256
                                },
                                {
                                    "type": "array",
                                    "items": {
                                        "type": "integer",
                                        "minimum": 1,
                                        "maximum": 256
                                    },
                                    "minItems": 1,
                                    "maxItems": 20
                                }
                            ]
                        },
                        "direct_io": {
                            "type": "boolean"
                        }
                    }
                }
            }
        },
        "bonnie_tests": {
            "type": "object",
            "description": "Bonnie++ test configurations",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Enable/disable all Bonnie++ tests"
                }
            },
            "patternProperties": {
                "^(?!enabled$).*$": {
                    "type": "object",
                    "properties": {
                        "enabled": {
                            "type": "boolean"
                        },
                        "file_size": {
                            "type": "string",
                            "pattern": "^[0-9]+[kmg]?$",
                            "description": "File size (e.g., '2g', '1024m')"
                        },
                        "num_files": {
                            "type": "string",
                            "pattern": "^[0-9]+:[0-9]+:[0-9]+:[0-9]+$",
                            "description": "Number of files in format num:max:min:num_dirs (e.g., '4:0:0:4')"
                        },
                        "fast_mode": {
                            "type": "boolean",
                            "description": "Enable fast mode"
                        },
                        "processes": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 256,
                            "description": "Number of processes"
                        },
                        "timeout": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 7200,
                            "description": "Timeout in seconds"
                        },
                    }
                }
            }
        },
        "dbench_tests": {
            "type": "object",
            "description": "dbench test configurations",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Enable/disable all dbench tests"
                },
                "common": {
                    "type": "object",
                    "description": "Common dbench parameters"
                }
            },
            "patternProperties": {
                "^(?!enabled|common).*$": {
                    "type": "object",
                    "properties": {
                        "enabled": {
                            "type": "boolean"
                        },
                        "num_clients": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 256
                        },
                        "duration": {
                            "type": "number",
                            "minimum": 1,
                            "maximum": 7200
                        },
                        "target_rate": {
                            "type": "number",
                            "minimum": 0
                        },
                        "warmup": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 600
                        },
                        "fsync": {
                            "type": "boolean"
                        },
                        "sync_open": {
                            "type": "boolean"
                        },
                        "sync_dirs": {
                            "type": "boolean"
                        },
                        "loadfile": {
                            "type": "string"
                        }
                    }
                }
            }
        },
        "test_config": {
            "type": "object",
            "description": "General test configuration",
            "properties": {
                "timeout": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 7200,
                    "description": "Default timeout in seconds"
                },
                "cleanup_on_error": {
                    "type": "boolean",
                    "description": "Clean up test files on error"
                },
                "log_level": {
                    "type": "string",
                    "enum": ["DEBUG", "INFO", "WARNING", "ERROR"],
                    "description": "Logging level"
                }
            }
        },
        "execution": {
            "type": "object",
            "description": "Test execution options",
            "properties": {
                "stop_on_error": {
                    "type": "boolean",
                    "description": "Stop execution on first error"
                },
                "cleanup_on_completion": {
                    "type": "boolean",
                    "description": "Clean up test files after completion"
                },
                "verbose": {
                    "type": "boolean",
                    "description": "Enable verbose output"
                }
            }
        },
        "output": {
            "type": "object",
            "description": "Output configuration",
            "properties": {
                "json_enabled": {
                    "type": "boolean",
                    "description": "Enable JSON output"
                },
                "log_enabled": {
                    "type": "boolean",
                    "description": "Enable log file output"
                },
                "console_summary": {
                    "type": "boolean",
                    "description": "Show summary on console"
                }
            }
        },
        "baselines": {
            "type": "object",
            "description": "Performance baselines for comparison",
            "patternProperties": {
                "^.*$": {
                    "type": "object",
                    "description": "Baseline configuration for specific network type"
                }
            }
        }
    },
    "additionalProperties": False
}


def get_schema():
    """
    Get the configuration schema.
    
    Returns:
        dict: JSON schema for configuration validation
    """
    return CONFIG_SCHEMA


def get_schema_description():
    """
    Get human-readable description of the schema.
    
    Returns:
        str: Description of configuration requirements
    """
    return """
NFS Performance Test Configuration Schema

Required Sections:
  - dd_tests: DD (Data Duplicator) test configurations
  - fio_tests: FIO (Flexible I/O Tester) test configurations

Optional Sections:
  - iozone_tests: IOzone test configurations
  - bonnie_tests: Bonnie++ test configurations
  - dbench_tests: dbench test configurations
  - test_config: General test settings

Common Parameters:
  - enabled: boolean - Enable/disable test
  - timeout: integer (1-7200) - Timeout in seconds
  - threads/numjobs: integer (1-256) - Parallel operations
  - size/file_size: string - Size with K/M/G suffix

Value Constraints:
  - Block sizes: Must end with K, M, or G (e.g., '1M', '4K')
  - Counts: 1 to 10,000,000
  - Threads/Jobs: 1 to 256
  - Timeouts: 1 to 7200 seconds (2 hours)
  - File counts: 1 to 1,000,000

For detailed schema, see CONFIG_SCHEMA in lib/config_schema.py
"""


# Made with Bob