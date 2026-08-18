"""
Data Ingestion Module
Handles loading and preprocessing social media data from various sources.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from pathlib import Path


class DataIngestionError(Exception):
    """Custom exception for data ingestion errors."""
    pass


class SocialMediaDataLoader:
    """
    Loads and preprocesses social media data from CSV files.
    Supports Facebook, Instagram, LinkedIn, and X (Twitter) data formats.
    """
    
    # Standard column mappings for different platforms
    PLATFORM_COLUMN_MAPS = {
        'facebook': {
            'date_col': 'Date (GMT)',
            'page_col': 'Facebook Page',
            'post_id_col': 'Post ID',
            'post_type_col': 'Post Type',
            'message_col': 'Post Message',
            'permalink_col': 'Post Permalink',
            'reach_col': 'Reach',
            'impressions_col': 'Fan impressions (unique)',
            'engagement_col': 'Post engagement',
            'engagement_rate_col': 'Engagement rate',
            'clicks_col': 'Clicks',
            'reactions_col': 'Reactions',
            'shares_col': 'Shares (unique)',
            'viral_reach_col': 'Viral reach',
            'wow_reactions_col': 'Reactions: Wow',
        },
        'instagram': {
            'date_col': 'Date (GMT)',
            'page_col': 'Instagram Business Account',
            'post_id_col': 'Post ID',
            'post_type_col': 'Post Type',
            'message_col': 'Post Message',
            'permalink_col': 'Post Permalink',
            'reach_col': 'Reach',
            'engagement_rate_col': 'Engagement rate',
            'likes_col': 'Likes',
            'comments_col': 'Comments',
            'tag_col': 'Tag',
        },
        'linkedin': {
            'date_col': 'Date',
            'impressions_col': 'Impressions',
            'engagement_col': 'Engagement',
            'engagement_rate_col': 'Engagement Rate',
            'clicks_col': 'Clicks',
            'reactions_col': 'Reactions',
            'comments_col': 'Comments',
            'shares_col': 'Shares',
        },
        'twitter': {
            'date_col': 'Date (GMT)',
            'page_col': 'Twitter Account',
            'post_id_col': 'Post ID',
            'post_type_col': 'Post Type',
            'message_col': 'Post Message',
            'permalink_col': 'Post Permalink',
            'impressions_col': 'Impressions',
            'engagement_col': 'Engagements',
            'engagement_rate_col': 'Engagement Rate',
            'tag_col': 'Tag',
        }
    }
    
    def __init__(self):
        self.data: Dict[str, pd.DataFrame] = {}
        self.raw_data: Dict[str, pd.DataFrame] = {}
        
    def detect_platform(self, df: pd.DataFrame) -> str:
        """
        Automatically detect the social media platform from column names.
        """
        columns = set(df.columns.str.lower())
        columns_str = ' '.join(df.columns).lower()
        
        # Check for specific platform identifiers
        if 'twitter account' in columns or 'twitter' in columns_str:
            return 'twitter'
        elif 'instagram business account' in columns or 'instagram' in columns_str:
            return 'instagram'
        elif 'facebook page' in columns or 'facebook' in columns_str:
            return 'facebook'
        elif 'linkedin' in columns_str:
            return 'linkedin'
        
        # Check for platform-specific metrics
        if 'engagements' in columns and 'impressions' in columns:
            return 'twitter'
        elif 'post engagement' in columns:
            return 'facebook'
        
        return 'unknown'
    
    def load_csv(self, file_path: str, platform: Optional[str] = None) -> pd.DataFrame:
        """
        Load a CSV file and preprocess it for analysis.
        
        Args:
            file_path: Path to the CSV file
            platform: Optional platform name. If not provided, will auto-detect.
            
        Returns:
            Preprocessed DataFrame
        """
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='latin-1')
        except Exception as e:
            raise DataIngestionError(f"Failed to load CSV: {str(e)}")
        
        if platform is None:
            platform = self.detect_platform(df)
        
        # Store raw data
        self.raw_data[platform] = df.copy()
        
        # Preprocess data
        df = self._preprocess_data(df, platform)
        
        # Store processed data
        self.data[platform] = df
        
        return df
    
    def _preprocess_data(self, df: pd.DataFrame, platform: str) -> pd.DataFrame:
        """
        Preprocess data: parse dates, standardize columns, handle missing values.
        """
        df = df.copy()
        
        # Get column mapping for platform
        col_map = self.PLATFORM_COLUMN_MAPS.get(platform, self.PLATFORM_COLUMN_MAPS['facebook'])
        
        # Parse date column
        date_col = col_map.get('date_col', 'Date')
        if date_col in df.columns:
            df['date'] = pd.to_datetime(df[date_col], errors='coerce')
        elif 'Date (GMT)' in df.columns:
            df['date'] = pd.to_datetime(df['Date (GMT)'], errors='coerce')
        elif 'Date' in df.columns:
            df['date'] = pd.to_datetime(df['Date'], errors='coerce')
        else:
            # Try to find any date-like column
            for col in df.columns:
                if 'date' in col.lower():
                    df['date'] = pd.to_datetime(df[col], errors='coerce')
                    break
        
        # Standardize numeric columns - Facebook
        fb_numeric_cols = ['Reach', 'Clicks', 'Post engagement', 'Reactions', 
                          'Shares (unique)', 'Viral reach', 'Fan impressions (unique)']
        
        # Standardize numeric columns - Instagram
        ig_numeric_cols = ['Reach', 'Likes', 'Comments']
        
        # Standardize numeric columns - Twitter/X
        tw_numeric_cols = ['Impressions', 'Engagements']
        
        # Process all numeric columns
        all_numeric_cols = list(set(fb_numeric_cols + ig_numeric_cols + tw_numeric_cols))
        for col in all_numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Engagement rate handling (different column names per platform)
        if 'Engagement rate' in df.columns:
            df['Engagement rate'] = pd.to_numeric(df['Engagement rate'], errors='coerce').fillna(0)
        elif 'Engagement Rate' in df.columns:
            df['Engagement rate'] = pd.to_numeric(df['Engagement Rate'], errors='coerce').fillna(0)
        
        # Platform-specific standardization
        if platform == 'instagram':
            # Calculate engagement from Likes + Comments for Instagram
            if 'Likes' in df.columns and 'Comments' in df.columns:
                df['Post engagement'] = df['Likes'] + df['Comments']
            # Use Likes as Reactions equivalent
            if 'Likes' in df.columns and 'Reactions' not in df.columns:
                df['Reactions'] = df['Likes']
            # Instagram doesn't have clicks or shares in this format
            if 'Clicks' not in df.columns:
                df['Clicks'] = 0
            if 'Shares (unique)' not in df.columns:
                df['Shares (unique)'] = 0
        
        elif platform == 'twitter':
            # Twitter/X uses Engagements as total engagement
            if 'Engagements' in df.columns:
                df['Post engagement'] = df['Engagements']
            # Twitter/X uses Impressions instead of Reach
            if 'Impressions' in df.columns and 'Reach' not in df.columns:
                df['Reach'] = df['Impressions']
            # Twitter/X doesn't have separate reactions/clicks/shares in this CSV format
            if 'Reactions' not in df.columns:
                df['Reactions'] = 0
            if 'Clicks' not in df.columns:
                df['Clicks'] = 0
            if 'Shares (unique)' not in df.columns:
                df['Shares (unique)'] = 0
        
        # Add platform identifier
        df['platform'] = platform
        
        # Sort by date
        if 'date' in df.columns:
            df = df.sort_values('date', ascending=False)
        
        return df
    
    def filter_by_date_range(self, df: pd.DataFrame, start_date: datetime, 
                             end_date: datetime) -> pd.DataFrame:
        """
        Filter DataFrame by date range.
        """
        if 'date' not in df.columns:
            return df
        
        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        return df[mask].copy()
    
    def get_combined_data(self) -> pd.DataFrame:
        """
        Combine data from all platforms into a single DataFrame.
        """
        if not self.data:
            return pd.DataFrame()
        
        # Combine all platform data
        combined = pd.concat(self.data.values(), ignore_index=True)
        return combined
    
    def get_date_range(self, df: Optional[pd.DataFrame] = None) -> Tuple[datetime, datetime]:
        """
        Get the date range of the data.
        """
        if df is None:
            df = self.get_combined_data()
        
        if df.empty or 'date' not in df.columns:
            return datetime.now() - timedelta(days=7), datetime.now()
        
        return df['date'].min(), df['date'].max()
    
    def validate_data(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Validate loaded data and return quality metrics.
        """
        validation = {
            'total_rows': len(df),
            'platforms': df['platform'].unique().tolist() if 'platform' in df.columns else [],
            'date_range': self.get_date_range(df),
            'missing_values': df.isnull().sum().to_dict(),
            'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
            'is_valid': len(df) > 0
        }
        return validation


class DataAggregator:
    """
    Aggregates social media data for reporting.
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        
    def aggregate_by_period(self, period: str = 'D') -> pd.DataFrame:
        """
        Aggregate data by time period.
        
        Args:
            period: 'D' for daily, 'W' for weekly, 'M' for monthly
        """
        if 'date' not in self.df.columns:
            return self.df
        
        df = self.df.copy()
        df['period'] = df['date'].dt.to_period(period)
        
        agg_dict = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if 'rate' in col.lower():
                agg_dict[col] = 'mean'
            else:
                agg_dict[col] = 'sum'
        
        return df.groupby('period').agg(agg_dict).reset_index()
    
    def aggregate_by_platform(self) -> pd.DataFrame:
        """
        Aggregate data by platform.
        """
        if 'platform' not in self.df.columns:
            return self.df
        
        agg_dict = {}
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if 'rate' in col.lower():
                agg_dict[col] = 'mean'
            else:
                agg_dict[col] = 'sum'
        
        return self.df.groupby('platform').agg(agg_dict).reset_index()
    
    def get_top_posts(self, metric: str = 'Post engagement', n: int = 5) -> pd.DataFrame:
        """
        Get top performing posts by a specific metric.
        """
        if metric not in self.df.columns:
            # Try to find similar column
            for col in self.df.columns:
                if metric.lower() in col.lower():
                    metric = col
                    break
            else:
                return pd.DataFrame()
        
        return self.df.nlargest(n, metric)
