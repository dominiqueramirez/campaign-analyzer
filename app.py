"""
Campaign Analyzer - Leadership Slide Generator
Streamlit Application for generating executive-ready social media performance slides.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import sys
import io

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.data_ingestion import SocialMediaDataLoader, DataAggregator
from src.metrics_engine import MetricsCalculator, PerformanceSnapshot
from src.insights_engine import InsightsEngine, generate_insights_report
from src.slide_generator import SlideGenerator, generate_leadership_slide

# Page configuration
st.set_page_config(
    page_title="Campaign Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #003366;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-top: 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        border: 1px solid #e0e0e0;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #003366;
    }
    .metric-change-positive {
        color: #228B22;
        font-weight: 600;
    }
    .metric-change-negative {
        color: #B22222;
        font-weight: 600;
    }
    .metric-label {
        color: #666;
        font-size: 0.9rem;
    }
    .insight-box {
        background-color: #f0f7ff;
        border-left: 4px solid #003366;
        padding: 15px;
        margin: 10px 0;
        border-radius: 0 8px 8px 0;
    }
    .stDownloadButton > button {
        background-color: #003366;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 10px 20px;
    }
    .section-divider {
        border-top: 2px solid #e0e0e0;
        margin: 30px 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'snapshot' not in st.session_state:
        st.session_state.snapshot = None
    if 'insights' not in st.session_state:
        st.session_state.insights = None
    if 'loader' not in st.session_state:
        st.session_state.loader = SocialMediaDataLoader()


def render_header():
    """Render the application header."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<p class="main-header">📊 Campaign Analyzer</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Generate executive-ready social media performance slides in minutes</p>', unsafe_allow_html=True)
    
    with col2:
        st.image("https://www.va.gov/img/homepage/va-logo-white-bg.png", width=150)


def render_sidebar():
    """Render the sidebar with data upload and settings."""
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # File upload section
        st.subheader("📁 Load Data")
        
        # Option 1: File path input (more reliable)
        file_path = st.text_input(
            "Enter file path (or drag file here)",
            placeholder=r"C:\path\to\your\file.csv",
            help="Paste the full path to your CSV file"
        )
        
        if file_path and st.button("📂 Load from Path"):
            try:
                import os
                if os.path.exists(file_path):
                    loader = st.session_state.loader
                    df = loader.load_csv(file_path)
                    st.session_state.df = df
                    st.session_state.data_loaded = True
                    st.success(f"✅ Loaded {len(df)} posts!")
                else:
                    st.error("File not found. Please check the path.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        st.divider()
        
        # Option 2: File uploader
        uploaded_files = st.file_uploader(
            "Or upload CSV file",
            type=['csv'],
            accept_multiple_files=True,
            help="Upload CSV exports from Facebook, Instagram, LinkedIn, or X (Twitter)"
        )
        
        if uploaded_files:
            process_uploads(uploaded_files)
        
        # Date range selection
        st.subheader("📅 Date Range")
        
        date_options = {
            "Last 7 Days": 7,
            "Last 14 Days": 14,
            "Last 30 Days": 30,
            "Custom Range": 0
        }
        
        selected_range = st.selectbox(
            "Select reporting period",
            options=list(date_options.keys()),
            index=0
        )
        
        if selected_range == "Custom Range":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
            with col2:
                end_date = st.date_input("End Date", datetime.now())
        else:
            days = date_options[selected_range]
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
        
        st.session_state.start_date = datetime.combine(start_date, datetime.min.time())
        st.session_state.end_date = datetime.combine(end_date, datetime.max.time())
        
        # Generate button
        st.markdown("---")
        
        if st.button("🚀 Generate Report", type="primary", use_container_width=True):
            if st.session_state.data_loaded:
                generate_report()
            else:
                st.error("Please upload data first!")
        
        # Data quality info
        if st.session_state.data_loaded:
            st.markdown("---")
            st.subheader("📊 Data Summary")
            df = st.session_state.df
            st.metric("Total Posts", len(df))
            if 'platform' in df.columns:
                platforms = df['platform'].unique()
                st.write(f"**Platforms:** {', '.join([p.title() for p in platforms])}")
            if 'date' in df.columns:
                st.write(f"**Date Range:** {df['date'].min().strftime('%b %d')} - {df['date'].max().strftime('%b %d, %Y')}")


def process_uploads(uploaded_files):
    """Process uploaded CSV files."""
    loader = st.session_state.loader
    all_dfs = []
    
    for file in uploaded_files:
        try:
            # Read CSV
            df = pd.read_csv(file)
            
            # Detect and process platform data
            platform = loader.detect_platform(df)
            processed_df = loader._preprocess_data(df, platform)
            all_dfs.append(processed_df)
            
            st.sidebar.success(f"✅ Loaded: {file.name} ({platform.title()})")
        except Exception as e:
            st.sidebar.error(f"❌ Error loading {file.name}: {str(e)}")
    
    if all_dfs:
        st.session_state.df = pd.concat(all_dfs, ignore_index=True)
        st.session_state.data_loaded = True


def generate_report():
    """Generate the performance report and insights."""
    with st.spinner("Analyzing data and generating insights..."):
        df = st.session_state.df
        start_date = st.session_state.start_date
        end_date = st.session_state.end_date
        
        # Calculate metrics
        calculator = MetricsCalculator(df)
        snapshot = calculator.calculate_snapshot(start_date, end_date)
        
        # Generate insights
        insights = generate_insights_report(snapshot)
        
        # Store in session state
        st.session_state.snapshot = snapshot
        st.session_state.insights = insights
        
        st.success("✅ Report generated successfully!")


def render_performance_snapshot():
    """Render the performance snapshot section."""
    snapshot = st.session_state.snapshot
    if not snapshot:
        return
    
    st.subheader("📊 Performance Snapshot")
    
    # Get headline metrics (now includes reactions/likes and shares)
    headline_metrics = snapshot.get_headline_metrics()
    
    # Create columns for metrics - show up to 6 metrics
    num_metrics = min(len(headline_metrics), 6)
    cols = st.columns(num_metrics)
    
    for i, metric in enumerate(headline_metrics[:6]):
        with cols[i]:
            # Determine change color
            if metric.is_positive_trend:
                delta_color = "normal"
            elif metric.trend == 'stable':
                delta_color = "off"
            else:
                delta_color = "inverse"
            
            st.metric(
                label=metric.display_name,
                value=metric.formatted_current,
                delta=metric.formatted_change,
                delta_color=delta_color
            )


def render_trend_chart():
    """Render trend visualization chart."""
    df = st.session_state.df
    snapshot = st.session_state.snapshot
    
    if df is None or 'date' not in df.columns:
        return
    
    st.subheader("📈 Performance Trends")
    
    # Map possible column names to standard names
    column_mapping = {
        'engagement': ['engagement', 'Post engagement', 'Engagement', 'engagements'],
        'reach': ['reach', 'Reach', 'Total Reach'],
        'clicks': ['clicks', 'Clicks', 'Link Clicks']
    }
    
    # Find actual column names in the dataframe
    agg_dict = {}
    actual_cols = {}
    for standard_name, possible_names in column_mapping.items():
        for col_name in possible_names:
            if col_name in df.columns:
                agg_dict[col_name] = 'sum'
                actual_cols[standard_name] = col_name
                break
    
    if not agg_dict:
        st.info("No metrics available for trend chart.")
        return
    
    # Aggregate by date
    daily_data = df.groupby(df['date'].dt.date).agg(agg_dict).reset_index()
    
    # Rename columns to standard names
    rename_dict = {'date': 'Date'}
    for standard_name, actual_name in actual_cols.items():
        rename_dict[actual_name] = standard_name.title()
    daily_data = daily_data.rename(columns=rename_dict)
    
    # Create chart
    fig = go.Figure()
    
    if 'Engagement' in daily_data.columns:
        fig.add_trace(go.Scatter(
            x=daily_data['Date'],
            y=daily_data['Engagement'],
            name='Engagement',
            line=dict(color='#003366', width=2),
            mode='lines+markers'
        ))
    
    if 'Reach' in daily_data.columns:
        fig.add_trace(go.Bar(
            x=daily_data['Date'],
            y=daily_data['Reach'],
            name='Reach',
            marker_color='rgba(0, 94, 162, 0.3)',
            yaxis='y2'
        ))
    
    fig.update_layout(
        height=350,
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title="Engagement", side="left"),
        yaxis2=dict(title="Reach", side="right", overlaying="y"),
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_insights_section():
    """Render the insights and recommendations section."""
    insights = st.session_state.insights
    if not insights:
        return
    
    st.subheader("💡 Insights & Recommendations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("##### 📋 What Happened")
        for item in insights.get('what_happened', [])[:3]:
            st.markdown(f"""
            <div class="insight-box">
                {item}
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("##### 🎯 Why It Matters")
        for item in insights.get('why_it_matters', [])[:3]:
            st.markdown(f"""
            <div class="insight-box">
                {item}
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("##### 🚀 What To Do Next")
        for item in insights.get('what_to_do', [])[:3]:
            st.markdown(f"""
            <div class="insight-box">
                {item}
            </div>
            """, unsafe_allow_html=True)


def render_top_content():
    """Render top performing content section."""
    snapshot = st.session_state.snapshot
    if not snapshot or not snapshot.top_post:
        return
    
    st.subheader("🏆 Top Performing Content")
    
    top_post = snapshot.top_post
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**Post Type:** {top_post.get('post_type', 'Post')}")
        message = top_post.get('message', 'No message available')
        st.markdown(f"> _{message[:300]}{'...' if len(message) > 300 else ''}_")
        
        if top_post.get('permalink'):
            st.markdown(f"[View Original Post]({top_post.get('permalink')})")
    
    with col2:
        st.metric("Engagement", f"{top_post.get('engagement', 0):,}")
        st.metric("Reach", f"{top_post.get('reach', 0):,}")
        st.metric("Shares", f"{top_post.get('shares', 0):,}")


def render_export_section():
    """Render the export section with download buttons."""
    snapshot = st.session_state.snapshot
    insights = st.session_state.insights
    
    if not snapshot or not insights:
        return
    
    st.markdown("---")
    st.subheader("📥 Export Report")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Generate PowerPoint
        if st.button("📊 Generate PowerPoint Slide", use_container_width=True):
            with st.spinner("Generating PowerPoint..."):
                generator = generate_leadership_slide(snapshot, insights)
                pptx_bytes = generator.to_bytes()
                
                st.download_button(
                    label="⬇️ Download PowerPoint",
                    data=pptx_bytes,
                    file_name=f"social_media_report_{datetime.now().strftime('%Y%m%d')}.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True
                )
    
    with col2:
        # Export to CSV
        if st.button("📋 Export Data Summary", use_container_width=True):
            # Create summary dataframe
            metrics_data = []
            for name, metric in snapshot.metrics.items():
                metrics_data.append({
                    'Metric': metric.display_name,
                    'Current Period': metric.formatted_current,
                    'Previous Period': metric._format_value(metric.previous_value),
                    'Change': metric.formatted_change,
                    'Trend': metric.trend.title()
                })
            
            summary_df = pd.DataFrame(metrics_data)
            csv_data = summary_df.to_csv(index=False)
            
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"metrics_summary_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col3:
        st.info("💡 **Tip:** The PowerPoint slide is designed for leadership presentations - one slide with all key insights!")


def render_data_preview():
    """Render a preview of the loaded data."""
    df = st.session_state.df
    if df is None:
        return
    
    with st.expander("📋 View Raw Data", expanded=False):
        # Show summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Posts", len(df))
        with col2:
            # Try different column names for engagement
            eng_col = next((c for c in ['engagement', 'Post engagement', 'Engagement'] if c in df.columns), None)
            if eng_col:
                st.metric("Total Engagement", f"{df[eng_col].sum():,.0f}")
        with col3:
            # Try different column names for reach
            reach_col = next((c for c in ['reach', 'Reach', 'Total Reach'] if c in df.columns), None)
            if reach_col:
                st.metric("Total Reach", f"{df[reach_col].sum():,.0f}")
        
        # Show data table - use available columns
        possible_cols = ['date', 'platform', 'Post Type', 'post_type', 'Post engagement', 'engagement', 
                         'Reach', 'reach', 'Clicks', 'clicks', 'Reactions', 'reactions', 'Shares (unique)', 'shares']
        display_cols = [col for col in possible_cols if col in df.columns]
        if display_cols:
            st.dataframe(df[display_cols].head(20), use_container_width=True)
        else:
            st.dataframe(df.head(20), use_container_width=True)


def render_welcome_screen():
    """Render welcome screen when no data is loaded."""
    st.markdown("""
    ## Welcome to Campaign Analyzer! 👋
    
    Generate executive-ready social media performance slides in minutes, not hours.
    
    ### Getting Started
    
    1. **Upload your data** - Use the sidebar to upload CSV exports from your social media platforms
    2. **Select date range** - Choose the reporting period (7, 14, 30 days, or custom)
    3. **Generate report** - Click the generate button to analyze your data
    4. **Export** - Download your leadership-ready PowerPoint slide
    
    ### Supported Platforms
    - 📘 Facebook
    - 📸 Instagram  
    - 💼 LinkedIn
    - 🐦 X (Twitter)
    
    ### What You'll Get
    - **Performance Snapshot** - Key metrics at a glance with period-over-period comparison
    - **Trend Analysis** - Automated detection of significant changes
    - **Top Content** - Your best performing posts highlighted
    - **AI Insights** - What happened, why it matters, and what to do next
    - **One-Page Slide** - Export-ready PowerPoint for leadership meetings
    
    ---
    
    👈 **Start by uploading your social media data in the sidebar**
    """)


def render_post_search():
    """Render the post search feature."""
    st.subheader("🔍 Post Search")
    st.write("Search for specific posts and view their detailed metrics.")
    
    df = st.session_state.df
    if df is None:
        st.warning("Please load data first.")
        return
    
    # Determine the message column name
    message_col = next((c for c in ['message', 'Post Message', 'Message', 'post_message'] if c in df.columns), None)
    
    if message_col is None:
        st.error("No post message column found in data.")
        return
    
    # Search input
    search_query = st.text_input(
        "Search posts by text",
        placeholder="Enter keywords to search for...",
        help="Search through post messages to find specific content"
    )
    
    if search_query:
        # Filter posts containing the search query (case insensitive)
        mask = df[message_col].astype(str).str.lower().str.contains(search_query.lower(), na=False)
        results = df[mask].copy()
        
        if len(results) == 0:
            st.info(f"No posts found containing '{search_query}'")
        else:
            st.success(f"Found {len(results)} post(s) matching '{search_query}'")
            
            # Display each matching post with its metrics
            for idx, row in results.iterrows():
                with st.expander(f"📝 Post from {row.get('date', 'Unknown date')}", expanded=True):
                    # Post content
                    st.markdown("**Post Content:**")
                    message = str(row.get(message_col, 'No message'))
                    st.markdown(f"> {message[:500]}{'...' if len(message) > 500 else ''}")
                    
                    # Post metadata
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        post_type = row.get('Post Type', row.get('post_type', 'N/A'))
                        st.markdown(f"**Type:** {post_type}")
                    with col2:
                        platform = row.get('platform', 'N/A')
                        st.markdown(f"**Platform:** {platform.title() if platform != 'N/A' else 'N/A'}")
                    with col3:
                        date_val = row.get('date', 'N/A')
                        if hasattr(date_val, 'strftime'):
                            date_str = date_val.strftime('%b %d, %Y')
                        else:
                            date_str = str(date_val)
                        st.markdown(f"**Date:** {date_str}")
                    
                    st.divider()
                    
                    # Metrics display
                    st.markdown("**📊 Post Metrics:**")
                    
                    # Define metric mappings (display name, possible column names)
                    metric_definitions = [
                        ("Reach", ['reach', 'Reach', 'Total Reach']),
                        ("Engagement", ['engagement', 'Post engagement', 'Engagement']),
                        ("Reactions/Likes", ['reactions', 'Reactions', 'Likes', 'likes']),
                        ("Shares", ['shares', 'Shares (unique)', 'Shares']),
                        ("Clicks", ['clicks', 'Clicks', 'Link Clicks']),
                        ("Comments", ['comments', 'Comments']),
                        ("Viral Reach", ['viral_reach', 'Viral reach', 'Viral Reach']),
                        ("Impressions", ['impressions', 'Fan impressions (unique)', 'Impressions']),
                    ]
                    
                    # Create metrics display in rows of 4
                    metrics_found = []
                    for display_name, col_names in metric_definitions:
                        for col_name in col_names:
                            if col_name in row.index:
                                value = row[col_name]
                                if pd.notna(value):
                                    metrics_found.append((display_name, value))
                                break
                    
                    # Display metrics in columns
                    if metrics_found:
                        cols = st.columns(4)
                        for i, (metric_name, metric_value) in enumerate(metrics_found):
                            with cols[i % 4]:
                                # Format the value
                                if isinstance(metric_value, float):
                                    if metric_value < 1:
                                        formatted = f"{metric_value:.2%}"
                                    elif metric_value >= 1000:
                                        formatted = f"{metric_value:,.0f}"
                                    else:
                                        formatted = f"{metric_value:.0f}"
                                else:
                                    formatted = f"{int(metric_value):,}" if pd.notna(metric_value) else "N/A"
                                
                                st.metric(label=metric_name, value=formatted)
                    else:
                        st.info("No metrics available for this post.")
                    
                    # Engagement rate calculation
                    reach_col = next((c for c in ['reach', 'Reach'] if c in row.index and pd.notna(row[c]) and row[c] > 0), None)
                    eng_col = next((c for c in ['engagement', 'Post engagement'] if c in row.index and pd.notna(row[c])), None)
                    
                    if reach_col and eng_col:
                        eng_rate = (row[eng_col] / row[reach_col]) * 100
                        st.markdown(f"**Engagement Rate:** {eng_rate:.2f}%")
                    
                    # Link to original post
                    permalink = row.get('permalink', row.get('Post Permalink', None))
                    if permalink and pd.notna(permalink):
                        st.markdown(f"[🔗 View Original Post]({permalink})")
    else:
        # Show recent posts when no search query
        st.markdown("---")
        st.markdown("**Recent Posts Preview:**")
        
        # Show last 5 posts
        recent = df.head(5)
        for idx, row in recent.iterrows():
            message = str(row.get(message_col, ''))[:100]
            date_val = row.get('date', '')
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime('%b %d')
            else:
                date_str = str(date_val)[:10]
            
            engagement = row.get('Post engagement', row.get('engagement', 0))
            st.markdown(f"• **{date_str}**: {message}... ({int(engagement):,} engagements)")


def main():
    """Main application entry point."""
    init_session_state()
    
    # Render header
    render_header()
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    if not st.session_state.data_loaded:
        render_welcome_screen()
    else:
        # Create tabs for different features
        tab1, tab2 = st.tabs(["📊 Dashboard", "🔍 Post Search"])
        
        with tab1:
            # Show data preview
            render_data_preview()
            
            # If report is generated, show results
            if st.session_state.snapshot:
                render_performance_snapshot()
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    render_trend_chart()
                with col2:
                    render_top_content()
                
                render_insights_section()
                render_export_section()
            else:
                st.info("👆 Click 'Generate Report' in the sidebar to analyze your data and generate insights!")
        
        with tab2:
            render_post_search()


if __name__ == "__main__":
    main()
