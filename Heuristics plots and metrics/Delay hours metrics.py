import numpy as np
import pandas as pd
from pathlib import Path


DATA_DIR = Path(r"x:\xxx\xxxx") #to be replaced with the actual path to the dataset location
OUT_DIR = DATA_DIR / "xxx" #to be replaced with the actual path to the output file location
OUT_DIR.mkdir(parents=True, exist_ok=True)

COL_PREV_TS = "prev_timestamp"
COL_CURR_TS = "current_timestamp"
COL_SENDER_KNOWN   = "is_fog_sender"
COL_RECEIVER_KNOWN = "is_fog_receiver"

THRESHOLDS = [6, 24, 48, 72, 96]

def parse_utc(series):
    s = series.astype(str).str.replace(r"\s*UTC\s*$", "", regex=True)
    return pd.to_datetime(s, errors="coerce", utc=True)
def evaluate_delay(work_df, label_column, role_name):
    results = []
    for thr in THRESHOLDS:
        predicted_positive = work_df["delta_hours"] <= thr
        actual_positive = work_df[label_column] == 1
        actual_negative = work_df[label_column] == 0
        TP = np.sum(predicted_positive & actual_positive)
        FN = np.sum(~predicted_positive & actual_positive)
        FP = np.sum(predicted_positive & actual_negative)
        TN = np.sum(~predicted_positive & actual_negative)
        Recall = TP / (TP + FN) if (TP + FN) > 0 else np.nan
        FN_rate = FN / (TP + FN) if (TP + FN) > 0 else np.nan
        FPR = FP / (FP + TN) if (FP + TN) > 0 else np.nan
        Specificity = TN / (FP + TN) if (FP + TN) > 0 else np.nan
        results.append({
            "role": role_name,
            "delay_threshold_hours": thr,
            "TP": TP,
            "FN": FN,
            "FN_rate": FN_rate,
            "Recall": Recall,
            "FP": FP,
            "TN": TN,
            "FPR": FPR,
            "Specificity": Specificity
        })
    return results
dfs = [pd.read_csv(f) for f in DATA_DIR.glob("*.csv")]
if not dfs:
    raise FileNotFoundError(f"No CSV files found in {DATA_DIR}")
df = pd.concat(dfs, ignore_index=True)
df["prev_dt"] = parse_utc(df[COL_PREV_TS])
df["curr_dt"] = parse_utc(df[COL_CURR_TS])
df[COL_SENDER_KNOWN] = pd.to_numeric(df[COL_SENDER_KNOWN], errors="coerce").fillna(0).astype(int)
df[COL_RECEIVER_KNOWN] = pd.to_numeric(df[COL_RECEIVER_KNOWN], errors="coerce").fillna(0).astype(int)
df["delta_hours"] = (
    (df["curr_dt"] - df["prev_dt"]).dt.total_seconds() / 3600
)
work = df.dropna(subset=["delta_hours"]).copy()
work = work[work["delta_hours"] >= 0]
all_results = []
all_results.extend(
    evaluate_delay(work, COL_SENDER_KNOWN, "sender")
)
all_results.extend(
    evaluate_delay(work, COL_RECEIVER_KNOWN, "receiver")
)
results_df = pd.DataFrame(all_results)
results_df.sort_values(
    by=["role", "delay_threshold_hours"],
    inplace=True
)
cols_to_round = ["FN_rate", "Recall", "FPR", "Specificity"]
results_df[cols_to_round] = results_df[cols_to_round].round(2)
results_df.to_csv(
    OUT_DIR / "xxx",  # to be replaced with the actual output csv file name
    index=False,
    float_format="%.2f"
)

