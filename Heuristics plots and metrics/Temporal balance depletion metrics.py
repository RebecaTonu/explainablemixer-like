import numpy as np
import pandas as pd
from pathlib import Path


DATA_DIR = Path(r"x:\xxx\xxxx") #to be replaced with the actual path to the dataset location
OUT_DIR = DATA_DIR / "xxx" #to be replaced with the actual path to the output file location
OUT_DIR.mkdir(parents=True, exist_ok=True)


DUST_LIMIT = 1e-08
BAL_ZERO_WINDOW = 6
S_DELAY_WINDOW = 6
R_DELAY_WINDOW = 24


def parse_utc(series):
    s = series.astype(str).str.replace(r"\s*UTC\s*$", "", regex=True)
    return pd.to_datetime(s, errors="coerce", utc=True)
def coerce_numeric(series):
    s = series.astype(str).str.replace(",", "", regex=False)
    for btc_str in [" btc", "BTC", " BTC", "btc"]:
        s = s.str.replace(btc_str, "", regex=False)
    return pd.to_numeric(s, errors="coerce")
csv_files = list(DATA_DIR.glob("*.csv"))
if not csv_files:
    print(f"No CSV files found in {DATA_DIR}")
    exit()
dfs = [pd.read_csv(f) for f in csv_files]
df = pd.concat(dfs, ignore_index=True)
df["dt_prev"] = parse_utc(df["prev_timestamp"])
df["dt_curr"] = parse_utc(df["current_timestamp"])
if "future_timestamp" in df.columns:
    df["dt_futr"] = parse_utc(df["future_timestamp"])
metrics_summary = []
for entity_name in ["sender", "receiver"]:
    if entity_name == "sender":
        bal_col = "sender_balance_after"
        flag_col = "is_fog_sender"
        delta = (df["dt_curr"] - df["dt_prev"]).dt.total_seconds() / 3600
        thr = S_DELAY_WINDOW
    else:
        bal_col = "balance_receiver_before"
        flag_col = "is_fog_receiver"
        if "dt_futr" in df.columns:
            delta = (df["dt_futr"] - df["dt_curr"]).dt.total_seconds() / 3600
        else:
            delta = (df["dt_curr"] - df["dt_prev"]).dt.total_seconds() / 3600
        thr = R_DELAY_WINDOW
    sub = df.dropna(subset=[bal_col]).copy()
    sub["delta_h"] = delta
    sub["bal_val"] = coerce_numeric(sub[bal_col])
    sub = sub[sub["delta_h"] >= 0]
    is_dust = sub["bal_val"] <= DUST_LIMIT
    cond1 = (sub["bal_val"] == 0) & (sub["delta_h"] < BAL_ZERO_WINDOW)
    cond2 = (sub["delta_h"] <= thr)
    predicted_positive = (cond1 | cond2) & is_dust
    predicted_negative = ~predicted_positive
    actual_positive = sub[flag_col].fillna(0).astype(int) == 1
    actual_negative = sub[flag_col].fillna(0).astype(int) == 0
    TP = np.sum(predicted_positive & actual_positive)
    FN = np.sum(predicted_negative & actual_positive)
    FP = np.sum(predicted_positive & actual_negative)
    TN = np.sum(predicted_negative & actual_negative)
    Recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    FN_rate = 1 - Recall
    FPR = FP / (FP + TN) if (FP + TN) > 0 else 0
    Specificity = 1 - FPR
    metrics_summary.append({
        "entity": entity_name,
        "span_hours": thr,
        "TP": int(TP),
        "FN": int(FN),
        "FN_rate_%": round(FN_rate * 100, 2),
        "Recall_%": round(Recall * 100, 2),
        "FP": int(FP),
        "TN": int(TN),
        "FPR_%": round(FPR * 100, 2),
        "Specificity_%": round(Specificity * 100, 2)
    })
results_df = pd.DataFrame(metrics_summary)
results_df.to_csv(
    OUT_DIR / "xxx",  # to be replaced with the actual output csv file name
    index=False,
    float_format="%.2f"
)
