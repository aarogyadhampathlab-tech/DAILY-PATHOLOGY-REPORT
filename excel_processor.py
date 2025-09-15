import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from datetime import datetime
import os

# Optional: AI categorization (safe fallback if unavailable)
try:
    import openai
    OPENAI_AVAILABLE = True
    openai.api_key = os.getenv("OPENAI_API_KEY")
except Exception:
    OPENAI_AVAILABLE = False

st.set_page_config(page_title="Daily Pathology Report", page_icon="📊", layout="wide")
st.title("📊 Daily Pathology Report Generator")

# -------------------------
# Static category rules (includes your custom mappings)
# -------------------------
CATEGORY_RULES = {
    "Biochemistry": [
        "RENAL FUNCTION TEST", "LIVER FUNCTION TEST", "BLOOD GLUCOSE",
        "GLYCOSYLATED HB", "SGOT", "SGPT", "BLOOD UREA",
        "VIRAL MARKER", "PREOPERATIVE PROFILE", "SEROLOGY", "PT/INR"
    ],
    "Clinical": [
        "URINE ANALYSIS", "PLEURAL FLUID EXAMINATION",
        "Plural Fluid for R/E Biochemistry / ADA"
    ],
    "Hematology": [
        "COMPLETE BLOOD COUNTS [CBC]", "TOTAL LEUCOCYTE COUNT",
        "FLUID DLC", "COMPLETE HEMOGRAM WITH ESR", "BLOOD GROUP"
    ],
    "Immunology": [
        "Hormone Assays Report", "Serum IGE", "VDRL TITER", "HBsAg",
        "HCV ANTIBODY TEST", "CA-125", "THYROID FUNCTION TEST",
        "THYROID STIMULATING HORMONE", "TOTAL THYROID PROFILE",
        "IgG IgM S Typhe", "C-REACTIVE PROTEIN"
    ]
}

# -------------------------
# Helpers
# -------------------------
def normalize_bookingmode(x):
    s = "" if pd.isna(x) else str(x).strip().upper()
    if "IPD" in s:
        return "IPD"
    if "OPD" in s:
        return "OPD Indent"
    return "OPD Indent"

def ai_batch_categorize(unknown_tests):
    """Optional AI categorization of unknown tests."""
    if not unknown_tests or not OPENAI_AVAILABLE or not openai.api_key:
        return {}
    tests_text = "\n".join([f"- Test: {t}, Subgroup: {s}" for t, s in unknown_tests])
    prompt = f"""
Categories: Biochemistry, Clinical, Hematology, Immunology.
Assign each test to the best category.
Return CSV: TestName,Subgroup,Category
Tests:
{tests_text}
"""
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0
        )
        mapping = {}
        for line in resp['choices'][0]['message']['content'].strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) == 3 and parts[2] in CATEGORY_RULES.keys():
                mapping[(parts[0], parts[1])] = parts[2]
        return mapping
    except Exception:
        return {}

def build_test_counts(df):
    df = df.copy()
    df["BookingMode_norm"] = df["BookingMode"].apply(normalize_bookingmode)
    pivot = df.pivot_table(index="TestName", columns="BookingMode_norm", aggfunc="size", fill_value=0).reset_index()
    pivot["IPD"] = pivot.get("IPD", 0)
    pivot["OPD"] = pivot.get("OPD Indent", 0)
    pivot["Total"] = pivot[["IPD", "OPD"]].sum(axis=1)
    result = pivot[["TestName", "IPD", "OPD", "Total"]].sort_values("TestName").reset_index(drop=True)
    grand_total = pd.DataFrame([{
        "TestName": "Grand Total",
        "IPD": int(result["IPD"].sum()),
        "OPD": int(result["OPD"].sum()),
        "Total": int(result["Total"].sum())
    }])
    return pd.concat([result, grand_total], ignore_index=True)

def build_category_counts(df):
    df = df.copy().reset_index(drop=True)
    unknown_tests, final_cats = [], []
    for _, row in df.iterrows():
        text = f"{row['TestName']} {row['subgroup']}".upper()
        final = None
        for category, keywords in CATEGORY_RULES.items():
            if any(kw.upper() in text for kw in keywords):
                final = category
                break
        if not final:
            unknown_tests.append((str(row['TestName']), str(row['subgroup'])))
        final_cats.append(final)

    ai_mapping = ai_batch_categorize(unknown_tests)
    corrected_cats = []
    for (cat, row) in zip(final_cats, df.itertuples()):
        corrected_cats.append(cat or ai_mapping.get((str(row.TestName), str(row.subgroup)), "Biochemistry"))
    df["Final_Category"] = corrected_cats

    results = []
    for category in CATEGORY_RULES.keys():
        cnt = int((df["Final_Category"] == category).sum())
        results.append({"Category": category, "Count": cnt})
    results.append({"Category": "Grand Total", "Count": int(len(df))})
    return pd.DataFrame(results), df

def style_excel(test_counts, cat_counts):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([["DAILY PATHOLOGY REPORT"]]).to_excel(
            writer, sheet_name="Analysis", header=False, index=False
        )
        test_counts.to_excel(writer, sheet_name="Analysis", startrow=2, index=False)
        start_cat = len(test_counts) + 5
        pd.DataFrame([["Category Counts"]]).to_excel(writer, sheet_name="Analysis", startrow=start_cat, header=False, index=False)
        cat_counts.to_excel(writer, sheet_name="Analysis", startrow=start_cat+1, index=False)

    wb = load_workbook(filename=BytesIO(output.getvalue()))
    ws = wb.active

    # Title
    ws.merge_cells("A1:D1")
    ws["A1"].font = Font(bold=True, size=16)
    ws["A1"].alignment = Alignment(horizontal="center")

    header_fill = PatternFill(start_color="87CEFA", end_color="87CEFA", fill_type="solid")
    total_fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
    thin = Side(border_style="thin", color="000000")

    # Header row styling
    for row in ws.iter_rows(min_row=3, max_row=3, min_col=1, max_col=4):
        for cell in row:
            cell.font = Font(bold=True)
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
            cell.border = Border(top=thin, left=thin, right=thin, bottom=thin)

    # Highlight grand total
    for row in ws.iter_rows(min_row=2+len(test_counts), max_row=2+len(test_counts), min_col=1, max_col=4):
        for cell in row:
            cell.font = Font(bold=True)
            cell.fill = total_fill

    # Category headers
    cat_start = len(test_counts) + 6
    for row in ws.iter_rows(min_row=cat_start, max_row=cat_start, min_col=1, max_col=2):
        for cell in row:
            cell.font = Font(bold=True)
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

    for row in ws.iter_rows(min_row=cat_start+len(cat_counts), max_row=cat_start+len(cat_counts), min_col=1, max_col=2):
        for cell in row:
            cell.font = Font(bold=True)
            cell.fill = total_fill

    ws.column_dimensions["A"].width = 45
    ws.column_dimensions["B"].width = 12
    ws.column_dimensions["C"].width = 10
    ws.column_dimensions["D"].width = 10

    # Footer date
    last_row = ws.max_row + 2
    ws.merge_cells(f"A{last_row}:D{last_row}")
    ws[f"A{last_row}"] = f"Generated on: {datetime.today().strftime('%d-%m-%Y')}"
    ws[f"A{last_row}"].alignment = Alignment(horizontal="center")
    ws[f"A{last_row}"].font = Font(italic=True, size=10)

    final_output = BytesIO()
    wb.save(final_output)
    return final_output

# -------------------------
# Streamlit App
# -------------------------
uploaded_file = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Normalize column names and rename
    df.columns = df.columns.str.strip().str.lower()
    df = df.rename(columns={
        "testname": "TestName",
        "bookingmode": "BookingMode",
        "subgroup": "subgroup"
    })
    df = df.dropna(subset=["TestName", "BookingMode", "subgroup"]).reset_index(drop=True)

    st.subheader("Raw Data Preview")
    st.dataframe(df.head(20))

    with st.spinner("Processing..."):
        test_counts = build_test_counts(df)
        cat_counts, _ = build_category_counts(df)
        styled_file = style_excel(test_counts, cat_counts)

    st.subheader("Test Name Counts")
    st.dataframe(test_counts)

    st.subheader("Category Counts")
    st.dataframe(cat_counts)

    st.download_button(
        label="⬇️ Download Daily Pathology Report",
        data=styled_file.getvalue(),
        file_name="daily_pathology_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
