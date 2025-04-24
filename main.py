import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, date, timedelta

# --- Page Configuration with improved appearance ---
st.set_page_config(
    page_title="HP Printer Analytics Dashboard",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to improve the look and feel
st.markdown("""
<style>
    /* Main content area styling */
    .main {
        background-color: #f9f9f9;
    }
    
    /* Header styling */
    .main .block-container h1 {
        color: #0066cc;
        padding-bottom: 1rem;
        border-bottom: 1px solid #e0e0e0;
    }
    
    /* Subheader styling */
    .main .block-container h2 {
        color: #333333;
        padding-top: 1rem;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
    }
    
    /* Metric containers */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border-radius: 5px;
        padding: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 0.5rem;
    }
    
    /* Metric label */
    div[data-testid="metric-container"] label {
        color: #555555;
    }
    
    /* Metric value */
    div[data-testid="metric-container"] div {
        color: #0066cc;
    }
    
    /* Divider styling */
    hr {
        margin: 1.5rem 0;
        border-color: #e0e0e0;
    }
    
    /* Chart container */
    div[data-testid="stPlotlyChart"] {
        background-color: white;
        border-radius: 5px;
        padding: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- Configuration & Data Loading ---
# Assumes the CSV files are in a subdirectory named 'hp_printer_data_csv_daily_nested'
DATA_DIR = "sample_data"
PRINTERS_PATH = os.path.join(DATA_DIR, "printers.csv")
USAGE_PATH = os.path.join(DATA_DIR, "daily_usage.csv")
ERRORS_PATH = os.path.join(DATA_DIR, "printer_errors.csv")
REVENUE_PATH = os.path.join(DATA_DIR, "revenue_share.csv")

# --- Cache Data Loading ---
# Use st.cache_data to avoid reloading data on every interaction
@st.cache_data
def load_data():
    """Loads and preprocesses all required data."""
    print("Loading data...")
    try:
        printers_df = pd.read_csv(PRINTERS_PATH)
        usage_df = pd.read_csv(USAGE_PATH, parse_dates=['usage_date'])
        # Handle potential parsing errors for error_timestamp
        try:
            errors_df = pd.read_csv(ERRORS_PATH, parse_dates=['error_timestamp'])
        except (ValueError, TypeError) as e:
            print(f"Warning: Could not parse 'error_timestamp' as dates directly. Attempting manual parsing. Error: {e}")
            errors_df = pd.read_csv(ERRORS_PATH)
            errors_df['error_timestamp'] = pd.to_datetime(errors_df['error_timestamp'], errors='coerce')

        revenue_df = pd.read_csv(REVENUE_PATH)
        print("Data loaded successfully.")

        # --- Data Preprocessing & Merging ---
        print("Preprocessing data...")
        # Merge usage data with printer details
        df = pd.merge(usage_df, printers_df, on='printer_id', how='left')

        # Merge error data with printer details
        errors_merged_df = pd.DataFrame() # Initialize empty
        if not errors_df.empty and 'printer_id' in errors_df.columns and 'error_timestamp' in errors_df.columns:
             # Drop rows where error_timestamp couldn't be parsed
             errors_df.dropna(subset=['error_timestamp'], inplace=True)
             errors_merged_df = pd.merge(errors_df, printers_df[['printer_id', 'model', 'customer_segment', 'region']], on='printer_id', how='left')
             errors_merged_df['error_date'] = errors_merged_df['error_timestamp'].dt.date
        else:
             print("Warning: Errors data is empty, missing columns, or has parsing issues. Error analysis will be limited.")
             errors_merged_df = pd.DataFrame(columns=['printer_id', 'error_timestamp', 'error_code', 'error_severity', 'model', 'customer_segment', 'region', 'error_date'])

        # Convert boolean column
        if 'low_ink_event_occurred' in df.columns:
            if df['low_ink_event_occurred'].dtype == 'object':
                 df['low_ink_event_occurred'] = df['low_ink_event_occurred'].astype(str).str.lower().map({'true': True, 'false': False, 'nan': False}).fillna(False)
            df['low_ink_event_occurred'] = df['low_ink_event_occurred'].astype(bool)
        else:
            print("Warning: 'low_ink_event_occurred' column not found.")
            df['low_ink_event_occurred'] = False

        # Count probes from string list
        def count_probes(probes_str):
            # Handle potential NaN values before string checks
            if pd.isna(probes_str):
                return 0
            if isinstance(probes_str, str) and probes_str.startswith('[') and probes_str.endswith(']'):
                 if len(probes_str) > 2: return probes_str.count(',') + 1
                 else: return 0
            return 0 # Return 0 if not a string list representation or NaN
        if 'daily_connectivity_probes' in df.columns:
            df['num_probes'] = df['daily_connectivity_probes'].apply(count_probes)
        else:
            print("Warning: 'daily_connectivity_probes' column not found.")
            df['num_probes'] = 0

        print("Preprocessing finished.")
        return df, errors_merged_df, revenue_df

    except FileNotFoundError:
        st.error(f"Error: Data files not found in directory '{DATA_DIR}'. Please ensure the CSV files are present.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        st.error(f"An error occurred during data loading or preprocessing: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Load data using the cached function
df, errors_merged_df, revenue_df = load_data()

# --- Dashboard Header with Logo ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    # Replace with your own logo or use a placeholder
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/HP_New_Logo_2D.svg/200px-HP_New_Logo_2D.svg.png", width=80)
with col_title:
    st.title("HP Printer Analytics Dashboard")
    st.markdown("*Comprehensive insights into printer usage, performance, and business impact*")

# Define a helper function to safely convert to string for sorting/display
def safe_str(val):
    if pd.isna(val):
        return "Unknown" # Or handle NaN as you prefer
    return str(val)

# --- Sidebar with improved styling ---
st.sidebar.markdown("""
<div style="text-align: center">
    <h2 style="color: #0066cc;">📊 Dashboard Controls</h2>
</div>
""", unsafe_allow_html=True)

# Check if dataframe is loaded before creating filters
if not df.empty:
    min_date = df['usage_date'].min().date()
    max_date = df['usage_date'].max().date()
    # Ensure default_start_date is not before min_date
    default_start_date = max(min_date, max_date - timedelta(days=90))

    # Date Range Selector with better styling
    st.sidebar.markdown("### 📅 Time Period")
    selected_date_range = st.sidebar.date_input(
        "Select Date Range:",
        value=(default_start_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key='date_picker' # Unique key needed
    )
    # Ensure we have two dates selected
    if len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
    else: # Handle case where only one date might be selected initially
        start_date = default_start_date
        end_date = max_date

    # Region Selector with visual enhancement
    st.sidebar.markdown("### 🌎 Geography")
    # Convert all unique regions to string before sorting to handle mixed types
    all_regions = sorted([safe_str(r) for r in df['region'].unique()])
    selected_regions = st.sidebar.multiselect(
        "Select Region(s):",
        options=all_regions,
        default=all_regions # Default to all selected
    )

    # Customer Segment Selector with visual enhancement
    st.sidebar.markdown("### 👥 Customer Segment")
    # Apply similar fix for safety, although less likely to be mixed type here
    all_segments = sorted([safe_str(s) for s in df['customer_segment'].unique()])
    selected_segments = st.sidebar.multiselect(
        "Select Customer Segment(s):",
        options=all_segments,
        default=all_segments
    )

    # Printer Model Selector with visual enhancement
    st.sidebar.markdown("### 🖨️ Printer Models")
    # Apply similar fix for safety
    all_models = sorted([safe_str(m) for m in df['model'].unique()])
    selected_models = st.sidebar.multiselect(
        "Select Printer Model(s):",
        options=all_models,
        default=all_models
    )

    # Add information about dashboard
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div style="background-color: #f0f8ff; padding: 10px; border-radius: 5px; border-left: 3px solid #0066cc;">
        <p style="margin: 0; font-size: 0.9em">This dashboard analyzes printer usage patterns, consumable consumption, and performance metrics across your printer fleet.</p>
    </div>
    """, unsafe_allow_html=True)

else:
    st.sidebar.warning("Data not loaded. Filters unavailable.")
    # Assign default empty values if data loading failed
    start_date, end_date = date.today(), date.today()
    selected_regions, selected_segments, selected_models = [], [], []

# --- Data Filtering based on Sidebar ---
# Perform filtering only if data and selections are valid
if not df.empty and selected_regions and selected_segments and selected_models and start_date and end_date:
    # Convert columns to string for consistent filtering against string lists from multiselect
    filtered_df = df[
        (df['usage_date'].dt.date >= start_date) &
        (df['usage_date'].dt.date <= end_date) &
        (df['region'].apply(safe_str).isin(selected_regions)) &
        (df['customer_segment'].apply(safe_str).isin(selected_segments)) &
        (df['model'].apply(safe_str).isin(selected_models))
    ].copy()

    # Apply similar logic for errors_merged_df if it's not empty
    if not errors_merged_df.empty:
        filtered_errors_df = errors_merged_df[
            (errors_merged_df['error_date'] >= start_date) &
            (errors_merged_df['error_date'] <= end_date) &
            (errors_merged_df['region'].apply(safe_str).isin(selected_regions)) &
            (errors_merged_df['customer_segment'].apply(safe_str).isin(selected_segments)) &
            (errors_merged_df['model'].apply(safe_str).isin(selected_models))
        ].copy()
    else:
        filtered_errors_df = pd.DataFrame()

else:
    filtered_df = pd.DataFrame() # Create empty if filtering is not possible
    filtered_errors_df = pd.DataFrame()

# --- Main Dashboard Layout ---

# Display warning if no data matches filters
if filtered_df.empty and not df.empty: # Check if original df was loaded but filter resulted in empty
    st.warning("No data matches the selected filter criteria. Please adjust your selections.")

# Proceed only if there's data after filtering
elif not filtered_df.empty:

    # --- Section A: Overall Usage Trends & KPIs ---
    st.header("📈 Overall Usage Trends & KPIs")
    
    # Enhanced KPIs with better visual display
    kpi_cols = st.columns(5)
    
    total_pages = filtered_df['total_pages'].sum()
    active_printers = filtered_df['printer_id'].nunique()
    # Ensure time_delta_days is at least 0 for calculation
    time_delta_days = (end_date - start_date).days
    days_in_range = max(0, time_delta_days) + 1
    avg_daily_pages = (total_pages / active_printers / days_in_range) if active_printers > 0 else 0
    low_ink_events = filtered_df['low_ink_event_occurred'].sum()
    avg_probes = filtered_df['num_probes'].mean() if not filtered_df.empty else 0
    
    with kpi_cols[0]:
        st.metric(label="📄 Total Pages", value=f"{total_pages:,.0f}")
    with kpi_cols[1]:
        st.metric(label="🖨️ Active Printers", value=f"{active_printers:,.0f}")
    with kpi_cols[2]:
        st.metric(label="📊 Avg Pages/Printer/Day", value=f"{avg_daily_pages:.1f}")
    with kpi_cols[3]:
        st.metric(label="🔴 Low Ink Events", value=f"{low_ink_events:,.0f}")
    with kpi_cols[4]:
        st.metric(label="📡 Avg Daily Probes", value=f"{avg_probes:.1f}")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Determine the appropriate time grouping based on selected date range
    time_delta_days = (end_date - start_date).days
    if time_delta_days <= 90: agg_freq, title_freq = 'D', 'Daily'
    elif time_delta_days <= 365: agg_freq, title_freq = 'W-Mon', 'Weekly'
    else: agg_freq, title_freq = 'ME', 'Monthly'
    
    # Usage Trend Chart with enhanced styling
    st.subheader("Print Volume Trend by Segment")
    # Ensure customer_segment is treated as string for grouping consistency
    usage_trend_data = filtered_df.set_index('usage_date').groupby(
        [pd.Grouper(freq=agg_freq), filtered_df['customer_segment'].apply(safe_str)]
    )['total_pages'].sum().reset_index()
    usage_trend_data = usage_trend_data.rename(columns={'usage_date': 'Time Period'}) # Rename for clarity

    fig_usage_trend = px.line(usage_trend_data, x='Time Period', y='total_pages', color='customer_segment',
                             title=f'{title_freq} Print Volume by Segment', markers=True if agg_freq == 'D' else False)
    fig_usage_trend.update_layout(
        hovermode="x unified",
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend_title_text='Customer Segment',
        xaxis_title="Date",
        yaxis_title="Total Pages Printed",
        font=dict(family="Arial, sans-serif", size=12),
        margin=dict(l=10, r=10, t=40, b=10),
        height=450
    )
    fig_usage_trend.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='#eeeeee')
    fig_usage_trend.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='#eeeeee')
    st.plotly_chart(fig_usage_trend, use_container_width=True)

    st.divider() # Visual separator

    # --- Section B: Printer Model Deep Dive ---
    st.header("🔍 Printer Model Analysis")
    colB1, colB2 = st.columns([2, 1]) # Ratio 2:1

    with colB1:
        # Top 10 Models Bar Chart with enhanced styling
        st.subheader("Top 10 Models by Print Volume")
        # Ensure model is treated as string for grouping consistency
        top_models_data = filtered_df.groupby(filtered_df['model'].apply(safe_str))['total_pages'].sum().reset_index()
        top_models_data = top_models_data.sort_values('total_pages', ascending=False).head(10)
        fig_top_models = px.bar(top_models_data, x='total_pages', y='model', orientation='h')
        fig_top_models.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis_title="Total Pages Printed",
            yaxis_title="Printer Model",
            yaxis={'categoryorder':'total ascending'},
            font=dict(family="Arial, sans-serif", size=12),
            margin=dict(l=10, r=10, t=40, b=10),
            height=400
        )
        fig_top_models.update_traces(marker_color='#0066cc')
        fig_top_models.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='#eeeeee')
        st.plotly_chart(fig_top_models, use_container_width=True)

    with colB2:
        # Market Share Donut Chart with enhanced styling
        st.subheader("Market Share by Model (Units)")
        if not revenue_df.empty:
            # Ensure model_line is string for plotting consistency
            revenue_df['model_line'] = revenue_df['model_line'].apply(safe_str)
            fig_market_share = px.pie(revenue_df, names='model_line', values='market_share_percent', hole=0.4)
            fig_market_share.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family="Arial, sans-serif", size=12),
                margin=dict(l=10, r=10, t=40, b=10),
                height=400,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.3,
                    xanchor="center",
                    x=0.5
                )
            )
            st.plotly_chart(fig_market_share, use_container_width=True)
        else:
            st.info("Revenue/Market share data not available.", icon="ℹ️")

    st.divider()

    # --- Section C: Consumables & Printer Health ---
    st.header("🧰 Consumables & Printer Health")
    colC1, colC2 = st.columns(2)

    with colC1:
        # Ink Consumption Stacked Bar with enhanced styling
        st.subheader("Ink Consumption by Type & Model (Top 15)")
        # Ensure model is treated as string for grouping consistency
        ink_data = filtered_df.groupby(filtered_df['model'].apply(safe_str))[['ink_consumed_mono_units', 'ink_consumed_color_units']].sum().reset_index()
        ink_data['total_ink'] = ink_data['ink_consumed_mono_units'] + ink_data['ink_consumed_color_units']
        ink_data = ink_data.sort_values('total_ink', ascending=False).head(15)
        ink_data_melted = pd.melt(ink_data, id_vars=['model'], value_vars=['ink_consumed_mono_units', 'ink_consumed_color_units'],
                                 var_name='ink_type', value_name='units_consumed')
        ink_data_melted['ink_type'] = ink_data_melted['ink_type'].replace({'ink_consumed_mono_units': 'Monochrome', 'ink_consumed_color_units': 'Color'})
        fig_ink_consumption = px.bar(ink_data_melted, y='model', x='units_consumed', color='ink_type', orientation='h', barmode='stack',
                                    color_discrete_map={'Monochrome': '#333333', 'Color': '#4caf50'})
        fig_ink_consumption.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            yaxis={'categoryorder':'total ascending'},
            xaxis_title="Ink Units Consumed",
            yaxis_title="Printer Model",
            legend_title_text='Ink Type',
            font=dict(family="Arial, sans-serif", size=12),
            margin=dict(l=10, r=10, t=40, b=10),
            height=500
        )
        fig_ink_consumption.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='#eeeeee')
        st.plotly_chart(fig_ink_consumption, use_container_width=True)

    with colC2:
        # Error Frequency Bar Chart with enhanced styling
        st.subheader("Top Printer Errors by Frequency")
        if not filtered_errors_df.empty and 'error_code' in filtered_errors_df.columns: # Check column exists
            # Ensure error_code is treated as string before value_counts
            error_counts = filtered_errors_df['error_code'].apply(safe_str).value_counts().reset_index()
            error_counts.columns = ['error_code', 'count']
            error_counts = error_counts.sort_values('count', ascending=False).head(15)
            fig_error_freq = px.bar(error_counts, x='error_code', y='count')
            fig_error_freq.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis={'categoryorder':'total descending', 'title': 'Error Code'},
                yaxis_title="Error Count",
                font=dict(family="Arial, sans-serif", size=12),
                margin=dict(l=10, r=10, t=40, b=10),
                height=500
            )
            fig_error_freq.update_traces(marker_color='#FF5252')
            fig_error_freq.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='#eeeeee')
            st.plotly_chart(fig_error_freq, use_container_width=True)
        else:
            st.info("No error data available for the selected filters.", icon="ℹ️")

    st.divider()

    # --- Section D: Business & Customer View ---
    st.header("💼 Business & Customer Insights")
    colD1, colD2, colD3 = st.columns(3)

    with colD1:
        # Regional Usage Treemap with enhanced styling
        st.subheader("Usage Distribution by Region")
        # Ensure region is treated as string for grouping consistency
        regional_data = filtered_df.groupby(filtered_df['region'].apply(safe_str))['total_pages'].sum().reset_index()
        fig_regional_usage = px.treemap(regional_data, path=['region'], values='total_pages',
                                      color='total_pages', color_continuous_scale='Blues')
        fig_regional_usage.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial, sans-serif", size=12),
            margin=dict(t=30, l=10, r=10, b=10),
            height=400
        )
        st.plotly_chart(fig_regional_usage, use_container_width=True)

    with colD2:
        # Active Printer Trend Line Chart with enhanced styling
        st.subheader("Active Printers Over Time")
        active_printer_trend_data = filtered_df.set_index('usage_date').groupby(pd.Grouper(freq=agg_freq))['printer_id'].nunique().reset_index()
        active_printer_trend_data = active_printer_trend_data.rename(columns={'usage_date': 'Time Period'})
        fig_active_printers = px.line(active_printer_trend_data, x='Time Period', y='printer_id',
                                     markers=True if agg_freq == 'D' else False)
        fig_active_printers.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis_title="Date",
            yaxis_title="Unique Printers",
            font=dict(family="Arial, sans-serif", size=12),
            margin=dict(t=30, l=10, r=10, b=10),
            height=400
        )
        fig_active_printers.update_traces(line_color='#4caf50')
        fig_active_printers.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='#eeeeee')
        fig_active_printers.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='#eeeeee')
        st.plotly_chart(fig_active_printers, use_container_width=True)

    with colD3:
        # Revenue Contribution Bar Chart with enhanced styling
        st.subheader("Estimated Revenue Contribution %")
        if not revenue_df.empty:
            # Ensure model_line is string for plotting consistency
            revenue_df['model_line'] = revenue_df['model_line'].apply(safe_str)
            revenue_sorted = revenue_df.sort_values('revenue_contribution_percent', ascending=False)
            fig_revenue = px.bar(revenue_sorted, y='model_line', x='revenue_contribution_percent', orientation='h')
            fig_revenue.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis_title="Contribution (%)",
                yaxis_title="Model Line",
                yaxis={'categoryorder':'total ascending'},
                font=dict(family="Arial, sans-serif", size=12),
                margin=dict(t=30, l=10, r=10, b=10),
                height=400
            )
            fig_revenue.update_traces(marker_color='#673ab7')
            fig_revenue.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='#eeeeee')
            st.plotly_chart(fig_revenue, use_container_width=True)
        else:
            st.info("Revenue/Market share data not available.", icon="ℹ️")

    st.divider()

    # --- Section E: Nested Data Example with enhanced styling ---
    st.header("💧 Ink Level Analysis")
    st.subheader("Distribution of Minimum Daily Ink Levels (%)")
    st.markdown("""
    <div style="background-color: #f9f9f9; padding: 10px; border-radius: 5px; border-left: 3px solid #0066cc; margin-bottom: 20px;">
        <p style="margin: 0; font-size: 0.9em">This chart shows the distribution of the minimum reported ink level per printer per day, parsed from the nested 'ink_levels_snapshot' column.</p>
    </div>
    """, unsafe_allow_html=True)

    min_ink_levels = []
    if 'ink_levels_snapshot' in filtered_df.columns:
        # Use .dropna() to avoid errors on NaN values before trying json.loads
        for snapshot_json in filtered_df['ink_levels_snapshot'].dropna():
            try:
                # Ensure it's treated as a string before loading
                ink_list = json.loads(str(snapshot_json))
                if ink_list: # Check if list is not empty after loading
                    # Safely get level_percent, default to None if key missing or item not dict
                    levels = [item.get('level_percent') for item in ink_list if isinstance(item, dict)]
                    # Filter out None values before finding min
                    valid_levels = [lvl for lvl in levels if lvl is not None]
                    if valid_levels:
                        min_ink_levels.append(min(valid_levels))
            except (json.JSONDecodeError, TypeError) as e:
                # Optionally log the error or the problematic value:
                # print(f"Could not parse ink snapshot: {snapshot_json}, Error: {e}")
                continue # Skip if JSON is invalid or not a string/dict structure

    if min_ink_levels:
        ink_level_df = pd.DataFrame({'min_ink_level': min_ink_levels})
        fig_ink_histogram = px.histogram(ink_level_df, x='min_ink_level', nbins=20)
        fig_ink_histogram.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis_title="Minimum Ink Level Reported (%)",
            yaxis_title="Frequency (Printer-Days)",
            font=dict(family="Arial, sans-serif", size=12),
            margin=dict(l=10, r=10, t=40, b=10),
            height=400
        )
        fig_ink_histogram.update_traces(marker_color='#5c6bc0')
        fig_ink_histogram.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='#eeeeee')
        fig_ink_histogram.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='#eeeeee')
        st.plotly_chart(fig_ink_histogram, use_container_width=True)
    else:
        st.info("No valid ink level snapshot data found for the selected filters.", icon="ℹ️")
        
    # Footer with data timestamp
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #888888; font-size: 0.8em;">
        <p>Dashboard last updated: {datetime.now().strftime('%B %d, %Y %H:%M')} | Data range: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}</p>
        <p>HP Printer Analytics Platform | © {datetime.now().year} Hewlett-Packard Enterprise</p>
    </div>
    """, unsafe_allow_html=True)