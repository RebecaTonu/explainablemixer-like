import numpy as np
import pandas as pd
from pathlib import Path


DATA_DIR = Path(r"x:\xxx\xxxx") #to be replaced with the actual path to the dataset location
OUT_DIR = DATA_DIR / "xxx" #to be replaced with the actual path to the output file location
OUT_DIR.mkdir(parents=True, exist_ok=True)

COL_PREV_TS = "prev_timestamp"
COL_CURR_TS = "current_timestamp"
COL_SENDER_BAL   = "sender_balance_after"
COL_RECEIVER_BAL = "balance_receiver_before"
COL_SENDER_FLAG   = "is_fog_sender"
COL_RECEIVER_FLAG = "is_fog_receiver"

SPANS_HOURS = [6, 24, 48, 72, 96]
THRESHOLDS  = [1e-8, 1e-6, 1e-4, 1e-3, 1e-2]


def parse_utc(series):
    s = series.astype(str).str.replace(r"\s*UTC\s*$", "", regex=True)
    return pd.to_datetime(s, errors="coerce", utc=True)
def coerce_numeric(series):
    s = series.astype(str).str.replace(",", "", regex=False)
    s = s.str.replace(" BTC", "", regex=False).str.replace("btc", "", regex=False)
    return pd.to_numeric(s, errors="coerce")
dfs = [pd.read_csv(f) for f in DATA_DIR.glob("*.csv")]
if not dfs:
    raise FileNotFoundError(f"No CSV files found in {DATA_DIR}")
df = pd.concat(dfs, ignore_index=True)
df["prev_dt"] = parse_utc(df[COL_PREV_TS])
df["curr_dt"] = parse_utc(df[COL_CURR_TS])
df[COL_SENDER_BAL]   = coerce_numeric(df[COL_SENDER_BAL])
df[COL_RECEIVER_BAL] = coerce_numeric(df[COL_RECEIVER_BAL])
df[COL_SENDER_FLAG]   = pd.to_numeric(df[COL_SENDER_FLAG], errors="coerce").fillna(0).astype(int)
df[COL_RECEIVER_FLAG] = pd.to_numeric(df[COL_RECEIVER_FLAG], errors="coerce").fillna(0).astype(int)
df["delta_hours"] = (df["curr_dt"] - df["prev_dt"]).dt.total_seconds() / 3600
work = df.dropna(subset=["delta_hours", "curr_dt"]).copy()
work = work[work["delta_hours"] >= 0]
summary_metrics = []
for span in SPANS_HOURS:
    sub = work[work["delta_hours"] <= span].copy()
    if sub.empty:
        continue
    for eps in THRESHOLDS:
        threshold_display = f"{eps:.0e}" if eps < 1e-4 else eps
        predicted_s = (sub[COL_SENDER_BAL] <= eps)
        actual_s    = (sub[COL_SENDER_FLAG] == 1)
        TP = len(sub[predicted_s & actual_s])
        FN = len(sub[~predicted_s & actual_s])
        FP = len(sub[predicted_s & ~actual_s])
        TN = len(sub[~predicted_s & ~actual_s])
        FN_rate = (FN / (TP + FN) * 100) if (TP + FN) > 0 else np.nan
        Recall  = (TP / (TP + FN) * 100) if (TP + FN) > 0 else np.nan
        FPR     = (FP / (FP + TN) * 100) if (FP + TN) > 0 else np.nan
        Specificity = (TN / (FP + TN) * 100) if (FP + TN) > 0 else np.nan

        summary_metrics.append({
            "role": "sender",
            "span_hours": span,
            "threshold": threshold_display,
            "TP": TP,
            "FN": FN,
            "FN_rate": FN_rate,
            "Recall": Recall,
            "FP": FP,
            "TN": TN,
            "FPR": FPR,
            "Specificity": Specificity
        })
        predicted_r = (sub[COL_RECEIVER_BAL] <= eps)
        actual_r    = (sub[COL_RECEIVER_FLAG] == 1)
        TP = len(sub[predicted_r & actual_r])
        FN = len(sub[~predicted_r & actual_r])
        FP = len(sub[predicted_r & ~actual_r])
        TN = len(sub[~predicted_r & ~actual_r])
        FN_rate = (FN / (TP + FN) * 100) if (TP + FN) > 0 else np.nan
        Recall  = (TP / (TP + FN) * 100) if (TP + FN) > 0 else np.nan
        FPR     = (FP / (FP + TN) * 100) if (FP + TN) > 0 else np.nan
        Specificity = (TN / (FP + TN) * 100) if (FP + TN) > 0 else np.nan
        summary_metrics.append({
            "role": "receiver",
            "span_hours": span,
            "threshold": threshold_display,
            "TP": TP,
            "FN": FN,
            "FN_rate": FN_rate,
            "Recall": Recall,
            "FP": FP,
            "TN": TN,
            "FPR": FPR,
            "Specificity": Specificity
        })
metrics_df = pd.DataFrame(summary_metrics)
cols_to_round = ["FN_rate", "Recall", "FPR", "Specificity"]
metrics_df[cols_to_round] = metrics_df[cols_to_round].round(2)
metrics_df.to_csv(
    OUT_DIR / "xxx",  # to be replaced with the actual output csv file name
    index=False,
    float_format="%.2f"
)

