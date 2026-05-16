import os
from datetime import datetime, timedelta

try:
    import openai
    OPENAI_AVAILABLE = True
    openai.api_key = os.getenv("OPENAI_API_KEY")
except Exception:
    openai = None
    OPENAI_AVAILABLE = False


def default_dates():
    today = datetime.today()
    yesterday = today - timedelta(days=1)
    today_str = today.strftime('%d-%m-%Y')
    yesterday_str = yesterday.strftime('%d-%m-%Y')
    return today_str, yesterday_str


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
