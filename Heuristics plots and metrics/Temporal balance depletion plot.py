import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


DATA_DIR = Path(r"x:\xxx\xxxx") #to be replaced with the actual path to the dataset location
OUT_DIR = DATA_DIR / "xxx" #to be replaced with the actual path to the output file location
OUT_DIR.mkdir(parents=True, exist_ok=True)


DUST_LIMIT = 0.00000001
BAL_ZERO_WINDOW = 6
S_DELAY_WINDOW = 6
R_DELAY_WINDOW = 24

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
def get_matrix(df, p_col, c_col, bal_col, delay_win):
    temp = df[[p_col, c_col, bal_col]].copy()
    temp["p_dt"] = parse_utc(temp[p_col])
    temp["c_dt"] = parse_utc(temp[c_col])
    temp["bal_val"] = coerce_numeric(temp[bal_col])
    temp["diff"] = (temp["c_dt"] - temp["p_dt"]).dt.total_seconds() / 3600
    temp = temp.dropna(subset=["diff", "bal_val", "c_dt"])
    temp = temp[temp["diff"] >= 0]
    temp["year"] = temp["c_dt"].dt.year
    years = sorted(temp["year"].unique())
    dust_mask = temp["bal_val"] <= DUST_LIMIT
    cond_bal_zero = (temp["bal_val"] == 0) & (temp["diff"] < BAL_ZERO_WINDOW)
    cond_delay = (temp["diff"] <= delay_win)
    flag_mask = (cond_bal_zero & dust_mask) | (cond_delay & dust_mask)
    m_flag = pd.DataFrame(index=years, columns=[0])
    m_norm = pd.DataFrame(index=years, columns=[0])
    m_flag[0] = temp[flag_mask].groupby("year").size()
    m_norm[0] = temp[~flag_mask].groupby("year").size()
    return m_flag.fillna(0), m_norm.fillna(0), years
dfs = [pd.read_csv(f) for f in DATA_DIR.glob("*.csv")]
full_df = pd.concat(dfs, ignore_index=True)
s_f, s_n, years = get_matrix(full_df, "prev_timestamp", "current_timestamp", "sender_balance_after", S_DELAY_WINDOW)
futr_col = "future_timestamp" if "future_timestamp" in full_df.columns else "current_timestamp"
r_f, r_n, _ = get_matrix(full_df, "current_timestamp", futr_col, "balance_receiver_before", R_DELAY_WINDOW)
fig, axes = plt.subplots(2, 2, figsize=(6.5, 4.5), sharey=True, gridspec_kw={'wspace': 0.35, 'hspace': 0.4})
plot_configs = [
    (s_f, "Reds", "Number of sender addresses flagged\nas potential mixers", "6"),
    (s_n, "Greens", "Number of sender addresses not flagged\nas potential mixers", "6"),
    (r_f, "Oranges", "Number of receiver addresses flagged\nas potential mixers", "24"),
    (r_n, "Blues", "Number of receiver addresses not flagged\nas potential mixers", "24")
]
for ax, (matrix, cmap, title, ox_label) in zip(axes.flat, plot_configs):
    im = ax.imshow(matrix.values, cmap=cmap, aspect="auto", alpha=0.75)
    ax.set_title(title, fontweight='bold', pad=6)
    for i in range(len(years)):
        val = int(matrix.iloc[i, 0])
        ax.text(0, i, f"{val:,}", ha="center", va="center", fontsize=6, color="black")
    cb = fig.colorbar(im, ax=ax, shrink=0.8, aspect=20)
    cb.ax.tick_params(labelsize=5)
    ax.set_xticks([0])
    ax.set_xticklabels([ox_label])
    ax.set_yticks(np.arange(len(years)))
    ax.set_yticklabels(years)
for ax in axes[:, 0]:
    ax.set_ylabel("Year")
file_path =OUT_DIR / "xxx",  # to be replaced with the actual output img  name
plt.savefig(
    file_path,
    dpi=300,
    bbox_inches="tight",
    pad_inches=0.02
)
plt.close()

