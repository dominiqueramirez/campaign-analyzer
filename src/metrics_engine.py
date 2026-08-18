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
        """Get the top 6 headline metrics for the slide."""
        # Priority order - includes Facebook, Instagram, and Twitter/X metrics
        # reach/impressions: reach for FB/IG, impressions for Twitter
        # reactions covers both Facebook Reactions and Instagram Likes
        # comments is Instagram-specific
        # impressions is Twitter/X-specific (shown separately if reach is from impressions)
        priority_order = ['reach', 'impressions', 'engagement', 'reactions', 'comments', 'shares', 'clicks', 'engagement_rate']
        headline = []
        
        for key in priority_order:
            if key in self.metrics and len(headline) < 6:
                # Skip shares/clicks/reactions/comments if they're 0 (platform doesn't have these)
                if key in ['shares', 'clicks', 'reactions', 'comments'] and self.metrics[key].current_value == 0:
                    continue
                # Skip impressions if it's the same as reach (to avoid duplicates)
                if key == 'impressions' and 'reach' in self.metrics:
                    if self.metrics['impressions'].current_value == self.metrics['reach'].current_value:
                        continue
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
        # Base column mapping (works for Facebook, Instagram, and Twitter after preprocessing)
        # Note: data_ingestion already standardizes Twitter Engagements → Post engagement
        # and Impressions → Reach, so we just need to lowercase
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
            # Instagram-specific mappings
            'Likes': 'likes',
            'Comments': 'comments',
        }
        
        # Only rename columns that exist and haven't already been standardized
        rename_map = {k: v for k, v in column_mapping.items() if k in self.df.columns}
        self.df = self.df.rename(columns=rename_map)
        
        # Handle Twitter/X raw columns if they weren't processed by data_ingestion
        # (fallback in case data came without preprocessing)
        if 'Engagements' in self.df.columns and 'engagement' not in self.df.columns:
            self.df = self.df.rename(columns={'Engagements': 'engagement'})
        if 'Impressions' in self.df.columns and 'reach' not in self.df.columns:
            self.df = self.df.rename(columns={'Impressions': 'reach'})
        
        # Remove duplicate columns (keep first occurrence)
        self.df = self.df.loc[:, ~self.df.columns.duplicated()]
        
        # If likes column exists but reactions doesn't, use likes as reactions
        if 'likes' in self.df.columns and 'reactions' not in self.df.columns:
            self.df['reactions'] = self.df['likes']
        
        # Ensure engagement column exists (for Instagram, it's calculated from likes + comments)
        if 'engagement' not in self.df.columns:
            if 'likes' in self.df.columns and 'comments' in self.df.columns:
                self.df['engagement'] = self.df['likes'] + self.df['comments']
            elif 'likes' in self.df.columns:
                self.df['engagement'] = self.df['likes']
        
        # For Twitter, if no reach but has impressions, use impressions as reach
        if 'reach' not in self.df.columns and 'impressions' in self.df.columns:
            self.df['reach'] = self.df['impressions']
    
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
        
        # Core metrics to calculate - includes both Facebook and Instagram metrics
        metric_configs = [
            ('reach', 'sum', 'Total Reach'),
            ('engagement', 'sum', 'Total Engagement'),
            ('engagement_rate', 'mean', 'Avg. Engagement Rate'),
            ('clicks', 'sum', 'Total Clicks'),
            ('reactions', 'sum', 'Total Reactions/Likes'),
            ('shares', 'sum', 'Total Shares'),
            ('comments', 'sum', 'Total Comments'),
            ('likes', 'sum', 'Total Likes'),
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
            # Use _safe_to_float helper to handle Series/numpy/scalar types
            eng_sum_current = self._safe_to_float(current_df['engagement'].sum())
            eng_sum_previous = self._safe_to_float(previous_df['engagement'].sum()) if len(previous_df) > 0 else 0.0
            
            avg_eng_current = eng_sum_current / max(len(current_df), 1)
            avg_eng_previous = eng_sum_previous / max(len(previous_df), 1) if len(previous_df) > 0 else 0.0
            
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
    
    def _safe_to_float(self, val) -> float:
        """Safely convert any value to a scalar float."""
        if val is None:
            return 0.0
        # Handle pandas Series - get first value or sum
        if isinstance(val, pd.Series):
            if len(val) == 0:
                return 0.0
            elif len(val) == 1:
                val = val.iloc[0]
            else:
                val = val.sum()
                # If sum still returns a Series (shouldn't happen), get iloc[0]
                if isinstance(val, pd.Series):
                    val = val.iloc[0]
        # Handle numpy types
        if hasattr(val, 'item'):
            try:
                val = val.item()
            except (ValueError, IndexError):
                pass
        # Convert to float
        try:
            result = float(val)
            # NaN check
            if result != result:
                return 0.0
            return result
        except (TypeError, ValueError):
            return 0.0
    
    def _aggregate_metric(self, df: pd.DataFrame, column: str, func: str) -> float:
        """Aggregate a metric using the specified function."""
        if df.empty or column not in df.columns:
            return 0.0
        
        try:
            if func == 'sum':
                result = df[column].sum()
            elif func == 'mean':
                result = df[column].mean()
            elif func == 'max':
                result = df[column].max()
            else:
                result = df[column].sum()
            
            # Use safe conversion helper
            return self._safe_to_float(result)
        except Exception:
            return 0.0
    
    def _create_metric_result(self, name: str, display_name: str,
                              current: float, previous: float) -> MetricResult:
        """Create a MetricResult with calculated changes."""
        # Ensure values are scalar floats using our safe helper
        current = self._safe_to_float(current)
        previous = self._safe_to_float(previous)
        
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
        
        # Helper to safely get scalar value from a Series row
        def get_val(row, key, default=''):
            try:
                if key in row.index:
                    val = row[key]
                    # Handle numpy/pandas scalar types
                    if hasattr(val, 'item'):
                        return val.item()
                    elif isinstance(val, pd.Series):
                        return val.iloc[0] if len(val) > 0 else default
                    # Check for NaN
                    if isinstance(val, float) and val != val:
                        return default
                    return val
                return default
            except Exception:
                return default
        
        # Try different metrics to find top post
        for metric in ['engagement', 'reach', 'clicks']:
            if metric in df.columns:
                try:
                    top_idx = df[metric].idxmax()
                    top_row = df.loc[top_idx]
                    
                    message = str(get_val(top_row, 'message', ''))
                    message = message[:200] + '...' if len(message) > 200 else message
                    
                    engagement_val = get_val(top_row, 'engagement', 0)
                    reach_val = get_val(top_row, 'reach', 0)
                    clicks_val = get_val(top_row, 'clicks', 0)
                    reactions_val = get_val(top_row, 'reactions', 0)
                    shares_val = get_val(top_row, 'shares', 0)
                    
                    return {
                        'date': get_val(top_row, 'date', 'N/A'),
                        'message': message,
                        'post_type': str(get_val(top_row, 'post_type', 'Post')),
                        'engagement': float(engagement_val) if engagement_val else 0.0,
                        'reach': float(reach_val) if reach_val else 0.0,
                        'clicks': float(clicks_val) if clicks_val else 0.0,
                        'reactions': float(reactions_val) if reactions_val else 0.0,
                        'shares': float(shares_val) if shares_val else 0.0,
                        'permalink': str(get_val(top_row, 'permalink', '')),
                        'platform': str(get_val(top_row, 'platform', 'Unknown')),
                    }
                except Exception as e:
                    continue
        
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
