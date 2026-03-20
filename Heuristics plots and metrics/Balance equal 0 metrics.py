import numpy as np
import pandas as pd
from pathlib import Path


DATA_DIR = Path(r"x:\xxx\xxxx") #to be replaced with the actual path to the dataset location
OUT_DIR = DATA_DIR / "xxx" #to be replaced with the actual path to the output file location
OUT_DIR.mkdir(parents=True, exist_ok=True)

COL_PREV_TS = "prev_timestamp"
COL_CURR_TS = "current_timestamp"
COL_SENDER_BAL = "sender_balance_after"
COL_RECEIVER_BAL = "balance_receiver_before"
COL_SENDER_FLAG = "is_fog_sender"
COL_RECEIVER_FLAG = "is_fog_receiver"

SPANS_HOURS = [6, 24, 48, 72, 96]

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
df[COL_SENDER_BAL] = coerce_numeric(df[COL_SENDER_BAL])
df[COL_RECEIVER_BAL] = coerce_numeric(df[COL_RECEIVER_BAL])
df[COL_SENDER_FLAG] = pd.to_numeric(df[COL_SENDER_FLAG], errors="coerce").fillna(0).astype(int)
df[COL_RECEIVER_FLAG] = pd.to_numeric(df[COL_RECEIVER_FLAG], errors="coerce").fillna(0).astype(int)
df["delta_hours"] = (df["curr_dt"] - df["prev_dt"]).dt.total_seconds() / 3600
work = df.dropna(subset=["delta_hours"]).copy()
work = work[work["delta_hours"] >= 0]
metrics_summary = []
for span in SPANS_HOURS:
    sub = work[work["delta_hours"] <= span].copy()
    if sub.empty:
        continue
    for entity in ["sender", "receiver"]:
        if entity == "sender":
            BAL_COL = COL_SENDER_BAL
            FLAG_COL = COL_SENDER_FLAG
        else:
            BAL_COL = COL_RECEIVER_BAL
            FLAG_COL = COL_RECEIVER_FLAG
        sub_entity = sub.dropna(subset=[BAL_COL]).copy()
        predicted_positive = sub_entity[BAL_COL] == 0
        predicted_negative = sub_entity[BAL_COL] > 0
        actual_positive = sub_entity[FLAG_COL] == 1
        actual_negative = sub_entity[FLAG_COL] == 0
        TP = np.sum(predicted_positive & actual_positive)
        FN = np.sum(predicted_negative & actual_positive)
        FP = np.sum(predicted_positive & actual_negative)
        TN = np.sum(predicted_negative & actual_negative)
        FN_rate = (FN / (TP + FN) * 100) if (TP + FN) > 0 else np.nan
        Recall = (TP / (TP + FN) * 100) if (TP + FN) > 0 else np.nan
        FPR = (FP / (FP + TN) * 100) if (FP + TN) > 0 else np.nan
        Specificity = (TN / (FP + TN) * 100) if (FP + TN) > 0 else np.nan
        metrics_summary.append({
            "entity": entity,
            "span_hours": span,
            "TP": TP,
            "FN": FN,
            "FN_rate_%": FN_rate,
            "Recall_%": Recall,
            "FP": FP,
            "TN": TN,
            "FPR_%": FPR,
            "Specificity_%": Specificity
        })
metrics_df = pd.DataFrame(metrics_summary)
cols_to_round = ["FN_rate", "Recall", "FPR", "Specificity"]
metrics_df[cols_to_round] = metrics_df[cols_to_round].round(2)
metrics_df.to_csv(
    OUT_DIR / "xxx",  # to be replaced with the actual output csv file name
    index=False,
    float_format="%.2f"
)
