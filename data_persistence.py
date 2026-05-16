import os
import pandas as pd

DATA_DIR = "processed_data"
os.makedirs(DATA_DIR, exist_ok=True)


def save_processed_data(date_str, df, test_counts, cat_counts):
    """Save processed data for a given date."""
    date_dir = os.path.join(DATA_DIR, date_str)
    os.makedirs(date_dir, exist_ok=True)
    df.to_csv(os.path.join(date_dir, "raw.csv"), index=False)
    test_counts.to_csv(os.path.join(date_dir, "test_counts.csv"), index=False)
    cat_counts.to_csv(os.path.join(date_dir, "cat_counts.csv"), index=False)


def load_processed_data(date_str):
    """Load processed data for a given date."""
    date_dir = os.path.join(DATA_DIR, date_str)
    if not os.path.exists(date_dir):
        return None, None, None
    df = pd.read_csv(os.path.join(date_dir, "raw.csv"))
    test_counts = pd.read_csv(os.path.join(date_dir, "test_counts.csv"))
    cat_counts = pd.read_csv(os.path.join(date_dir, "cat_counts.csv"))
    return df, test_counts, cat_counts


def delete_processed_data(date_str):
    """Delete processed data for a given date."""
    date_dir = os.path.join(DATA_DIR, date_str)
    if os.path.exists(date_dir):
        import shutil
        shutil.rmtree(date_dir)


def get_saved_dates():
    """Get list of saved dates."""
    if not os.path.exists(DATA_DIR):
        return []
    return sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))])


def compute_cumulative():
    """Compute cumulative sums across all saved dates."""
    dates = get_saved_dates()
    if not dates:
        return None, None
    all_test_counts = []
    all_cat_counts = []
    for date in dates:
        _, tc, cc = load_processed_data(date)
        if tc is not None:
            tc['Date'] = date
            all_test_counts.append(tc)
        if cc is not None:
            cc['Date'] = date
            all_cat_counts.append(cc)
    if all_test_counts:
        combined_tc = pd.concat(all_test_counts, ignore_index=True)
        cumulative_tc = combined_tc.groupby('TestName')[['IPD', 'OPD', 'Total']].sum().reset_index()
        grand_total_tc = pd.DataFrame([{"TestName": "Grand Total", "IPD": int(cumulative_tc["IPD"].sum()), "OPD": int(cumulative_tc["OPD"].sum()), "Total": int(cumulative_tc["Total"].sum())}])
        cumulative_tc = pd.concat([cumulative_tc, grand_total_tc], ignore_index=True)
    else:
        cumulative_tc = None
    if all_cat_counts:
        combined_cc = pd.concat(all_cat_counts, ignore_index=True)
        cumulative_cc = combined_cc.groupby('Category')[['Count']].sum().reset_index()
        grand_total_cc = pd.DataFrame([{"Category": "Grand Total", "Count": int(cumulative_cc["Count"].sum())}])
        cumulative_cc = pd.concat([cumulative_cc, grand_total_cc], ignore_index=True)
    else:
        cumulative_cc = None
    return cumulative_tc, cumulative_cc
