# Campaign Analyzer

**Automatically generate executive-ready social media performance slides in minutes.**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![License](https://img.shields.io/badge/license-MIT-gray)

## Overview

Campaign Analyzer transforms fragmented social media data into decision-ready intelligence. Upload your CSV exports, select a date range, and get a professional one-page leadership slide with automated insights and recommendations.

### Key Features

- 📊 **One-Page Slide Generation** - Executive-ready PowerPoint slide
- 📈 **Automated Insights** - What happened, why it matters, what to do next
- 🔄 **Period Comparison** - Automatic week-over-week analysis
- 🎯 **Top Content Identification** - Highlights best performing posts
- ⚡ **Fast Generation** - Reports in under 2 minutes

### Supported Platforms

- Facebook
- Instagram
- LinkedIn
- X (Twitter)

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Setup

1. **Clone or download** this project

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

Start the Streamlit app:

```bash
streamlit run app.py
```

This will open the application in your default web browser at `http://localhost:8501`.

### Workflow

1. **Upload Data**
   - Click the file uploader in the sidebar
   - Select CSV exports from your social media platforms
   - Multiple files can be uploaded at once

2. **Select Date Range**
   - Choose a preset period (7, 14, or 30 days)
   - Or select a custom date range

3. **Generate Report**
   - Click the "Generate Report" button
   - Wait for analysis to complete (typically < 30 seconds)

4. **Review Insights**
   - View performance metrics
   - See trend analysis
   - Read automated insights

5. **Export**
   - Download PowerPoint slide for presentations
   - Export CSV for data analysis

### Data Format

The app accepts CSV files with social media metrics. The following columns are recognized:

| Column Name | Description |
|------------|-------------|
| Date (GMT) | Post publish date |
| Post engagement | Total engagements |
| Reach | Total reach |
| Clicks | Link clicks |
| Reactions | Total reactions |
| Shares (unique) | Share count |
| Post Message | Post content |
| Post Type | Content type |

## Project Structure

```
Campaign Analyzer/
├── app.py                  # Main Streamlit application
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── src/
    ├── __init__.py
    ├── data_ingestion.py   # Data loading and preprocessing
    ├── metrics_engine.py   # Metrics calculation
    ├── insights_engine.py  # Automated insights generation
    └── slide_generator.py  # PowerPoint generation
```

## Configuration

Edit `config.py` to customize:

- Color scheme
- Insight thresholds
- Metric priorities
- Export settings

## Output

### Leadership Slide Sections

1. **Header** - Brand name, date range, platforms
2. **Performance Snapshot** - Top 5 KPIs with % change
3. **Trend Highlights** - Significant changes
4. **Top Content** - Best performing post
5. **Insights & Recommendations** - Auto-generated analysis

### Metrics Calculated

- Total Reach
- Total Engagement
- Engagement Rate
- Total Clicks
- Total Reactions
- Total Shares
- Posts Published
- Average Engagement per Post

## Troubleshooting

### Common Issues

**App won't start**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (requires 3.9+)

**Data not loading**
- Verify CSV format matches expected columns
- Check for encoding issues (UTF-8 recommended)

**Metrics show as 0**
- Ensure date column is properly formatted
- Check that selected date range contains data

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License.

## Acknowledgments

Developed for the U.S. Department of Veterans Affairs Education Service to streamline social media reporting and enable data-driven decision making.
