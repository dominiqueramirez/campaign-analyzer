"""
Insights Generation Engine
Automatically generates natural-language insights and recommendations for leadership.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .metrics_engine import PerformanceSnapshot, MetricResult


class InsightType(Enum):
    """Types of insights that can be generated."""
    TREND = "trend"
    WIN = "win"
    RISK = "risk"
    RECOMMENDATION = "recommendation"
    CALLOUT = "callout"


class InsightPriority(Enum):
    """Priority levels for insights."""
    HIGH = 3
    MEDIUM = 2
    LOW = 1


@dataclass
class Insight:
    """Represents a generated insight."""
    type: InsightType
    priority: InsightPriority
    title: str
    description: str
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    change_percent: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'type': self.type.value,
            'priority': self.priority.value,
            'title': self.title,
            'description': self.description,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'change_percent': self.change_percent
        }


class InsightsEngine:
    """
    Generates natural-language insights and recommendations from social media data.
    Designed to provide executive-level narratives.
    """
    
    # Thresholds for significant changes
    SIGNIFICANT_INCREASE = 15  # %
    SIGNIFICANT_DECREASE = -15  # %
    MAJOR_INCREASE = 30  # %
    MAJOR_DECREASE = -30  # %
    
    # Templates for insight generation
    INSIGHT_TEMPLATES = {
        'major_increase': {
            'reach': "Reach surged by {change}% — content resonated strongly with the audience this period.",
            'engagement': "Engagement jumped {change}% — posts drove significantly more interaction than the previous period.",
            'clicks': "Click-throughs increased by {change}% — audience showed strong interest in linked content.",
            'reactions': "Reactions increased by {change}% — content generated strong emotional responses.",
            'shares': "Shares spiked {change}% — content was highly share-worthy this period.",
        },
        'major_decrease': {
            'reach': "Reach declined by {change}% — consider reviewing content timing and targeting strategy.",
            'engagement': "Engagement dropped {change}% — audience interaction decreased significantly.",
            'clicks': "Click-throughs fell by {change}% — CTAs may need refreshing or stronger value props.",
            'reactions': "Reactions decreased by {change}% — content may need more emotional hooks.",
            'shares': "Shares declined by {change}% — content shareability needs attention.",
        },
        'moderate_increase': {
            'reach': "Reach grew by {change}% — steady audience expansion.",
            'engagement': "Engagement improved by {change}% — positive momentum in audience interaction.",
            'clicks': "Clicks increased {change}% — good interest in linked content.",
        },
        'moderate_decrease': {
            'reach': "Reach dipped by {change}% — monitor for continued decline.",
            'engagement': "Engagement slipped {change}% — may warrant content strategy review.",
            'clicks': "Clicks decreased {change}% — consider A/B testing CTAs.",
        },
        'stable': {
            'default': "{metric} remained stable compared to the previous period."
        }
    }
    
    RECOMMENDATION_TEMPLATES = {
        'low_engagement': "Consider increasing interactive content formats (polls, questions, carousels) to boost engagement.",
        'low_reach': "Review posting times and frequency — test different schedules to maximize reach.",
        'low_clicks': "Strengthen call-to-action messaging and ensure links provide clear value.",
        'declining_trend': "Performance is trending downward — recommend a content audit and strategy refresh.",
        'strong_performance': "Continue current content strategy — it's delivering strong results.",
        'engagement_opportunity': "High reach but moderate engagement — focus on more engaging content formats.",
        'top_post_success': "Replicate elements from top-performing content: {post_type} format drove highest engagement.",
        'post_frequency': "Consider adjusting posting frequency — {recommendation}.",
    }
    
    def __init__(self, snapshot: PerformanceSnapshot):
        self.snapshot = snapshot
        self.insights: List[Insight] = []
        self.what_happened: List[str] = []
        self.why_it_matters: List[str] = []
        self.what_to_do: List[str] = []
    
    def generate_all_insights(self) -> Dict:
        """
        Generate all insights for the leadership slide.
        
        Returns:
            Dictionary with categorized insights
        """
        self.insights = []
        self.what_happened = []
        self.why_it_matters = []
        self.what_to_do = []
        
        # Generate metric-based insights
        self._analyze_metric_changes()
        
        # Generate trend insights
        self._analyze_trends()
        
        # Generate content insights
        self._analyze_top_content()
        
        # Generate recommendations
        self._generate_recommendations()
        
        # Sort insights by priority
        self.insights.sort(key=lambda x: x.priority.value, reverse=True)
        
        return {
            'insights': [i.to_dict() for i in self.insights],
            'what_happened': self.what_happened[:3],  # Top 3
            'why_it_matters': self.why_it_matters[:3],
            'what_to_do': self.what_to_do[:3],
            'headline_insight': self._generate_headline_insight(),
            'summary': self._generate_executive_summary()
        }
    
    def _analyze_metric_changes(self):
        """Analyze changes in key metrics and generate insights."""
        for metric_name, metric in self.snapshot.metrics.items():
            if metric_name in ['post_count']:
                continue
            
            change = metric.change_percent
            
            # Determine insight type based on change magnitude
            if change >= self.MAJOR_INCREASE:
                self._add_metric_insight(metric, 'major_increase', InsightType.WIN, InsightPriority.HIGH)
            elif change <= self.MAJOR_DECREASE:
                self._add_metric_insight(metric, 'major_decrease', InsightType.RISK, InsightPriority.HIGH)
            elif change >= self.SIGNIFICANT_INCREASE:
                self._add_metric_insight(metric, 'moderate_increase', InsightType.WIN, InsightPriority.MEDIUM)
            elif change <= self.SIGNIFICANT_DECREASE:
                self._add_metric_insight(metric, 'moderate_decrease', InsightType.RISK, InsightPriority.MEDIUM)
    
    def _add_metric_insight(self, metric: MetricResult, template_key: str, 
                           insight_type: InsightType, priority: InsightPriority):
        """Add an insight based on metric performance."""
        templates = self.INSIGHT_TEMPLATES.get(template_key, {})
        template = templates.get(metric.name, templates.get('default', ''))
        
        if not template:
            template = f"{metric.display_name} changed by {{change}}%"
        
        description = template.format(
            change=abs(metric.change_percent),
            metric=metric.display_name,
            value=metric.formatted_current
        )
        
        insight = Insight(
            type=insight_type,
            priority=priority,
            title=f"{metric.display_name}: {'+' if metric.change_percent > 0 else ''}{metric.change_percent:.0f}%",
            description=description,
            metric_name=metric.name,
            metric_value=metric.current_value,
            change_percent=metric.change_percent
        )
        
        self.insights.append(insight)
        
        # Categorize for slide sections
        if insight_type == InsightType.WIN:
            self.what_happened.append(f"✅ {description}")
            self.why_it_matters.append(f"Strong {metric.display_name.lower()} indicates content resonated with the audience.")
        elif insight_type == InsightType.RISK:
            self.what_happened.append(f"⚠️ {description}")
            self.why_it_matters.append(f"Declining {metric.display_name.lower()} may impact overall campaign effectiveness.")
    
    def _analyze_trends(self):
        """Analyze overall trends in the data."""
        metrics = self.snapshot.metrics
        
        # Count positive vs negative trends
        positive_count = sum(1 for m in metrics.values() if m.trend == 'up' and m.is_positive_trend)
        negative_count = sum(1 for m in metrics.values() if m.trend == 'down' and not m.is_positive_trend)
        
        if positive_count > negative_count * 2:
            self.insights.append(Insight(
                type=InsightType.TREND,
                priority=InsightPriority.HIGH,
                title="Strong Overall Performance",
                description="Most key metrics showed positive momentum this period."
            ))
            self.what_happened.append("📈 Overall performance trend is positive across most metrics.")
        elif negative_count > positive_count * 2:
            self.insights.append(Insight(
                type=InsightType.TREND,
                priority=InsightPriority.HIGH,
                title="Performance Decline Detected",
                description="Multiple key metrics declined — recommend strategy review."
            ))
            self.what_happened.append("📉 Performance declined across multiple key metrics.")
    
    def _analyze_top_content(self):
        """Analyze top performing content."""
        top_post = self.snapshot.top_post
        
        if top_post:
            post_type = str(top_post.get('post_type', 'Post'))
            engagement = int(top_post.get('engagement', 0))
            reach = int(top_post.get('reach', 0))
            
            self.insights.append(Insight(
                type=InsightType.CALLOUT,
                priority=InsightPriority.MEDIUM,
                title=f"Top Post: {post_type}",
                description=f"Best performing {post_type.lower()} achieved {engagement:,} engagements and {reach:,} reach.",
                metric_value=engagement
            ))
            
            # Add content insight
            message_preview = str(top_post.get('message', ''))[:100]
            if message_preview:
                self.what_happened.append(f"🏆 Top content: \"{message_preview}...\" drove highest engagement.")
    
    def _generate_recommendations(self):
        """Generate actionable recommendations based on insights."""
        metrics = self.snapshot.metrics
        
        # Check engagement rate
        if 'engagement_rate' in metrics:
            eng_rate = metrics['engagement_rate']
            if eng_rate.current_value < 0.02:  # Below 2%
                self.what_to_do.append("💡 " + self.RECOMMENDATION_TEMPLATES['low_engagement'])
            elif eng_rate.change_percent < -10:
                self.what_to_do.append("💡 Test more engaging content formats — engagement rate is declining.")
        
        # Check reach
        if 'reach' in metrics:
            reach = metrics['reach']
            if reach.change_percent < -20:
                self.what_to_do.append("💡 " + self.RECOMMENDATION_TEMPLATES['low_reach'])
        
        # Check clicks
        if 'clicks' in metrics:
            clicks = metrics['clicks']
            if clicks.change_percent < -15:
                self.what_to_do.append("💡 " + self.RECOMMENDATION_TEMPLATES['low_clicks'])
        
        # Top post recommendation
        if self.snapshot.top_post:
            post_type = self.snapshot.top_post.get('post_type', 'content')
            rec = self.RECOMMENDATION_TEMPLATES['top_post_success'].format(post_type=post_type)
            self.what_to_do.append(f"💡 {rec}")
        
        # Post frequency recommendation
        post_count = metrics.get('post_count')
        if post_count:
            period_days = (self.snapshot.period_end - self.snapshot.period_start).days
            posts_per_week = (post_count.current_value / max(period_days, 1)) * 7
            
            if posts_per_week < 3:
                self.what_to_do.append("💡 Consider increasing posting frequency — currently below 3 posts per week.")
            elif posts_per_week > 21:
                self.what_to_do.append("💡 High posting volume — monitor for audience fatigue and engagement quality.")
        
        # Default recommendation if none generated
        if not self.what_to_do:
            # Check overall performance
            positive_metrics = sum(1 for m in metrics.values() if m.change_percent > 5)
            if positive_metrics >= len(metrics) / 2:
                self.what_to_do.append("💡 " + self.RECOMMENDATION_TEMPLATES['strong_performance'])
            else:
                self.what_to_do.append("💡 Monitor key metrics closely and A/B test content variations.")
    
    def _generate_headline_insight(self) -> str:
        """Generate a single headline insight for the slide."""
        metrics = self.snapshot.metrics
        
        # Find the most significant change
        most_significant = None
        max_abs_change = 0
        
        for name, metric in metrics.items():
            if name == 'post_count':
                continue
            abs_change = abs(metric.change_percent)
            if abs_change > max_abs_change:
                max_abs_change = abs_change
                most_significant = metric
        
        if most_significant and max_abs_change > 10:
            direction = "up" if most_significant.change_percent > 0 else "down"
            return f"{most_significant.display_name} {direction} {abs(most_significant.change_percent):.0f}% vs. previous period"
        
        # Default headline based on post count
        post_count = self.snapshot.post_count
        return f"{post_count} posts analyzed across {len(self.snapshot.platform_breakdown)} platform(s)"
    
    def _generate_executive_summary(self) -> str:
        """Generate a 2-3 sentence executive summary."""
        metrics = self.snapshot.metrics
        period_days = (self.snapshot.period_end - self.snapshot.period_start).days
        
        # Build summary components
        components = []
        
        # Period context
        components.append(f"This {period_days}-day period saw {self.snapshot.post_count} posts published")
        
        # Key metric highlight
        if 'reach' in metrics:
            reach = metrics['reach']
            components[0] += f", reaching {reach.formatted_current} people"
            if abs(reach.change_percent) > 5:
                direction = "up" if reach.change_percent > 0 else "down"
                components[0] += f" ({direction} {abs(reach.change_percent):.0f}%)"
        components[0] += "."
        
        # Engagement summary
        if 'engagement' in metrics:
            eng = metrics['engagement']
            eng_statement = f"Total engagement was {eng.formatted_current}"
            if abs(eng.change_percent) > 5:
                direction = "increased" if eng.change_percent > 0 else "decreased"
                eng_statement += f", which {direction} by {abs(eng.change_percent):.0f}% compared to the previous period"
            eng_statement += "."
            components.append(eng_statement)
        
        # Overall assessment
        positive_count = sum(1 for m in metrics.values() if m.change_percent > 5)
        negative_count = sum(1 for m in metrics.values() if m.change_percent < -5)
        
        if positive_count > negative_count:
            components.append("Overall performance shows positive momentum.")
        elif negative_count > positive_count:
            components.append("Performance requires attention — multiple metrics declined.")
        else:
            components.append("Performance remained relatively stable.")
        
        return " ".join(components)
    
    def get_trend_highlights(self) -> List[Dict]:
        """Get formatted trend highlights for the slide."""
        highlights = []
        
        for metric_name, metric in self.snapshot.metrics.items():
            if metric_name in ['post_count']:
                continue
            
            if abs(metric.change_percent) > 10:
                highlights.append({
                    'metric': metric.display_name,
                    'value': metric.formatted_current,
                    'change': metric.formatted_change,
                    'trend': metric.trend,
                    'is_positive': metric.is_positive_trend
                })
        
        # Sort by absolute change
        highlights.sort(key=lambda x: abs(float(x['change'].replace('%', '').replace('+', ''))), reverse=True)
        
        return highlights[:5]  # Top 5 trends


def generate_insights_report(snapshot: PerformanceSnapshot) -> Dict:
    """
    Convenience function to generate a complete insights report.
    
    Args:
        snapshot: Performance snapshot from MetricsCalculator
        
    Returns:
        Dictionary containing all insights and recommendations
    """
    engine = InsightsEngine(snapshot)
    return engine.generate_all_insights()
