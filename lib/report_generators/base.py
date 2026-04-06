#!/usr/bin/env python3
"""
Base classes for HTML report generators

Provides abstract base class and common functionality for all report generators.
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


logger = logging.getLogger(__name__)


class BaseReportGenerator(ABC):
    """
    Abstract base class for all report generators.
    
    Provides common functionality and defines the interface that all
    report generators must implement.
    """
    
    def __init__(self, output_dir: Path = None, report_style: str = 'dimension-based',
                 enable_analysis: bool = True, analysis_level: str = 'detailed'):
        """
        Initialize the report generator.
        
        Args:
            output_dir: Directory for output files (default: ./report)
            report_style: Report organization style - 'dimension-based' or 'tool-based' (default: 'dimension-based')
            enable_analysis: Whether to include performance analysis (default: True)
            analysis_level: Analysis detail level - 'basic', 'detailed', or 'comprehensive' (default: 'detailed')
        """
        self.output_dir = output_dir or Path("report")
        self.output_dir.mkdir(exist_ok=True)
        self.report_style = report_style
        self.enable_analysis = enable_analysis
        self.analysis_level = analysis_level
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
    
    def _generate_analysis_section(self, data: Dict[str, Any]) -> str:
        """
        Generate performance analysis section.
        
        Args:
            data: Test results data (single or multi-version format)
            
        Returns:
            Analysis section HTML or empty string if disabled
        """
        if not self.enable_analysis:
            return ""
        
        try:
            from ..performance_analyzer import PerformanceAnalyzer
            from .templates import get_analysis_section_html, get_analysis_error_html
            
            # Create analyzer and run analysis
            analyzer = PerformanceAnalyzer(data)
            analysis = analyzer.analyze()
            
            # Filter by analysis level if needed
            if self.analysis_level == 'basic':
                analysis = self._filter_basic_analysis(analysis)
            elif self.analysis_level == 'comprehensive':
                # Comprehensive includes everything (no filtering)
                pass
            
            # Render analysis HTML
            return get_analysis_section_html(analysis, self.report_style)
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}", exc_info=True)
            from .templates import get_analysis_error_html
            return get_analysis_error_html(str(e))
    
    def _filter_basic_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter analysis to show only critical insights for basic level.
        
        Args:
            analysis: Full analysis results
            
        Returns:
            Filtered analysis with only critical insights
        """
        filtered_insights = [
            insight for insight in analysis.get('insights', [])
            if insight.get('severity') == 'critical'
        ]
        
        return {
            'insights': filtered_insights,
            'recommendations': analysis.get('recommendations', [])[:3],  # Top 3 only
            'severity_counts': {
                'critical': len(filtered_insights),
                'warning': 0,
                'info': 0
            },
            'overall_health': analysis.get('overall_health', 0),
            'is_multi_version': analysis.get('is_multi_version', False)
        }
    
    def _aggregate_multi_analysis(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate multiple analysis results into a summary.
        Deduplicates insights and recommendations to avoid repetition.
        
        Args:
            analyses: List of analysis results from different versions
            
        Returns:
            Aggregated analysis summary
        """
        if not analyses:
            return {}
        
        # Aggregate severity counts
        total_critical = sum(a.get('severity_counts', {}).get('critical', 0) for a in analyses)
        total_warning = sum(a.get('severity_counts', {}).get('warning', 0) for a in analyses)
        total_info = sum(a.get('severity_counts', {}).get('info', 0) for a in analyses)
        
        # Calculate average health score
        health_scores = []
        for a in analyses:
            health = a.get('overall_health', 0)
            if isinstance(health, dict):
                health_scores.append(health.get('score', 0))
            else:
                health_scores.append(health)
        avg_health = sum(health_scores) / len(health_scores) if health_scores else 0
        
        # Deduplicate insights by title
        seen_insights = {}
        for analysis in analyses:
            for insight in analysis.get('insights', []):
                title = insight.get('title', '')
                severity = insight.get('severity', 'info')
                # Keep the highest severity version of each insight
                if title not in seen_insights or self._severity_rank(severity) > self._severity_rank(seen_insights[title].get('severity', 'info')):
                    seen_insights[title] = insight
        
        # Sort by severity and limit
        unique_insights = sorted(
            seen_insights.values(),
            key=lambda x: self._severity_rank(x.get('severity', 'info')),
            reverse=True
        )[:10]  # Top 10 unique insights
        
        # Deduplicate recommendations by title
        seen_recommendations = {}
        for analysis in analyses:
            for rec in analysis.get('recommendations', []):
                if isinstance(rec, dict):
                    title = rec.get('title', '')
                    priority = rec.get('priority', 'low')
                    # Keep the highest priority version
                    if title not in seen_recommendations or self._priority_rank(priority) > self._priority_rank(seen_recommendations[title].get('priority', 'low')):
                        seen_recommendations[title] = rec
        
        # Sort by priority
        unique_recommendations = sorted(
            seen_recommendations.values(),
            key=lambda x: self._priority_rank(x.get('priority', 'low')),
            reverse=True
        )[:5]  # Top 5 unique recommendations
        
        return {
            'insights': unique_insights,
            'recommendations': unique_recommendations,
            'severity_counts': {
                'critical': total_critical,
                'warning': total_warning,
                'info': total_info
            },
            'overall_health': {
                'score': avg_health,
                'status': self._get_health_status(avg_health),
                'color': self._get_health_color(avg_health)
            },
            'is_aggregated': True,
            'versions_analyzed': len(analyses)
        }
    
    def _severity_rank(self, severity: str) -> int:
        """Return numeric rank for severity (higher = more severe)."""
        ranks = {'critical': 3, 'warning': 2, 'info': 1}
        return ranks.get(severity, 0)
    
    def _priority_rank(self, priority: str) -> int:
        """Return numeric rank for priority (higher = more important)."""
        ranks = {'high': 3, 'medium': 2, 'low': 1}
        return ranks.get(priority, 0)
    
    def _get_health_status(self, score: float) -> str:
        """Get health status from score."""
        if score >= 90:
            return 'excellent'
        elif score >= 75:
            return 'good'
        elif score >= 60:
            return 'fair'
        elif score >= 40:
            return 'poor'
        else:
            return 'critical'
    
    def _get_health_color(self, score: float) -> str:
        """Get health color from score."""
        if score >= 90:
            return 'green'
        elif score >= 75:
            return 'lightgreen'
        elif score >= 60:
            return 'yellow'
        elif score >= 40:
            return 'orange'
        else:
            return 'red'

# Made with Bob
