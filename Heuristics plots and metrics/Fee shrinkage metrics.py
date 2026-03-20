import numpy as np
import pandas as pd
from pathlib import Path


DATA_DIR = Path(r"x:\xxx\xxxx") #to be replaced with the actual path to the dataset location
OUT_DIR = DATA_DIR / "xxx" #to be replaced with the actual path to the output file location
OUT_DIR.mkdir(parents=True, exist_ok=True)


R_PREV_TS = "current_timestamp"
R_CURR_TS = "future_timestamp"
R_LABEL = "is_fog_receiver"
S_PREV_TS = "prev_timestamp"
S_CURR_TS = "current_timestamp"
S_LABEL = "is_fog_sender"
COL_PREV_RECEIVED = "prev_amount_received"
COL_OUTPUT = "receiver_output"


SPANS_HOURS = [6, 24, 48, 72, 96]
EPS_VALUES = [0.005, 0.01, 0.02, 0.03, 0.05]


def parse_utc(series):
    s = series.astype(str).str.replace(r"\s*UTC\s*$", "", regex=True)
    return pd.to_datetime(s, errors="coerce", utc=True)
def coerce_numeric(series):
    s = series.astype(str).str.replace(",", "", regex=False)
    s = s.str.replace(" BTC", "", regex=False).str.replace("btc", "", regex=False)
    return pd.to_numeric(s, errors="coerce")
dfs = [pd.read_csv(f) for f in DATA_DIR.glob("*.csv")]
df = pd.concat(dfs, ignore_index=True)
df["r_prev_dt"] = parse_utc(df[R_PREV_TS])
df["r_curr_dt"] = parse_utc(df[R_CURR_TS])
df[COL_PREV_RECEIVED] = coerce_numeric(df[COL_PREV_RECEIVED])
df[COL_OUTPUT] = coerce_numeric(df[COL_OUTPUT])
df[R_LABEL] = pd.to_numeric(df[R_LABEL], errors="coerce").fillna(0).astype(int)
df["r_delta"] = (df["r_curr_dt"] - df["r_prev_dt"]).dt.total_seconds() / 3600
receiver = df.dropna(subset=["r_delta", COL_PREV_RECEIVED, COL_OUTPUT]).copy()
receiver = receiver[
    (receiver["r_delta"] >= 0) &
    (receiver[COL_PREV_RECEIVED] > 0)
]
receiver["shrinkage"] = (
    (receiver[COL_PREV_RECEIVED] - receiver[COL_OUTPUT]) /
    receiver[COL_PREV_RECEIVED]
)
receiver = receiver[receiver["shrinkage"] >= 0]
df["s_prev_dt"] = parse_utc(df[S_PREV_TS])
df["s_curr_dt"] = parse_utc(df[S_CURR_TS])
df[S_LABEL] = pd.to_numeric(df[S_LABEL], errors="coerce").fillna(0).astype(int)
df["s_delta"] = (df["s_curr_dt"] - df["s_prev_dt"]).dt.total_seconds() / 3600
sender = df.dropna(subset=["s_delta", COL_PREV_RECEIVED, COL_OUTPUT]).copy()
sender = sender[
    (sender["s_delta"] >= 0) &
    (sender[COL_PREV_RECEIVED] > 0)
]
sender["shrinkage"] = (
    (sender[COL_PREV_RECEIVED] - sender[COL_OUTPUT]) /
    sender[COL_PREV_RECEIVED]
)
sender = sender[sender["shrinkage"] >= 0]
def run_sweep(data, delta_col, label_col, role):
    results = []
    for span in SPANS_HOURS:
        sub = data[data[delta_col] <= span]
        if sub.empty:
            continue
        actual_positive = sub[label_col] == 1
        actual_negative = sub[label_col] == 0
        for eps in EPS_VALUES:
            predicted_positive = sub["shrinkage"] <= eps
            TP = np.sum(predicted_positive & actual_positive)
            FN = np.sum(~predicted_positive & actual_positive)
            FP = np.sum(predicted_positive & actual_negative)
            TN = np.sum(~predicted_positive & actual_negative)
            FN_rate = FN / (TP + FN) if (TP + FN) > 0 else np.nan
            Recall = TP / (TP + FN) if (TP + FN) > 0 else np.nan
            FPR = FP / (FP + TN) if (FP + TN) > 0 else np.nan
            Specificity = TN / (FP + TN) if (FP + TN) > 0 else np.nan
            results.append({
                "role": role,
                "span_hours": span,
                "epsilon": eps,
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

receiver_results = run_sweep(receiver, "r_delta", R_LABEL, "receiver")
sender_results = run_sweep(sender, "s_delta", S_LABEL, "sender")
results_df = pd.DataFrame(receiver_results + sender_results)
cols_to_round = ["FN_rate", "Recall", "FPR", "Specificity"]
results_df[cols_to_round] = (results_df[cols_to_round] * 100).round(2)
results_df.to_csv(
    OUT_DIR / "xxx",  # to be replaced with the actual output csv file name
    index=False,
    float_format="%.2f"
)

