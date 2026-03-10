import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from datetime import datetime, timedelta
import os

# --- 1. DYNAMIC DATE CALCULATION ---
# Function to detect date from file or default to Yesterday
def get_report_dates(df=None):
    # Logic: If data has a date (e.g., 9th), show previous (8th)
    # Defaulting here to yesterday for demonstration
    target_date = datetime.today() - timedelta(days=1) 
    # Example: If your Excel has a 'Date' column, you could use: 
    # target_date = pd.to_datetime(df['Date']).iloc[0] - timedelta(days=1)
    
    return target_date.strftime('%d-%m-%Y'), datetime.today().strftime('%d-%m-%Y')

report_date, generated_date = get_report_dates()

st.set_page_config(page_title="Pathology Report", layout="wide")

# UI HEADER
st.markdown(f"""
    <div style="text-align: center;">
        <h1 style="margin-bottom:0;">DAILY PATHOLOGY REPORT</h1>
        <h3 style="margin-top:0; color: gray;">Report Date: {report_date}</h3>
        <p>Aarogyadham Hospital | Generated: {generated_date}</p>
    </div>
    <hr>
""", unsafe_allow_html=True)

# --- 2. EXCEL STYLING & SINGLE-PAGE PRINT SETUP ---
def style_excel_for_print(test_counts, cat_counts):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        test_counts.to_excel(writer, sheet_name="Daily_Report", startrow=4, index=False)
        start_cat = len(test_counts) + 7
        cat_counts.to_excel(writer, sheet_name="Daily_Report", startrow=start_cat, index=False)

    wb = load_workbook(filename=BytesIO(output.getvalue()))
    ws = wb.active

    # PAGE SETUP: Fit everything on ONE page
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT
    ws.page_setup.paperSize = ws.PAPERSIZE_A4

    # HEADER LABELS IN EXCEL
    ws.merge_cells("A1:D1")
    ws["A1"] = "DAILY PATHOLOGY REPORT"
    ws["A1"].font = Font(bold=True, size=16)
    ws["A1"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:D2")
    ws["A2"] = f"Report Date: {report_date}" # Date below header as requested
    ws["A2"].font = Font(bold=True, size=12)
    ws["A2"].alignment = Alignment(horizontal="center")

    # BORDERS & STYLING
    thin = Side(border_style="thin", color="000000")
    full_border = Border(top=thin, left=thin, right=thin, bottom=thin)
    
    for row in ws.iter_rows(min_row=5, max_row=ws.max_row, min_col=1, max_col=4):
        for cell in row:
            cell.border = full_border

    # FOOTER DATE
    last_row = ws.max_row + 2
    ws.merge_cells(f"A{last_row}:D{last_row}")
    ws[f"A{last_row}"] = f"Generated on: {generated_date}"
    ws[f"A{last_row}"].alignment = Alignment(horizontal="right")

    final_output = BytesIO()
    wb.save(final_output)
    return final_output

# --- 3. SIDEBAR & DOWNLOAD ---
st.sidebar.header("Settings")
file = st.sidebar.file_uploader("Upload Excel", type="xlsx")

if file:
    df = pd.read_excel(file)
    # (Insert your existing build_test_counts / build_category_counts here)
    test_counts = df.groupby("TestName").size().reset_index(name="Total") # Placeholder
    cat_counts = pd.DataFrame({"Category": ["Total"], "Count": [len(df)]}) # Placeholder

    processed_excel = style_excel_for_print(test_counts, cat_counts)
    
    st.sidebar.success("Excel Ready for Printing")
    st.sidebar.download_button(
        label="📥 Download & Print Excel (1-Page Fit)",
        data=processed_excel.getvalue(),
        file_name=f"Pathology_Report_{report_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.dataframe(test_counts, use_container_width=True)
