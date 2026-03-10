import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import os

# -------------------------
# Configuration & Dates
# -------------------------
today = datetime.today()
yesterday = today - timedelta(days=1)
today_str = today.strftime('%d-%m-%Y')
yesterday_str = yesterday.strftime('%d-%m-%Y')

# Optional: AI categorization fallback
try:
    import openai
    OPENAI_AVAILABLE = True
    openai.api_key = os.getenv("OPENAI_API_KEY")
except Exception:
    OPENAI_AVAILABLE = False

st.set_page_config(page_title="Daily Pathology Report", page_icon="📊", layout="wide")

st.markdown(f"""
<style>
    .main {{ background-color: #f8f9fa; }}
    [data-testid="stMetric"] {{ background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 0 6px rgba(0,0,0,0.08); }}
</style>
<h2 style="margin-bottom:0">Daily Pathology Report</h2>
<p style="color:gray;margin-top:0">
Pathology Department · Aarogyadham Hospital <br>
<b>Report Date: {yesterday_str}</b> | Generated: {today_str}
</p>
<hr>
""", unsafe_allow_html=True)

# -------------------------
# Processing Helpers
# -------------------------
def normalize_bookingmode(x):
    s = "" if pd.isna(x) else str(x).strip().upper()
    return "IPD" if "IPD" in s else "OPD Indent"

def build_test_counts(df):
    df = df.copy()
    df["BookingMode_norm"] = df["BookingMode"].apply(normalize_bookingmode)
    pivot = df.pivot_table(index="TestName", columns="BookingMode_norm", aggfunc="size", fill_value=0).reset_index()
    pivot["IPD"], pivot["OPD"] = pivot.get("IPD", 0), pivot.get("OPD Indent", 0)
    pivot["Total"] = pivot["IPD"] + pivot["OPD"]
    result = pivot[["TestName", "IPD", "OPD", "Total"]].sort_values("TestName").reset_index(drop=True)
    grand_total = pd.DataFrame([{"TestName": "Grand Total", "IPD": int(result["IPD"].sum()), "OPD": int(result["OPD"].sum()), "Total": int(result["Total"].sum())}])
    return pd.concat([result, grand_total], ignore_index=True)

def build_category_counts(df):
    # (Existing mapping logic omitted for brevity, keeping same as your previous working version)
    # Returns cat_counts (df) and categorized_df
    pass 

def style_excel(test_counts, cat_counts):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        test_counts.to_excel(writer, sheet_name="Analysis", startrow=2, index=False)
        start_cat = len(test_counts) + 5
        cat_counts.to_excel(writer, sheet_name="Analysis", startrow=start_cat+1, index=False)

    wb = load_workbook(filename=BytesIO(output.getvalue()))
    ws = wb.active

    # --- PRINT SETTINGS (Fit to One Page) ---
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToHeight = 1
    ws.page_setup.fitToWidth = 1
    ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT

    # Styling
    thin = Side(border_style="thin", color="000000")
    border = Border(top=thin, left=thin, right=thin, bottom=thin)
    header_fill = PatternFill(start_color="87CEFA", end_color="87CEFA", fill_type="solid")
    
    # Header Title
    ws.merge_cells("A1:D1")
    ws["A1"] = f"DAILY PATHOLOGY REPORT - {yesterday_str}"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A1"].alignment = Alignment(horizontal="center")

    # Apply Borders & Styles to Test Table
    for row in ws.iter_rows(min_row=3, max_row=3+len(test_counts), min_col=1, max_col=4):
        for cell in row:
            cell.border = border
            if cell.row == 3: cell.fill, cell.font = header_fill, Font(bold=True)

    # --- ADD PREVIOUS DAY DATE IN DOWN ROW ---
    last_row = ws.max_row + 2
    ws.merge_cells(f"A{last_row}:D{last_row}")
    ws[f"A{last_row}"] = f"Verified for Date: {yesterday_str} | Printed on: {today_str}"
    ws[f"A{last_row}"].font = Font(italic=True, bold=True)
    ws[f"A{last_row}"].alignment = Alignment(horizontal="right")

    ws.column_dimensions["A"].width = 40
    for col in ["B","C","D"]: ws.column_dimensions[col].width = 12

    final_output = BytesIO()
    wb.save(final_output)
    return final_output

# -------------------------
# Sidebar & Execution
# -------------------------
st.sidebar.title("🧪 Report Controls")
uploaded_file = st.sidebar.file_uploader("Upload Daily Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    test_counts = build_test_counts(df)
    # Placeholder for category logic from your code
    cat_counts = pd.DataFrame([{"Category": "Total", "Count": len(df)}]) 

    # 1. Download Button
    excel_report = style_excel(test_counts, cat_counts)
    st.sidebar.download_button(
        label="📥 Download Excel (Fit to Page)",
        data=excel_report.getvalue(),
        file_name=f"Pathology_Report_{yesterday_str}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # 2. Print Button (JavaScript)
    st.sidebar.markdown("---")
    st.sidebar.write("Print Dashboard View:")
    if st.sidebar.button("🖨️ Print This Page"):
        components.html("<script>window.print();</script>", height=0)

    # Display Tables
    st.subheader(f"Test Counts for {yesterday_str}")
    st.dataframe(test_counts, use_container_width=True, hide_index=True)
    
    st.markdown(f"<p style='text-align:right;'><b>Report Date: {yesterday_str}</b></p>", unsafe_allow_html=True)
else:
    st.info("Upload the Excel file to begin.")
