#!/usr/bin/env python3
"""
Base classes for HTML report generators

Provides abstract base class and common functionality for all report generators.
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class BaseReportGenerator(ABC):
    """
    Abstract base class for all report generators.
    
    Provides common functionality and defines the interface that all
    report generators must implement.
    """
    
    def __init__(self, output_dir: Path = None, report_style: str = 'dimension-based'):
        """
        Initialize the report generator.
        
        Args:
            output_dir: Directory for output files (default: ./report)
            report_style: Report organization style - 'dimension-based' or 'tool-based' (default: 'dimension-based')
        """
        self.output_dir = output_dir or Path("report")
        self.output_dir.mkdir(exist_ok=True)
        self.report_style = report_style
        self.logger = logger
        
    @abstractmethod
    def generate(self) -> Path:
        """
        Generate the HTML report.
        
        Returns:
            Path to the generated HTML file
            
        Raises:
            Exception: If report generation fails
        """
        pass
    
    @abstractmethod
    def _load_data(self) -> Dict[str, Any]:
        """
        Load and validate input data.
        
        Returns:
            Dictionary containing loaded data
            
        Raises:
            FileNotFoundError: If required files are not found
            ValueError: If data validation fails
        """
        pass
    
    @abstractmethod
    def _generate_html(self, data: Dict[str, Any]) -> str:
        """
        Generate HTML content from data.
        
        Args:
            data: Processed data dictionary
            
        Returns:
            Complete HTML content as string
        """
        pass
    
    def _write_report(self, html_content: str, filename: str = None) -> Path:
        """
        Write HTML content to file.
        
        Args:
            html_content: HTML content to write
            filename: Optional custom filename (default: auto-generated)
            
        Returns:
            Path to the written file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nfs_performance_report_{timestamp}.html"
        
        output_file = self.output_dir / filename
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"Report saved to: {output_file}")
            return output_file
        except Exception as e:
            self.logger.error(f"Failed to write report: {e}")
            raise
    
    def _load_json_file(self, json_file: Path) -> Dict[str, Any]:
        """
        Load and parse a JSON file.
        
        Args:
            json_file: Path to JSON file
            
        Returns:
            Parsed JSON data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        if not json_file.exists():
            raise FileNotFoundError(f"JSON file not found: {json_file}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {json_file}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading {json_file}: {e}")
            raise
    
    def _safe_get(self, data: Dict, *keys, default=None):
        """
        Safely get nested dictionary values.
        
        Args:
            data: Dictionary to search
            *keys: Sequence of keys to traverse
            default: Default value if key path doesn't exist
            
        Returns:
            Value at key path or default
            
        Example:
            _safe_get(data, 'results', 'dd_tests', 'test1', default={})
        """
        result = data
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
                if result is None:
                    return default
            else:
                return default
        return result if result is not None else default

# Made with Bob
