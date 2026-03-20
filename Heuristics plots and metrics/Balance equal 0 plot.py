import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


DATA_DIR = Path(r"x:\xxx\xxxx") #to be replaced with the actual path to the dataset location
OUT_DIR = DATA_DIR / "xxx" #to be replaced with the actual path to the output file location
OUT_DIR.mkdir(parents=True, exist_ok=True)


S_PREV, S_CURR, S_BAL = "prev_timestamp", "current_timestamp", "sender_balance_after"
R_PREV, R_CURR, R_BAL = "current_timestamp", "future_timestamp", "balance_receiver_before"
SPANS_HOURS = [6, 24, 48, 72, 96]


plt.rcParams.update({
    "font.family": "serif",
    "font.size": 7,
    "axes.titlesize": 7.5,
    "axes.labelsize": 7,
    "xtick.labelsize": 6,
    "ytick.labelsize": 6,
    "text.color": "black"
})



def parse_utc(series):
    s = series.astype(str).str.replace(r"\s*UTC\s*$", "", regex=True)
    return pd.to_datetime(s, errors="coerce", utc=True)
def coerce_numeric(series):
    s = series.astype(str).str.replace(",", "", regex=False)
    for btc_str in [" btc", "BTC", " BTC", "btc"]:
        s = s.str.replace(btc_str, "", regex=False)
    return pd.to_numeric(s, errors="coerce")
def get_matrix(df, p_col, c_col, b_col):
    temp = df[[p_col, c_col, b_col]].copy()
    temp["p_dt"] = parse_utc(temp[p_col])
    temp["c_dt"] = parse_utc(temp[c_col])
    temp["val"] = coerce_numeric(temp[b_col])
    temp["diff"] = (temp["c_dt"] - temp["p_dt"]).dt.total_seconds() / 3600
    temp = temp.dropna(subset=["diff", "val", "c_dt"])
    temp = temp[temp["diff"] >= 0]
    temp["year"] = temp["c_dt"].dt.year
    years = sorted(temp["year"].unique())
    m_flag = pd.DataFrame(index=years, columns=SPANS_HOURS)
    m_norm = pd.DataFrame(index=years, columns=SPANS_HOURS)
    for s in SPANS_HOURS:
        sub = temp[temp["diff"] <= s]
        m_flag[s] = sub[sub["val"] == 0].groupby("year").size()
        m_norm[s] = sub[sub["val"] != 0].groupby("year").size()
    return m_flag.fillna(0), m_norm.fillna(0), years
dfs = [pd.read_csv(f) for f in DATA_DIR.glob("*.csv")]
full_df = pd.concat(dfs, ignore_index=True)
s_f, s_n, years = get_matrix(full_df, S_PREV, S_CURR, S_BAL)
r_f, r_n, _ = get_matrix(full_df, R_PREV, R_CURR, R_BAL)
fig, axes = plt.subplots(2, 2, figsize=(6.5, 4.5), sharey=True, sharex=True,
                         gridspec_kw={'wspace': 0.35, 'hspace': 0.4})
plot_configs = [
    (s_f, "Reds", "Number of sender addresses flagged\n as potential mixers"),
    (s_n, "Greens", "Number of sender addresses not flagged\n as potential mixers"),
    (r_f, "Oranges", "Number of receiver addresses flagged\n as potential mixers"),
    (r_n, "Blues", "Number of receiver addresses not flagged\n as potential mixers")
]
for ax, (matrix, cmap, title) in zip(axes.flat, plot_configs):
    im = ax.imshow(matrix.values, cmap=cmap, aspect="auto", alpha=0.75)
    ax.set_title(title, fontweight='bold', pad=6)
    for i in range(len(years)):
        for j in range(len(SPANS_HOURS)):
            val = int(matrix.iloc[i, j])
            ax.text(j, i, f"{val:,}", ha="center", va="center",
                    fontsize=5.5, color="black")
    cb = fig.colorbar(im, ax=ax, shrink=0.8, aspect=20)
    cb.ax.tick_params(labelsize=5)
for ax in axes[:, 0]: ax.set_ylabel("Year")
for ax in axes.flat:
    ax.set_xticks(np.arange(len(SPANS_HOURS)))
    ax.set_xticklabels([f"{h}h" for h in SPANS_HOURS])
    ax.set_yticks(np.arange(len(years)))
    ax.set_yticklabels(years)
plt.savefig(
    OUT_DIR / "xxx",  # to be replaced with the actual output img  name
    dpi=300,
    bbox_inches="tight",
    pad_inches=0.02
)
plt.close()

