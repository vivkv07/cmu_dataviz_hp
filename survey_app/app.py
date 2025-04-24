import streamlit as st
import pandas as pd
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
from sklearn.preprocessing import MultiLabelBinarizer

# Set page configuration
st.set_page_config(
    page_title="Central Michigan University Data Visualization Workshop",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CMU Colors
CMU_MAROON = "#6a0032"
CMU_GOLD = "#ffb400"
CMU_MAROON_LIGHT = "#8c1046"
CMU_MAROON_DARK = "#4c0023"
CMU_GOLD_LIGHT = "#ffca4d"
CMU_GOLD_DARK = "#e6a200"

# CMU Color Sequences for Charts
CMU_COLOR_SEQUENCE = [CMU_MAROON, CMU_GOLD, CMU_MAROON_LIGHT, CMU_GOLD_LIGHT, CMU_MAROON_DARK, CMU_GOLD_DARK]
CMU_CONTINUOUS_COLORS = [[0, CMU_GOLD_LIGHT], [0.5, CMU_GOLD], [1, CMU_MAROON]]

# CMU Maroon and Gold Themed CSS
st.markdown("""
<style>
    /* CMU Colors */
    :root {
        --cmu-maroon: #6a0032;
        --cmu-gold: #ffb400;
        --cmu-maroon-light: #8c1046;
        --cmu-maroon-dark: #4c0023;
        --cmu-gold-light: #ffca4d;
        --cmu-gold-dark: #e6a200;
        --light-bg: #f9f9f9;
        --card-bg: #ffffff;
        --text-dark: #333333;
        --text-light: #666666;
    }
    
    /* Global styles */
    .main {
        background-color: var(--light-bg);
        padding: 1.5rem;
    }
    
    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Georgia', serif;
        color: var(--cmu-maroon);
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    h1 {
        font-size: 2.5rem;
        padding-bottom: 0.5rem;
        text-align: center;
        margin-top: 0.5rem;
        margin-bottom: 1.5rem;
    }
    
    h2 {
        font-size: 1.8rem;
        padding-left: 0;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        color: var(--cmu-maroon);
    }
    
    /* Card components */
    .card {
        background-color: var(--card-bg);
        border-radius: 0.5rem;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        margin-bottom: 2rem;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: var(--cmu-maroon);
        color: white;
        padding: 1rem;
    }
    
    /* Sidebar headings */
    .sidebar h2, .sidebar h3 {
        color: var(--cmu-gold);
    }
    
    /* Metrics */
    .metric-container {
        background-color: var(--card-bg);
        border-radius: 0.5rem;
        padding: 1.25rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        text-align: center;
        margin-bottom: 1rem;
        border-top: 4px solid var(--cmu-gold);
    }
    
    .metric-value {
        font-size: 2.25rem;
        font-weight: 700;
        color: var(--cmu-maroon);
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: var(--text-light);
        font-weight: 500;
    }
    
    /* Footer */
    .footer {
        margin-top: 3rem;
        padding-top: 1rem;
        text-align: center;
        color: var(--text-light);
        font-size: 0.9rem;
    }
    
    /* Section styling */
    .section-title {
        color: var(--cmu-maroon);
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
    }
    
    /* Alert styling */
    .info-box {
        background-color: rgba(106, 0, 50, 0.05);
        border-left: 4px solid var(--cmu-maroon);
        padding: 1rem;
        border-radius: 0.25rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.markdown("<h1>Central Michigan University Data Visualization Workshop</h1>", unsafe_allow_html=True)

# =================== Load and Prepare Data ===================
@st.cache_data
def load_data():
    df = pd.read_excel("CMU-DataVisualization-Responses.xlsx", sheet_name="Form Responses 1")
    df.columns = [col.strip() for col in df.columns]  # Clean column names
    
    # Assuming there's a timestamp column for when the form was submitted
    # Typical Google Form has 'Timestamp' as first column
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Response Date'] = df['Timestamp'].dt.date
    
    return df

df = load_data()

# Sidebar filters
with st.sidebar:
    st.markdown("<h2 style='color: #ffb400;'>Filters</h2>", unsafe_allow_html=True)
    
    prog_col = "What is your current program of study?"
    bg_col = "What is your academic background?"
    
    selected_programs = st.multiselect(
        "Program of Study", 
        df[prog_col].dropna().unique(),
        default=df[prog_col].dropna().unique()
    )
    
    selected_backgrounds = st.multiselect(
        "Academic Background", 
        df[bg_col].dropna().unique(),
        default=df[bg_col].dropna().unique()
    )
    
    # Date range filter if timestamp exists
    if 'Response Date' in df.columns:
        min_date = df['Response Date'].min()
        max_date = df['Response Date'].max()
        
        selected_date_range = st.date_input(
            "Response Date Range",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
        
        if len(selected_date_range) == 2:
            start_date, end_date = selected_date_range
            date_filter = (df['Response Date'] >= start_date) & (df['Response Date'] <= end_date)
        else:
            date_filter = True
    else:
        date_filter = True

# Apply filters
if 'Response Date' in df.columns:
    filtered_df = df[
        df[prog_col].isin(selected_programs) & 
        df[bg_col].isin(selected_backgrounds) &
        date_filter
    ]
else:
    filtered_df = df[
        df[prog_col].isin(selected_programs) & 
        df[bg_col].isin(selected_backgrounds)
    ]

# =================== Enhanced Helpers ===================
def extract_other_responses(series, option_list):
    """Extract 'Other...' responses and their text content."""
    other_responses = []
    other_pattern = re.compile(r'Other[.…]*\s*(.*)', re.IGNORECASE)
    
    for response in series.dropna():
        match = other_pattern.search(response)
        if match and match.group(1).strip():
            other_responses.append(match.group(1).strip())
            
    return other_responses

def count_multiselect_matches(series, valid_options, extract_other=False):
    """Accurately count exact selections from multiselect columns with other handling."""
    counter = Counter()
    other_responses = []
    
    for row in series.dropna():
        has_other = False
        for option in valid_options:
            if option in row:
                if option.startswith("Other"):
                    has_other = True
                else:
                    counter[option] += 1
        
        # Extract Other text if present
        if has_other and extract_other:
            other_match = re.search(r'Other[.…]*\s*(.*)', row)
            if other_match and other_match.group(1).strip():
                other_responses.append(other_match.group(1).strip())
    
    return counter, other_responses

# =================== Key Metrics ===================
st.markdown("<h2>Key Metrics</h2>", unsafe_allow_html=True)

# Calculate key metrics
total_responses = len(filtered_df)
if 'Timestamp' in df.columns:
    response_days = filtered_df['Response Date'].nunique()
    earliest_response = filtered_df['Response Date'].min()
    latest_response = filtered_df['Response Date'].max()
else:
    response_days = "N/A"
    earliest_response = "N/A"
    latest_response = "N/A"

# Display key metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"<div class='metric-container'>"
        f"<div class='metric-value'>{total_responses}</div>"
        f"<div class='metric-label'>Total Responses</div>"
        f"</div>",
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"<div class='metric-container'>"
        f"<div class='metric-value'>{response_days}</div>"
        f"<div class='metric-label'>Collection Days</div>"
        f"</div>",
        unsafe_allow_html=True
    )

# Average work experience
with col3:
    exp_col = "Do you have any work experience?"
    exp_vals = pd.to_numeric(filtered_df[exp_col], errors='coerce').dropna()
    avg_exp = exp_vals.mean() if not exp_vals.empty else 0
    
    st.markdown(
        f"<div class='metric-container'>"
        f"<div class='metric-value'>{avg_exp:.1f}</div>"
        f"<div class='metric-label'>Avg Work Experience (Years)</div>"
        f"</div>",
        unsafe_allow_html=True
    )

# International student percentage
with col4:
    intl_col = "Are you an international student?"
    if intl_col in filtered_df.columns:
        intl_pct = (filtered_df[intl_col] == "Yes").mean() * 100
        
        st.markdown(
            f"<div class='metric-container'>"
            f"<div class='metric-value'>{intl_pct:.1f}%</div>"
            f"<div class='metric-label'>International Students</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='metric-container'>"
            f"<div class='metric-value'>N/A</div>"
            f"<div class='metric-label'>International Students</div>"
            f"</div>",
            unsafe_allow_html=True
        )

# =================== Response Timeline ===================
if 'Response Date' in df.columns:
    st.markdown("<h2>Response Timeline</h2>", unsafe_allow_html=True)
    
    # Create a date range from min to max date
    min_date = filtered_df['Response Date'].min()
    max_date = filtered_df['Response Date'].max()
    
    # Count responses by date
    response_counts = filtered_df.groupby('Response Date').size().reset_index(name='Count')
    
    # Create a complete date range (including days with 0 responses)
    all_dates = pd.date_range(start=min_date, end=max_date, freq='D')
    complete_date_df = pd.DataFrame({'Response Date': all_dates})
    complete_date_df['Response Date'] = complete_date_df['Response Date'].dt.date
    
    # Merge with actual counts
    timeline_df = pd.merge(complete_date_df, response_counts, on='Response Date', how='left').fillna(0)
    
    # Create a line graph with markers
    fig_timeline = go.Figure()
    
    fig_timeline.add_trace(
        go.Scatter(
            x=timeline_df['Response Date'],
            y=timeline_df['Count'],
            mode='lines+markers',
            name='Responses',
            line=dict(color=CMU_MAROON, width=2),
            marker=dict(size=8, color=CMU_MAROON, line=dict(width=2, color='white'))
        )
    )
    
    # Configure layout
    fig_timeline.update_layout(
        title=None,
        xaxis_title='Date',
        yaxis_title='Number of Responses',
        template='plotly_white',
        height=400,
        margin=dict(l=40, r=40, t=20, b=40),
    )
    
    # Add a moving average trendline
    if len(timeline_df) > 3:  # Only add trendline if we have enough data points
        timeline_df['MA3'] = timeline_df['Count'].rolling(window=3, min_periods=1).mean()
        
        fig_timeline.add_trace(
            go.Scatter(
                x=timeline_df['Response Date'],
                y=timeline_df['MA3'],
                mode='lines',
                name='3-Day Moving Average',
                line=dict(color=CMU_GOLD, width=2, dash='dot')
            )
        )
    
    # Add annotations for peak days
    peak_day = timeline_df.loc[timeline_df['Count'].idxmax()]
    fig_timeline.add_annotation(
        x=peak_day['Response Date'],
        y=peak_day['Count'],
        text=f"Peak: {int(peak_day['Count'])} responses",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#333333",
        ax=-30,
        ay=-30
    )
    
    st.plotly_chart(fig_timeline, use_container_width=True)

# =================== Demographics ===================
st.markdown("<h2>Participant Demographics</h2>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    prog_counts = filtered_df[prog_col].value_counts()
    
    fig_prog = px.pie(
        names=prog_counts.index,
        values=prog_counts.values,
        title=None,
        hole=0.5,
        color_discrete_sequence=[CMU_MAROON, CMU_GOLD, CMU_MAROON_LIGHT, CMU_GOLD_LIGHT, CMU_MAROON_DARK, CMU_GOLD_DARK]
    )
    
    fig_prog.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=10)
        ),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    
    fig_prog.add_annotation(
        text="Program Distribution",
        showarrow=False,
        font=dict(size=14, color=CMU_MAROON),
        x=0.5,
        y=0.5
    )
    
    st.plotly_chart(fig_prog, use_container_width=True)

with col2:
    intl_col = "Are you an international student?"
    intl_counts = filtered_df[intl_col].value_counts()
    
    fig_intl = px.pie(
        names=intl_counts.index,
        values=intl_counts.values,
        title=None,
        hole=0.5,
        color_discrete_sequence=[CMU_MAROON, CMU_GOLD]
    )
    
    fig_intl.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=10)
        ),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    
    fig_intl.add_annotation(
        text="International Students",
        showarrow=False,
        font=dict(size=14, color=CMU_MAROON),
        x=0.5,
        y=0.5
    )
    
    st.plotly_chart(fig_intl, use_container_width=True)

with col3:
    exp_col = "Do you have any work experience?"
    exp_vals = pd.to_numeric(filtered_df[exp_col], errors='coerce').dropna()
    
    # Create bins for work experience
    bins = [0, 1, 3, 5, 10, max(exp_vals.max() + 1, 15)]
    labels = ['< 1 year', '1-3 years', '3-5 years', '5-10 years', '10+ years']
    
    exp_binned = pd.cut(exp_vals, bins=bins, labels=labels)
    exp_dist = exp_binned.value_counts().sort_index()
    
    fig_exp = px.bar(
        x=exp_dist.index,
        y=exp_dist.values,
        labels={"x": "Experience", "y": "Count"},
        title="Work Experience Distribution",
        color_discrete_sequence=[CMU_MAROON] * len(exp_dist),
        text=exp_dist.values
    )
    
    fig_exp.update_layout(
        title=None,
        xaxis_tickangle=-45,
        margin=dict(l=20, r=20, t=30, b=60),
        showlegend=False
    )
    
    fig_exp.update_traces(
        marker_color=CMU_MAROON,
        textposition='outside',
        textfont=dict(color='#333333')
    )
    
    st.plotly_chart(fig_exp, use_container_width=True)

# =================== SQL Experience ===================
st.markdown("<h2>SQL/MySQL Experience</h2>", unsafe_allow_html=True)

sql_col = "How would you rate your experience with SQL/MySQL?"
sql_levels = [
    "No experience",
    "Beginner (basic SELECT queries)",
    "Intermediate (JOINs, subqueries, etc.)",
    "Advanced (CTEs, window functions, optimization)"
]

sql_counts = filtered_df[sql_col].value_counts().reindex(sql_levels, fill_value=0)

# Create two columns - one for pie chart, one for horizontal bar
sql_col1, sql_col2 = st.columns(2)

with sql_col1:
    # Pie chart
    fig_sql_pie = px.pie(
        names=sql_counts.index,
        values=sql_counts.values,
        title=None,
        hole=0.5,
        color_discrete_sequence=[CMU_GOLD_LIGHT, CMU_GOLD, CMU_MAROON_LIGHT, CMU_MAROON]
    )
    
    fig_sql_pie.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=10)
        ),
        margin=dict(l=20, r=20, t=30, b=60)
    )
    
    fig_sql_pie.add_annotation(
        text="Self-Rated SQL Experience",
        showarrow=False,
        font=dict(size=14, color=CMU_MAROON),
        x=0.5,
        y=0.5
    )
    
    st.plotly_chart(fig_sql_pie, use_container_width=True)

with sql_col2:
    # Horizontal bar
    fig_sql_bar = px.bar(
        y=sql_counts.index,
        x=sql_counts.values,
        orientation='h',
        title=None,
        text=sql_counts.values,
    )
    
    fig_sql_bar.update_layout(
        yaxis=dict(categoryorder='array', categoryarray=sql_levels),
        xaxis_title="Number of Students",
        yaxis_title="",
        showlegend=False,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    
    # Set custom colors for each bar
    fig_sql_bar.update_traces(
        marker_color=[CMU_GOLD_LIGHT, CMU_GOLD, CMU_MAROON_LIGHT, CMU_MAROON],
        textposition='outside',
        textfont=dict(color='#333333')
    )
    
    fig_sql_bar.add_annotation(
        text="SQL Proficiency Levels",
        showarrow=False,
        font=dict(size=14, color=CMU_MAROON),
        xref="paper",
        yref="paper",
        x=0.5,
        y=1.05
    )
    
    st.plotly_chart(fig_sql_bar, use_container_width=True)

# =================== Learning Goals ===================
st.markdown("<h2>What Students Want to Learn</h2>", unsafe_allow_html=True)

goal_col = "What would you most like to get out of this session? (Choose up to 3 Topics you  want to learn or walk away with.)"
goal_options = [
    "Understand the role and importance of data visualization in the real world",
    "Learn how companies deal with complex data (e.g., arrays, nested data) during visualization",
    "Discover common challenges and pitfalls in data visualization – and how to avoid them",
    "Understand how different data roles (analyst, engineer, scientist) interact with visualization",
    "Hear real-world examples of how visualizations drive business decisions",
    "Get career advice and insights into working in data-focused roles",
    "Other…"
]

# Count options and extract "Other" responses
goal_counts, goal_other_responses = count_multiselect_matches(filtered_df[goal_col], goal_options, extract_other=True)
goal_df = pd.DataFrame(goal_counts.items(), columns=["Topic", "Count"]).sort_values("Count", ascending=True)

# Create the main bar chart
fig_goals = px.bar(
    goal_df,
    x="Count",
    y="Topic",
    orientation="h",
    title=None,
    text="Count"
)

fig_goals.update_layout(
    yaxis=dict(categoryorder='total ascending'),
    xaxis_title="Number of Students",
    yaxis_title="",
    showlegend=False,
    margin=dict(l=20, r=20, t=30, b=20)
)

# Create a gradient of colors from gold to maroon
num_bars = len(goal_df)
colors = [CMU_GOLD] * num_bars
if num_bars > 1:
    # The top bar (max value) will be maroon
    colors[-1] = CMU_MAROON

fig_goals.update_traces(
    marker_color=colors,
    textposition='outside',
    textfont=dict(color='#333333')
)

st.plotly_chart(fig_goals, use_container_width=True)

# Display "Other" responses if any
if goal_other_responses:
    st.markdown("#### Additional Learning Goals (From 'Other' Responses)")
    for i, response in enumerate(goal_other_responses):
        st.markdown(f"- {response}")

# =================== Topic Interests ===================
st.markdown("<h2>General Interests in Data Topics</h2>", unsafe_allow_html=True)

interest_col = "What topics are you most interested in? (specific subjects you are generally curious about)"
interest_options = [
    "Data Visualization principles and tools",
    "Real-world data storytelling and dashboards",
    "Handling complex or messy data in visuals (arrays, lists, nested fields)",
    "Role of visualization in business/technical decision-making",
    "AI/ML visualization and automation",
    "Careers and roles in data (analyst, engineer, scientist, architect, etc.)",
    "Other…"
]

# Count options and extract "Other" responses
interest_counts, interest_other_responses = count_multiselect_matches(
    filtered_df[interest_col], 
    interest_options,
    extract_other=True
)

interest_df = pd.DataFrame(interest_counts.items(), columns=["Topic", "Count"]).sort_values("Count", ascending=True)

# Create the main bar chart
fig_interests = px.bar(
    interest_df,
    x="Count",
    y="Topic",
    orientation="h",
    title=None,
    text="Count"
)

fig_interests.update_layout(
    yaxis=dict(categoryorder='total ascending'),
    xaxis_title="Number of Students",
    yaxis_title="",
    showlegend=False,
    margin=dict(l=20, r=20, t=30, b=20)
)

# Alternate colors between maroon and gold
num_bars = len(interest_df)
colors = [CMU_MAROON if i % 2 == 0 else CMU_GOLD for i in range(num_bars)]

fig_interests.update_traces(
    marker_color=colors,
    textposition='outside',
    textfont=dict(color='#333333')
)

st.plotly_chart(fig_interests, use_container_width=True)

# Display "Other" responses if any
if interest_other_responses:
    st.markdown("#### Additional Topics of Interest (From 'Other' Responses)")
    for i, response in enumerate(interest_other_responses):
        st.markdown(f"- {response}")

# =================== Skill Level Correlation ===================
st.markdown("<h2>Correlation Analysis</h2>", unsafe_allow_html=True)

# Check if we can correlate work experience with SQL skills
col1, col2 = st.columns(2)

with col1:
    if exp_col in filtered_df.columns and sql_col in filtered_df.columns:
        # Create a dataframe for the correlation
        corr_df = filtered_df[[exp_col, sql_col]].copy()
        
        # Convert SQL levels to numeric
        sql_level_map = {
            "No experience": 0,
            "Beginner (basic SELECT queries)": 1,
            "Intermediate (JOINs, subqueries, etc.)": 2,
            "Advanced (CTEs, window functions, optimization)": 3
        }
        
        corr_df['SQL_Level'] = corr_df[sql_col].map(sql_level_map)
        corr_df['Years_Experience'] = pd.to_numeric(corr_df[exp_col], errors='coerce')
        
        # Drop rows with missing values
        corr_df = corr_df.dropna(subset=['SQL_Level', 'Years_Experience'])
        
        # Scatter plot
        fig_corr = px.scatter(
            corr_df,
            x='Years_Experience',
            y='SQL_Level',
            title=None,
            labels={'SQL_Level': 'SQL Proficiency Level', 'Years_Experience': 'Years of Work Experience'},
            color_discrete_sequence=[CMU_MAROON],
            opacity=0.7,
            size_max=15
        )
        
        # Add custom y-axis ticks
        fig_corr.update_layout(
            yaxis=dict(
                tickmode='array',
                tickvals=[0, 1, 2, 3],
                ticktext=list(sql_level_map.keys())
            ),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        # Add trendline
        fig_corr.add_trace(
            go.Scatter(
                x=corr_df['Years_Experience'],
                y=corr_df['SQL_Level'],
                mode='lines',
                name='Trend',
                line=dict(color=CMU_GOLD, width=2, dash='dot'),
                visible="legendonly"
            )
        )
        
        fig_corr.add_annotation(
            text="Work Experience vs. SQL Proficiency",
            showarrow=False,
            font=dict(size=14, color=CMU_MAROON),
            xref="paper",
            yref="paper",
            x=0.5,
            y=1.05
        )
        
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.info("Cannot create correlation plot: Required columns not found in dataset")

with col2:
    if prog_col in filtered_df.columns and sql_col in filtered_df.columns:
        # Create a heatmap of program vs SQL level
        prog_sql_cross = pd.crosstab(
            filtered_df[prog_col], 
            filtered_df[sql_col]
        )
        
        # Reorder columns to match SQL levels progression
        if all(level in prog_sql_cross.columns for level in sql_levels):
            prog_sql_cross = prog_sql_cross[sql_levels]
        
        # Create heatmap with CMU colors
        colorscale = [[0, '#ffb400'], [0.5, '#b07f19'], [1, '#6a0032']]
        
        # Create heatmap
        fig_heatmap = px.imshow(
            prog_sql_cross,
            labels=dict(x="SQL Proficiency", y="Program", color="Count"),
            x=prog_sql_cross.columns,
            y=prog_sql_cross.index,
            color_continuous_scale=colorscale,
            title=None
        )
        
        fig_heatmap.update_layout(
            xaxis_tickangle=-45,
            margin=dict(l=20, r=20, t=30, b=80)
        )
        
        # Add text annotations
        annotations = []
        for i, row in enumerate(prog_sql_cross.index):
            for j, col in enumerate(prog_sql_cross.columns):
                annotations.append(
                    dict(
                        x=col,
                        y=row,
                        text=str(prog_sql_cross.iloc[i, j]),
                        showarrow=False,
                        font=dict(color="white" if prog_sql_cross.iloc[i, j] > prog_sql_cross.values.mean() else "black")
                    )
                )
        
        fig_heatmap.update_layout(annotations=annotations)
        
        fig_heatmap.add_annotation(
            text="SQL Proficiency by Program",
            showarrow=False,
            font=dict(size=14, color=CMU_MAROON),
            xref="paper",
            yref="paper",
            x=0.5,
            y=1.05
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)
    else:
        st.info("Cannot create heatmap: Required columns not found in dataset")



# =================== Clustering of Students by Interest ===================
st.markdown("<h2>Clustering Students by Topic Interests</h2>", unsafe_allow_html=True)

try:
    from sklearn.manifold import TSNE
    from sklearn.preprocessing import MultiLabelBinarizer

    mlb = MultiLabelBinarizer()
    filtered_df['Interest List'] = filtered_df[interest_col].apply(
        lambda x: [i.strip() for i in str(x).split(',')] if pd.notnull(x) else []
    )
    interest_binary = mlb.fit_transform(filtered_df['Interest List'])
    n_samples = interest_binary.shape[0]
    perplexity = min(30, max(2, n_samples // 3))

    if n_samples >= 5:
        tsne = TSNE(n_components=2, random_state=42, perplexity=perplexity)
        tsne_results = tsne.fit_transform(interest_binary)

        tsne_df = pd.DataFrame(tsne_results, columns=["TSNE-1", "TSNE-2"])
        tsne_df[prog_col] = filtered_df[prog_col].values

        fig_cluster = px.scatter(
            tsne_df, x="TSNE-1", y="TSNE-2", color=prog_col,
            title=None,
            labels={"color": "Program of Study"},
            opacity=0.9,
            symbol=prog_col,
            color_discrete_sequence=[CMU_MAROON, CMU_GOLD, CMU_MAROON_LIGHT, CMU_GOLD_LIGHT, CMU_MAROON_DARK, CMU_GOLD_DARK]
        )
        fig_cluster.update_traces(marker=dict(size=12, line=dict(width=1, color='white')))
        fig_cluster.update_layout(
            margin=dict(l=40, r=40, t=30, b=40),
            plot_bgcolor='#ffffff',
            paper_bgcolor='#ffffff',
            legend=dict(
                title_font=dict(size=14),
                font=dict(size=12)
            )
        )
        
        fig_cluster.add_annotation(
            text="Student Clusters Based on Topic Interests",
            showarrow=False,
            font=dict(size=14, color=CMU_MAROON),
            xref="paper",
            yref="paper",
            x=0.5,
            y=1.05
        )
        
        st.plotly_chart(fig_cluster, use_container_width=True)
    else:
        st.info("Not enough data to generate meaningful clusters. At least 5 responses required.")
except Exception as e:
    st.error(f"Error generating clustering: {str(e)}")

# =================== Presentation Recommendation ===================
st.markdown("<h2>Presentation Recommendation</h2>", unsafe_allow_html=True)

sql_col = "How would you rate your experience with SQL/MySQL?"
exp_col = "Do you have any work experience?"

sql_levels = [
    "No experience",
    "Beginner (basic SELECT queries)",
    "Intermediate (JOINs, subqueries, etc.)",
    "Advanced (CTEs, window functions, optimization)"
]

try:
    sql_counts = filtered_df[sql_col].value_counts().reindex(sql_levels, fill_value=0)
    sql_props = sql_counts / sql_counts.sum()

    exp_vals = pd.to_numeric(filtered_df[exp_col], errors='coerce').dropna()
    avg_exp = exp_vals.mean()

    sql_numeric_map = {
        "No experience": 0,
        "Beginner (basic SELECT queries)": 1,
        "Intermediate (JOINs, subqueries, etc.)": 2,
        "Advanced (CTEs, window functions, optimization)": 3
    }

    filtered_df["SQL Numeric"] = filtered_df[sql_col].map(sql_numeric_map)
    filtered_df["Experience Numeric"] = pd.to_numeric(filtered_df[exp_col], errors='coerce')
    filtered_df["Tech Score"] = (filtered_df["SQL Numeric"] + filtered_df["Experience Numeric"]) / 2
    avg_tech_score = filtered_df["Tech Score"].mean()

    if avg_tech_score < 1.5:
        recommendation = "Keep it simple and focus on fundamentals with real-world examples."
        rec_color = CMU_GOLD
    elif 1.5 <= avg_tech_score < 2.5:
        recommendation = "Use a balanced approach: start with basics, layer in complexity."
        rec_color = CMU_GOLD_DARK
    else:
        recommendation = "Lean into advanced content and optimization techniques."
        rec_color = CMU_MAROON

    st.markdown(f"""
    <div style='background-color: {rec_color}20; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1.5rem;'>
        <h3 style='color: {rec_color}; margin-top: 0; font-size: 1.5rem;'>Guidance: {recommendation}</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Why this recommendation?")
    
    reasoning_points = []
    if sql_props["No experience"] + sql_props["Beginner (basic SELECT queries)"] > 0.6:
        reasoning_points.append("- More than 60% of students rated themselves as having beginner or no SQL experience.")
    if sql_props["Intermediate (JOINs, subqueries, etc.)"] > 0.5:
        reasoning_points.append("- Over half the audience has intermediate SQL skills.")
    if sql_props["Advanced (CTEs, window functions, optimization)"] > 0.3:
        reasoning_points.append("- A significant portion (>30%) of students reported advanced SQL proficiency.")
    if avg_exp < 2:
        reasoning_points.append("- The average work experience is less than 2 years, suggesting limited exposure.")
    if avg_exp >= 2 and avg_exp < 3:
        reasoning_points.append("- The audience has some industry experience (2-3 years).")
    if avg_exp >= 3:
        reasoning_points.append("- The audience is relatively experienced (3+ years).")

    reasoning_points.append(f"- Total responses analyzed: {len(filtered_df)}")
    reasoning_points.append(f"- Average experience: {avg_exp:.1f} years")
    reasoning_points.append(f"- Average technical score (experience + SQL level): {avg_tech_score:.2f}")
    reasoning_points.append(f"- Skill diversity suggests varying levels of technical depth expected")
    reasoning_points.append(f"- A mixed distribution in SQL levels indicates need for adaptive content")

    for point in reasoning_points:
        st.markdown(point)

    col1, col2 = st.columns(2)

    with col1:
        fig_sql = px.bar(
            x=sql_counts.index,
            y=sql_counts.values,
            title=None,
            labels={"x": "SQL Level", "y": "Number of Students"},
            text=sql_counts.values,
        )
        fig_sql.update_layout(
            xaxis_tickangle=-30, 
            margin=dict(t=30, b=40),
            plot_bgcolor='#ffffff'
        )
        
        # Set custom colors for each bar
        fig_sql.update_traces(
            marker_color=[CMU_GOLD_LIGHT, CMU_GOLD, CMU_MAROON_LIGHT, CMU_MAROON],
            textposition='outside',
            textfont=dict(color='#333333')
        )
        
        fig_sql.add_annotation(
            text="SQL Skill Levels",
            showarrow=False,
            font=dict(size=14, color=CMU_MAROON),
            xref="paper",
            yref="paper",
            x=0.5,
            y=1.05
        )
        
        st.plotly_chart(fig_sql, use_container_width=True)

    with col2:
        bins = [0, 1, 3, 5, 10, 20]
        labels = ['< 1 year', '1-3 years', '3-5 years', '5-10 years', '10+ years']
        exp_binned = pd.cut(exp_vals, bins=bins, labels=labels)
        exp_dist = exp_binned.value_counts().sort_index()

        fig_exp = px.bar(
            x=exp_dist.index,
            y=exp_dist.values,
            title=None,
            labels={"x": "Experience Range", "y": "Count"},
            text=exp_dist.values,
        )
        fig_exp.update_layout(
            margin=dict(t=30, b=60),
            plot_bgcolor='#ffffff'
        )
        
        # Gradient colors from gold to maroon
        num_bars = len(exp_dist)
        colors = [CMU_GOLD, CMU_GOLD_LIGHT, CMU_MAROON_LIGHT, CMU_MAROON, CMU_MAROON_DARK][:num_bars]
        
        fig_exp.update_traces(
            marker_color=colors,
            textposition='outside',
            textfont=dict(color='#333333')
        )
        
        fig_exp.add_annotation(
            text="Audience Work Experience",
            showarrow=False,
            font=dict(size=14, color=CMU_MAROON),
            xref="paper",
            yref="paper",
            x=0.5,
            y=1.05
        )
        
        st.plotly_chart(fig_exp, use_container_width=True)
except Exception as e:
    st.error(f"Error generating recommendations: {str(e)}")

# =================== Footer ===================
st.markdown(f"""
<div style='margin-top: 3rem; padding-top: 1rem; text-align: center; color: #666666; font-size: 0.9rem;'>
    Central Michigan University Data Visualization Workshop | {datetime.now().strftime('%Y')}
</div>
""", unsafe_allow_html=True)