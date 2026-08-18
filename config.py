# Campaign Analyzer Configuration

# Application Settings
APP_NAME = "Campaign Analyzer"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Generate executive-ready social media performance slides"

# Date Range Defaults
DEFAULT_PERIOD_DAYS = 7
MIN_PERIOD_DAYS = 7
MAX_PERIOD_DAYS = 365

# Thresholds for Insights
SIGNIFICANT_CHANGE_THRESHOLD = 15  # Percentage
MAJOR_CHANGE_THRESHOLD = 30  # Percentage
STABLE_THRESHOLD = 5  # Percentage

# Metric Priorities (for display order)
METRIC_PRIORITY = [
    'reach',
    'engagement', 
    'engagement_rate',
    'clicks',
    'reactions',
    'shares',
    'impressions',
    'viral_reach',
]

# Color Scheme (VA Brand aligned)
COLORS = {
    'primary': '#003366',
    'secondary': '#005EA2',
    'accent': '#1A4480',
    'success': '#228B22',
    'warning': '#FFBE2E',
    'danger': '#B22222',
    'light': '#F8F9FA',
    'dark': '#1B1B1B',
    'gray': '#71767A',
}

# Slide Layout Settings
SLIDE_SETTINGS = {
    'width_inches': 13.333,
    'height_inches': 7.5,
    'margin_inches': 0.3,
    'header_height_inches': 0.9,
    'footer_height_inches': 0.35,
}

# Export Settings
EXPORT_SETTINGS = {
    'pptx_enabled': True,
    'pdf_enabled': False,  # Requires additional setup
    'csv_enabled': True,
    'google_slides_enabled': False,  # Future feature
}

# Platform Configuration
PLATFORM_CONFIG = {
    'facebook': {
        'name': 'Facebook',
        'icon': '📘',
        'color': '#1877F2',
        'metrics': ['reach', 'engagement', 'clicks', 'reactions', 'shares'],
    },
    'instagram': {
        'name': 'Instagram',
        'icon': '📸',
        'color': '#E4405F',
        'metrics': ['reach', 'engagement', 'likes', 'comments', 'saves'],
    },
    'linkedin': {
        'name': 'LinkedIn',
        'icon': '💼',
        'color': '#0A66C2',
        'metrics': ['impressions', 'engagement', 'clicks', 'reactions', 'shares'],
    },
    'twitter': {
        'name': 'X (Twitter)',
        'icon': '🐦',
        'color': '#1DA1F2',
        'metrics': ['impressions', 'engagement', 'likes', 'retweets', 'replies'],
    },
}

# Insight Templates Configuration
INSIGHT_CONFIG = {
    'max_what_happened': 3,
    'max_why_matters': 3,
    'max_what_to_do': 3,
    'include_emojis': True,
}
