"""
Metrics Calculation Engine
Calculates key performance indicators and period-over-period comparisons.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class MetricResult:
    """Represents a calculated metric with comparison data."""
    name: str
    display_name: str
    current_value: float
    previous_value: float
    change_value: float
    change_percent: float
    trend: str  # 'up', 'down', 'stable'
    is_positive_trend: bool  # Whether the trend is good or bad
    formatted_current: str = ""
    formatted_change: str = ""
    
    def __post_init__(self):
        if not self.formatted_current:
            self.formatted_current = self._format_value(self.current_value)
        if not self.formatted_change:
            self.formatted_change = self._format_percent(self.change_percent)
    
    def _format_value(self, value: float) -> str:
        """Format large numbers with K/M suffixes."""
        if pd.isna(value):
            return "N/A"
        if abs(value) >= 1_000_000:
            return f"{value/1_000_000:.1f}M"
        elif abs(value) >= 1_000:
            return f"{value/1_000:.1f}K"
        elif isinstance(value, float) and value < 1:
            return f"{value:.2%}" if value > 0 else "0%"
        else:
            return f"{int(value):,}"
    
    def _format_percent(self, value: float) -> str:
        """Format percentage change."""
        if pd.isna(value) or value == float('inf') or value == float('-inf'):
            return "N/A"
        sign = "+" if value > 0 else ""
        return f"{sign}{value:.1f}%"


@dataclass
class PerformanceSnapshot:
    """Complete performance snapshot for a time period."""
    period_start: datetime
    period_end: datetime
    previous_period_start: datetime
    previous_period_end: datetime
    metrics: Dict[str, MetricResult] = field(default_factory=dict)
    platform_breakdown: Dict[str, Dict[str, float]] = field(default_factory=dict)
    post_count: int = 0
    top_post: Optional[Dict] = None
    
    def get_headline_metrics(self) -> List[MetricResult]:
        """Get the top 5 headline metrics for the slide."""
        priority_order = ['reach', 'engagement', 'engagement_rate', 'clicks', 'reactions', 'shares']
        headline = []
        
        for key in priority_order:
            if key in self.metrics and len(headline) < 5:
                headline.append(self.metrics[key])
        
        return headline


class MetricsCalculator:
    """
    Calculates social media metrics and period-over-period comparisons.
    """
    
    # Define which metrics are "positive when up"
    POSITIVE_METRICS = {
        'reach', 'engagement', 'engagement_rate', 'clicks', 'reactions', 
        'shares', 'impressions', 'viral_reach', 'followers', 'likes',
        'comments', 'saves', 'video_views'
    }
    
    # Metric display names
    METRIC_DISPLAY_NAMES = {
        'reach': 'Total Reach',
        'engagement': 'Total Engagement',
        'engagement_rate': 'Avg. Engagement Rate',
        'clicks': 'Total Clicks',
        'reactions': 'Total Reactions',
        'shares': 'Total Shares',
        'impressions': 'Total Impressions',
        'viral_reach': 'Viral Reach',
        'post_count': 'Posts Published',
        'avg_engagement_per_post': 'Avg. Engagement/Post',
        'top_reach': 'Best Post Reach',
    }
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._standardize_columns()
    
    def _standardize_columns(self):
        """Map platform-specific columns to standard names."""
        column_mapping = {
            'Reach': 'reach',
            'Post engagement': 'engagement',
            'Engagement rate': 'engagement_rate',
            'Clicks': 'clicks',
            'Reactions': 'reactions',
            'Shares (unique)': 'shares',
            'Fan impressions (unique)': 'impressions',
            'Viral reach': 'viral_reach',
            'Post Message': 'message',
            'Post Type': 'post_type',
            'Post Permalink': 'permalink',
        }
        
        self.df = self.df.rename(columns=column_mapping)
    
    def calculate_snapshot(self, start_date: datetime, end_date: datetime,
                          compare_previous: bool = True) -> PerformanceSnapshot:
        """
        Calculate a complete performance snapshot for the given period.
        
        Args:
            start_date: Start of the analysis period
            end_date: End of the analysis period
            compare_previous: Whether to calculate comparison with previous period
        """
        # Filter current period data
        current_df = self._filter_by_date(self.df, start_date, end_date)
        
        # Calculate previous period dates (same duration)
        period_days = (end_date - start_date).days
        prev_end = start_date - timedelta(days=1)
        prev_start = prev_end - timedelta(days=period_days)
        
        # Filter previous period data
        previous_df = self._filter_by_date(self.df, prev_start, prev_end) if compare_previous else pd.DataFrame()
        
        # Create snapshot
        snapshot = PerformanceSnapshot(
            period_start=start_date,
            period_end=end_date,
            previous_period_start=prev_start,
            previous_period_end=prev_end,
            post_count=len(current_df)
        )
        
        # Calculate core metrics
        snapshot.metrics = self._calculate_all_metrics(current_df, previous_df)
        
        # Calculate platform breakdown
        snapshot.platform_breakdown = self._calculate_platform_breakdown(current_df)
        
        # Find top performing post
        snapshot.top_post = self._find_top_post(current_df)
        
        return snapshot
    
    def _filter_by_date(self, df: pd.DataFrame, start: datetime, end: datetime) -> pd.DataFrame:
        """Filter dataframe by date range."""
        if 'date' not in df.columns:
            return df
        
        mask = (df['date'] >= pd.Timestamp(start)) & (df['date'] <= pd.Timestamp(end))
        return df[mask].copy()
    
    def _calculate_all_metrics(self, current_df: pd.DataFrame, 
                               previous_df: pd.DataFrame) -> Dict[str, MetricResult]:
        """Calculate all metrics with period-over-period comparison."""
        metrics = {}
        
        # Core metrics to calculate
        metric_configs = [
            ('reach', 'sum', 'Total Reach'),
            ('engagement', 'sum', 'Total Engagement'),
            ('engagement_rate', 'mean', 'Avg. Engagement Rate'),
            ('clicks', 'sum', 'Total Clicks'),
            ('reactions', 'sum', 'Total Reactions'),
            ('shares', 'sum', 'Total Shares'),
            ('viral_reach', 'sum', 'Viral Reach'),
            ('impressions', 'sum', 'Total Impressions'),
        ]
        
        for metric_name, agg_func, display_name in metric_configs:
            if metric_name in current_df.columns:
                current_val = self._aggregate_metric(current_df, metric_name, agg_func)
                previous_val = self._aggregate_metric(previous_df, metric_name, agg_func) if len(previous_df) > 0 else 0
                
                metrics[metric_name] = self._create_metric_result(
                    metric_name, display_name, current_val, previous_val
                )
        
        # Add derived metrics
        if 'engagement' in current_df.columns:
            avg_eng_current = current_df['engagement'].sum() / max(len(current_df), 1)
            avg_eng_previous = previous_df['engagement'].sum() / max(len(previous_df), 1) if len(previous_df) > 0 else 0
            
            metrics['avg_engagement_per_post'] = self._create_metric_result(
                'avg_engagement_per_post', 'Avg. Engagement/Post', 
                avg_eng_current, avg_eng_previous
            )
        
        # Post count metric
        metrics['post_count'] = self._create_metric_result(
            'post_count', 'Posts Published',
            len(current_df), len(previous_df) if len(previous_df) > 0 else 0
        )
        
        return metrics
    
    def _aggregate_metric(self, df: pd.DataFrame, column: str, func: str) -> float:
        """Aggregate a metric using the specified function."""
        if df.empty or column not in df.columns:
            return 0.0
        
        if func == 'sum':
            return df[column].sum()
        elif func == 'mean':
            return df[column].mean()
        elif func == 'max':
            return df[column].max()
        else:
            return df[column].sum()
    
    def _create_metric_result(self, name: str, display_name: str,
                              current: float, previous: float) -> MetricResult:
        """Create a MetricResult with calculated changes."""
        change_value = current - previous
        
        if previous == 0:
            change_percent = 100.0 if current > 0 else 0.0
        else:
            change_percent = ((current - previous) / previous) * 100
        
        # Determine trend
        if abs(change_percent) < 1:
            trend = 'stable'
        elif change_percent > 0:
            trend = 'up'
        else:
            trend = 'down'
        
        # Determine if trend is positive (good)
        is_positive = name.replace('_', '') in self.POSITIVE_METRICS or name in self.POSITIVE_METRICS
        is_positive_trend = (trend == 'up' and is_positive) or (trend == 'down' and not is_positive)
        
        return MetricResult(
            name=name,
            display_name=display_name,
            current_value=current,
            previous_value=previous,
            change_value=change_value,
            change_percent=change_percent,
            trend=trend,
            is_positive_trend=is_positive_trend
        )
    
    def _calculate_platform_breakdown(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculate metrics breakdown by platform."""
        if 'platform' not in df.columns or df.empty:
            return {}
        
        breakdown = {}
        for platform in df['platform'].unique():
            platform_df = df[df['platform'] == platform]
            breakdown[platform] = {
                'reach': platform_df['reach'].sum() if 'reach' in platform_df.columns else 0,
                'engagement': platform_df['engagement'].sum() if 'engagement' in platform_df.columns else 0,
                'posts': len(platform_df),
            }
        
        return breakdown
    
    def _find_top_post(self, df: pd.DataFrame) -> Optional[Dict]:
        """Find the top performing post by engagement."""
        if df.empty:
            return None
        
        # Try different metrics to find top post
        for metric in ['engagement', 'reach', 'clicks']:
            if metric in df.columns:
                top_idx = df[metric].idxmax()
                top_row = df.loc[top_idx]
                
                return {
                    'date': top_row.get('date', 'N/A'),
                    'message': str(top_row.get('message', ''))[:200] + '...' if len(str(top_row.get('message', ''))) > 200 else str(top_row.get('message', '')),
                    'post_type': top_row.get('post_type', 'Post'),
                    'engagement': top_row.get('engagement', 0),
                    'reach': top_row.get('reach', 0),
                    'clicks': top_row.get('clicks', 0),
                    'reactions': top_row.get('reactions', 0),
                    'shares': top_row.get('shares', 0),
                    'permalink': top_row.get('permalink', ''),
                    'platform': top_row.get('platform', 'Unknown'),
                }
        
        return None
    
    def calculate_trends(self, window_days: int = 7) -> Dict[str, str]:
        """
        Identify significant trends in the data.
        
        Returns dict of trend descriptions.
        """
        trends = {}
        
        if 'date' not in self.df.columns or self.df.empty:
            return trends
        
        # Sort by date
        df_sorted = self.df.sort_values('date')
        
        # Calculate rolling averages for key metrics
        for metric in ['engagement', 'reach', 'clicks']:
            if metric in df_sorted.columns:
                df_sorted[f'{metric}_rolling'] = df_sorted[metric].rolling(window=3, min_periods=1).mean()
                
                # Compare first half to second half
                mid_point = len(df_sorted) // 2
                first_half = df_sorted[f'{metric}_rolling'].iloc[:mid_point].mean()
                second_half = df_sorted[f'{metric}_rolling'].iloc[mid_point:].mean()
                
                if first_half > 0:
                    change = ((second_half - first_half) / first_half) * 100
                    if abs(change) > 10:
                        direction = "increasing" if change > 0 else "decreasing"
                        trends[metric] = f"{metric.title()} has been {direction} ({change:.0f}%)"
        
        return trends


def format_number(value: float, is_rate: bool = False) -> str:
    """Format a number for display."""
    if pd.isna(value):
        return "N/A"
    
    if is_rate:
        return f"{value:.2%}" if value < 1 else f"{value:.1f}%"
    
    if abs(value) >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    elif abs(value) >= 1_000:
        return f"{value/1_000:.1f}K"
    else:
        return f"{int(value):,}"
