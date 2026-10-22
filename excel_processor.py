import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from config import default_dates
from helpers import build_test_counts, build_category_counts, style_excel
from data_persistence import save_processed_data, load_processed_data, delete_processed_data, get_saved_dates, compute_cumulative

st.set_page_config(page_title="Pathology Report", page_icon="🧪", layout="wide")

# ============================================================================
# BLACK & WHITE MODERN GLOSSY CSS STYLING
# ============================================================================
st.markdown("""
<style>
* {
    margin: 0;
    padding: 0;
}

html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
    min-height: 100vh;
}

[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a1a 0%, #2d2d2d 100%);
    border-right: 2px solid #333;
}

.main {
    background: transparent;
}

.block-container {
    padding: 2rem 1rem;
    max-width: 1400px;
}

/* Card Styling */
.glossy-card {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 25px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    margin-bottom: 20px;
    transition: transform 0.3s ease, box-shadow 0.3s ease, border 0.3s ease;
}

.glossy-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 40px rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Upload Section */
.upload-container {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 30px;
    padding: 80px 40px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(10px);
    border: 2px solid rgba(255, 255, 255, 0.1);
    text-align: center;
    margin: 40px 0;
    transition: all 0.3s ease;
}

.upload-container:hover {
    background: rgba(255, 255, 255, 0.08);
    box-shadow: 0 25px 70px rgba(255, 255, 255, 0.05);
    border: 2px solid rgba(255, 255, 255, 0.15);
}

.upload-icon {
    font-size: 5em;
    margin-bottom: 20px;
    animation: float 3s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-20px); }
}

.upload-title {
    color: #ffffff;
    font-size: 2.5em;
    font-weight: 700;
    margin-bottom: 10px;
}

.upload-subtitle {
    color: rgba(255, 255, 255, 0.7);
    font-size: 1.1em;
    margin-bottom: 30px;
}

/* Header Styling */
.header-title {
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    color: white;
    padding: 50px;
    border-radius: 25px;
    text-align: center;
    margin-bottom: 30px;
    box-shadow: 0 15px 50px rgba(0, 0, 0, 0.4);
    border: 2px solid rgba(255, 255, 255, 0.1);
}

.header-title h1 {
    font-size: 3.5em;
    font-weight: 800;
    margin-bottom: 10px;
    background: linear-gradient(135deg, #ffffff 0%, #c0c0c0 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.header-title p {
    font-size: 1.2em;
    opacity: 0.85;
    color: rgba(255, 255, 255, 0.8);
}

/* Metric Cards */
[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.08);
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
}

[data-testid="stMetricValue"] {
    color: #ffffff;
    font-size: 2.5em !important;
    font-weight: 800;
}

[data-testid="stMetricLabel"] {
    color: rgba(255, 255, 255, 0.7) !important;
}

/* Button Styling */
.stButton > button {
    background: linear-gradient(135deg, #ffffff 0%, #e8e8e8 100%);
    color: #1a1a1a;
    border: none;
    border-radius: 12px;
    padding: 12px 30px;
    font-weight: 700;
    font-size: 1em;
    box-shadow: 0 4px 15px rgba(255, 255, 255, 0.2);
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 25px rgba(255, 255, 255, 0.3);
    background: linear-gradient(135deg, #f0f0f0 0%, #d0d0d0 100%);
}

/* Upload Button */
.stFileUploader > button {
    background: linear-gradient(135deg, #ffffff 0%, #e8e8e8 100%) !important;
    color: #1a1a1a !important;
    font-weight: 700 !important;
}

/* Tab Styling */
[data-testid="stTabs"] [role="tablist"] {
    background: transparent;
    border: none;
    border-bottom: 2px solid rgba(255, 255, 255, 0.1);
}

[data-testid="stTabs"] [role="tab"] {
    background: transparent;
    color: rgba(255, 255, 255, 0.6);
    border: none;
    padding: 12px 20px;
    font-weight: 600;
    border-bottom: 3px solid transparent;
    transition: all 0.3s ease;
}

[data-testid="stTabs"] [role="tab"]:hover {
    color: rgba(255, 255, 255, 0.9);
}

[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: transparent;
    color: white;
    border-bottom: 3px solid #ffffff;
}

/* Selectbox Styling */
[data-testid="stSelectbox"] {
    border-radius: 12px;
}

.stSelectbox {
    margin-bottom: 20px;
}

/* Section Header */
.section-header {
    font-size: 1.8em;
    font-weight: 700;
    color: #ffffff;
    margin: 30px 0 20px 0;
    padding-bottom: 10px;
    border-bottom: 3px solid rgba(255, 255, 255, 0.2);
}

/* Table Styling */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.05);
}

/* Download Button */
.stDownloadButton > button {
    background: linear-gradient(135deg, #ffffff 0%, #e8e8e8 100%);
    color: #1a1a1a;
    font-weight: 700;
}

.stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(255, 255, 255, 0.3);
}

/* Success/Error Messages */
.stSuccess {
    background: rgba(76, 175, 80, 0.15);
    border-left: 5px solid #4CAF50;
    border-radius: 8px;
    color: rgba(255, 255, 255, 0.9);
}

.stError {
    background: rgba(244, 67, 54, 0.15);
    border-left: 5px solid #f44336;
    border-radius: 8px;
    color: rgba(255, 255, 255, 0.9);
}

.stInfo {
    background: rgba(33, 150, 243, 0.15);
    border-left: 5px solid #2196F3;
    border-radius: 8px;
    color: rgba(255, 255, 255, 0.9);
}

.stWarning {
    background: rgba(255, 152, 0, 0.15);
    border-left: 5px solid #FF9800;
    border-radius: 8px;
    color: rgba(255, 255, 255, 0.9);
}

/* Divider */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    margin: 30px 0;
}

/* Text Colors */
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
}

p, span, label {
    color: rgba(255, 255, 255, 0.85) !important;
}

/* Input Fields */
input {
    background: rgba(255, 255, 255, 0.08) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
}

input::placeholder {
    color: rgba(255, 255, 255, 0.4) !important;
}

/* Checkbox */
[data-testid="stCheckbox"] {
    color: rgba(255, 255, 255, 0.9) !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER
# ============================================================================
st.markdown("""
<div class="header-title">
    <h1>🧪 Pathology Report Dashboard</h1>
    <p>Aarogyadham Hospital - Professional Report Management System</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state for tabs
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0

# Create main tabs
tab1, tab2, tab3 = st.tabs(["📊 Daily Report", "📁 Saved Reports", "📈 Analytics"])

# ============================================================================
# TAB 1: DAILY REPORT - BIG CENTERED UPLOAD & DOWNLOAD
# ============================================================================
with tab1:
    st.markdown('<div class="glossy-card">', unsafe_allow_html=True)
    
    # Check if we have any saved data to show at top
    saved_dates = get_saved_dates()
    
    if saved_dates:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### 📂 Quick Access Previous Reports")
        with col2:
            if st.button("🔄 Refresh", use_container_width=True, key="refresh_tab1"):
                st.rerun()
        
        saved_dates_sorted = sorted(saved_dates, reverse=True)[:5]  # Last 5
        cols = st.columns(len(saved_dates_sorted))
        for idx, date_str in enumerate(saved_dates_sorted):
            with cols[idx]:
                if st.button(f"📅 {date_str}", use_container_width=True, key=f"quick_date_{date_str}"):
                    st.session_state[f"viewing_{date_str}"] = True
        
        st.divider()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ================================================================
    # BIG CENTERED UPLOAD SECTION
    # ================================================================
    st.markdown("""
    <div class="upload-container">
        <div class="upload-icon">📥</div>
        <div class="upload-title">Upload Daily Report</div>
        <div class="upload-subtitle">Drag and drop your Excel file or click to browse</div>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("", type=["xlsx"], key="upload_daily", label_visibility="collapsed")
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            
            # Validate required columns
            required_columns = ['TestName', 'subgroup']
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                st.error(f"❌ Missing columns: {', '.join(missing)}")
                st.stop()
            
            # Extract date from data
            if 'Date' in df.columns:
                dates = pd.to_datetime(df['Date'].dropna()).dt.date.unique()
                report_date = dates[0] if len(dates) > 0 else datetime.today().date()
                report_date_str = report_date.strftime('%d-%m-%Y')
            else:
                report_date_str = datetime.today().strftime('%d-%m-%Y')
            
            # Process data
            test_counts = build_test_counts(df)
            cat_counts, categorized_df = build_category_counts(df)
            
            # Save data
            save_processed_data(report_date_str, df, test_counts, cat_counts)
            
            st.success(f"✅ Report for {report_date_str} processed successfully!")
            
            # ================================================================
            # REPORT DETAILS CARD WITH DOWNLOAD
            # ================================================================
            st.markdown('<div class="glossy-card">', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([2, 2, 1.5])
            with col1:
                st.markdown(f"### 📅 Report Date: **{report_date_str}**")
            with col2:
                st.markdown(f"### 🏥 Hospital: Aarogyadham")
            with col3:
                excel_report = style_excel(test_counts, cat_counts, report_date_str)
                st.download_button(
                    label="⬇️ Download Report",
                    data=excel_report.getvalue(),
                    file_name=f"Report_{report_date_str}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # ================================================================
            # KEY METRICS
            # ================================================================
            st.markdown("### 📊 Quick Metrics")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("📋 Total Tests", len(df), delta=None)
            with m2:
                ipd_count = int(test_counts.iloc[-1]["IPD"]) if not test_counts.empty else 0
                st.metric("🛏️ IPD", ipd_count)
            with m3:
                opd_count = int(test_counts.iloc[-1]["OPD"]) if not test_counts.empty else 0
                st.metric("🚶 OPD", opd_count)
            
            # ================================================================
            # DETAILED TABLES
            # ================================================================
            st.markdown('<div class="glossy-card">', unsafe_allow_html=True)
            
            col_t1, col_t2 = st.columns(2)
            
            with col_t1:
                st.markdown("#### 🧬 Test-wise Breakdown")
                st.dataframe(test_counts, use_container_width=True, hide_index=True)
            
            with col_t2:
                st.markdown("#### 📂 Category Summary")
                st.dataframe(cat_counts, use_container_width=True, hide_index=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
    else:
        st.info("💡 Select an Excel file with 'TestName' and 'subgroup' columns to begin")

# ============================================================================
# TAB 2: SAVED REPORTS MANAGEMENT
# ============================================================================
with tab2:
    st.markdown('<div class="glossy-card">', unsafe_allow_html=True)
    st.markdown("### 📁 Manage Your Saved Reports")
    st.markdown('</div>', unsafe_allow_html=True)
    
    saved_dates = get_saved_dates()
    
    if saved_dates:
        # Sort dates in descending order (most recent first)
        saved_dates_sorted = sorted(saved_dates, reverse=True)
        
        # Display as cards
        cols = st.columns(1)
        with cols[0]:
            for date_str in saved_dates_sorted:
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                
                with col1:
                    st.markdown(f"#### 📅 {date_str}")
                
                with col2:
                    try:
                        df_loaded, tc, cc = load_processed_data(date_str)
                        if df_loaded is not None:
                            st.caption(f"📋 {len(df_loaded)} tests")
                    except:
                        pass
                
                with col3:
                    if st.button("👁️ View", key=f"view_{date_str}", use_container_width=True):
                        st.session_state[f"viewing_{date_str}"] = True
                
                with col4:
                    if st.button("🗑️ Delete", key=f"del_{date_str}", use_container_width=True):
                        delete_processed_data(date_str)
                        st.success(f"✅ Deleted report for {date_str}")
                        st.rerun()
                
                # Show detailed view if clicked
                if st.session_state.get(f"viewing_{date_str}", False):
                    with st.expander(f"📋 Detailed View - {date_str}", expanded=True):
                        try:
                            df_view, tc_view, cc_view = load_processed_data(date_str)
                            if df_view is not None:
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.markdown("**🧬 Test-wise Counts:**")
                                    st.dataframe(tc_view, use_container_width=True, hide_index=True)
                                with col_b:
                                    st.markdown("**📂 Category Counts:**")
                                    st.dataframe(cc_view, use_container_width=True, hide_index=True)
                        except Exception as e:
                            st.error(f"❌ Error loading data: {str(e)}")
                
                st.divider()
    else:
        st.info("📂 No saved reports yet. Upload a file in the Daily Report tab to save it.")

# ============================================================================
# TAB 3: CUMULATIVE ANALYTICS
# ============================================================================
with tab3:
    st.markdown('<div class="glossy-card">', unsafe_allow_html=True)
    st.markdown("### 📊 Cumulative Analytics Dashboard")
    st.markdown('</div>', unsafe_allow_html=True)
    
    cum_tc, cum_cc = compute_cumulative()
    
    if cum_tc is not None and not cum_tc.empty:
        # Metrics Row
        total_tests = int(cum_tc.iloc[-1]["Total"]) if not cum_tc.empty else 0
        total_ipd = int(cum_tc.iloc[-1]["IPD"]) if not cum_tc.empty else 0
        total_opd = int(cum_tc.iloc[-1]["OPD"]) if not cum_tc.empty else 0
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("📋 Total Cumulative Tests", total_tests)
        with m2:
            st.metric("🛏️ Total IPD", total_ipd)
        with m3:
            st.metric("🚶 Total OPD", total_opd)
        
        # Charts Row
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Test Count Distribution")
            # Prepare data excluding Grand Total row
            tc_data = cum_tc[cum_tc["TestName"] != "Grand Total"].copy()
            
            fig_tc = px.bar(
                tc_data,
                x="TestName",
                y=["IPD", "OPD"],
                title="IPD vs OPD by Test",
                barmode="group",
                color_discrete_map={"IPD": "#ffffff", "OPD": "#cccccc"}
            )
            fig_tc.update_layout(
                hovermode="x unified",
                showlegend=True,
                height=400,
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "#ffffff"}
            )
            st.plotly_chart(fig_tc, use_container_width=True)
        
        with col2:
            st.markdown("#### 📈 Category Distribution")
            cc_data = cum_cc[cum_cc["Category"] != "Grand Total"].copy()
            
            fig_cc = px.pie(
                cc_data,
                values="Count",
                names="Category",
                title="Tests by Category",
                color_discrete_sequence=["#ffffff", "#e0e0e0", "#b0b0b0", "#808080"]
            )
            fig_cc.update_layout(
                height=400,
                paper_bgcolor="rgba(0,0,0,0)",
                font={"color": "#ffffff"}
            )
            st.plotly_chart(fig_cc, use_container_width=True)
        
        # Detailed Tables
        st.markdown("---")
        st.markdown("#### 📈 Detailed Cumulative Data")
        
        tab_test, tab_cat = st.tabs(["🧬 Test Counts", "📂 Category Counts"])
        
        with tab_test:
            st.dataframe(cum_tc, use_container_width=True, hide_index=True)
        
        with tab_cat:
            st.dataframe(cum_cc, use_container_width=True, hide_index=True)
    else:
        st.info("📊 No cumulative data available. Save some reports first!")
