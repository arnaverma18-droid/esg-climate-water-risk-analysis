"""
ESG Climate & Water Risk Analysis
Arnav Verma — arnaverma18-droid.github.io

Run this script to generate all 5 chart images into the images/ folder.
Usage: python generate_charts.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── Create output folder ──────────────────────────────────────────────────────
os.makedirs("images", exist_ok=True)

# ── Colour palette ────────────────────────────────────────────────────────────
BG     = "#0d1117"
CARD   = "#161b22"
A1     = "#58a6ff"   # carbon — blue
A2     = "#3fb950"   # water  — green
WARN   = "#f78166"   # high risk — red
TEXT   = "#e6edf3"
MUTED  = "#8b949e"
BORDER = "#30363d"
SECTOR_COLORS = ["#f78166","#ff9e64","#e3b341","#58a6ff",
                 "#3fb950","#bc8cff","#79c0ff","#ffa657"]

plt.rcParams.update({
    "figure.facecolor": BG,   "axes.facecolor": CARD,
    "axes.edgecolor":  BORDER,"axes.labelcolor": TEXT,
    "xtick.color": MUTED,     "ytick.color": MUTED,
    "text.color":  TEXT,      "font.family": "monospace",
    "axes.grid": True,        "grid.color": BORDER,
    "grid.alpha": 0.5,
    "axes.spines.top": False, "axes.spines.right": False,
})

# ── Load data ─────────────────────────────────────────────────────────────────
portfolio   = pd.read_csv("data/portfolio_data.csv")
sector_risk = pd.read_csv("data/sector_risk.csv")

# ── Merge & compute exposures ─────────────────────────────────────────────────
df = portfolio.merge(sector_risk, on="sector")
df["carbon_exposure"] = df["portfolio_weight"] * df["carbon_intensity"]
df["water_exposure"]  = df["portfolio_weight"] * df["water_intensity"]
df["composite_esg"]   = df["carbon_exposure"] + df["water_exposure"] * 0.6

sector_agg = (
    df.groupby("sector")
    .agg(
        total_weight    = ("portfolio_weight", "sum"),
        carbon_exposure = ("carbon_exposure",  "sum"),
        water_exposure  = ("water_exposure",   "sum"),
        composite_esg   = ("composite_esg",    "sum"),
    )
    .reset_index()
    .sort_values("carbon_exposure", ascending=False)
)

print("Data loaded.")
print(f"  Holdings : {len(df)}")
print(f"  Sectors  : {df['sector'].nunique()}")
print(f"  Carbon exposure total : {df['carbon_exposure'].sum():.3f}")
print(f"  Water exposure total  : {df['water_exposure'].sum():.3f}")
print(f"  Composite ESG total   : {df['composite_esg'].sum():.3f}")
print()

# ── CHART 1 — Sector ESG Exposure (stacked bar) ───────────────────────────────
fig, ax = plt.subplots(figsize=(11, 6), facecolor=BG)
ax.set_facecolor(CARD)
x = np.arange(len(sector_agg))

ax.bar(x, sector_agg["carbon_exposure"], 0.55,
       label="Carbon Exposure", color=A1, alpha=0.9, zorder=3)
ax.bar(x, sector_agg["water_exposure"] * 0.6, 0.55,
       bottom=sector_agg["carbon_exposure"],
       label="Water Exposure (0.6x scaled)", color=A2, alpha=0.85, zorder=3)

ax.set_xticks(x)
ax.set_xticklabels(sector_agg["sector"], rotation=30, ha="right", fontsize=9)
ax.set_ylabel("Weighted ESG Exposure", fontsize=10, labelpad=10)
ax.set_title("Portfolio ESG Exposure by Sector  |  Carbon + Water Risk",
             fontsize=12, fontweight="bold", color=TEXT, pad=14)
ax.legend(frameon=False, fontsize=9)

plt.tight_layout()
plt.savefig("images/sector_esg_exposure.png", dpi=150,
            bbox_inches="tight", facecolor=BG)
plt.close()
print("✓ Chart 1 saved — sector_esg_exposure.png")

# ── CHART 2 — Portfolio Allocation Donut ──────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 7), facecolor=BG)
ax.set_facecolor(BG)

wedges, _, ats = ax.pie(
    sector_agg["total_weight"], labels=None,
    autopct=lambda p: f"{p:.1f}%" if p > 5 else "",
    startangle=140, colors=SECTOR_COLORS,
    wedgeprops=dict(width=0.55, edgecolor=BG, linewidth=2),
    pctdistance=0.75,
)
for at in ats:
    at.set_fontsize(8); at.set_color("white"); at.set_fontweight("bold")

ax.legend(wedges, sector_agg["sector"],
          loc="center left", bbox_to_anchor=(0.85, 0.5),
          frameon=False, fontsize=9)
ax.set_title("Portfolio Allocation by Sector",
             fontsize=13, fontweight="bold", color=TEXT, pad=14)
ax.text(0, 0, "30\nHoldings", ha="center", va="center",
        fontsize=12, color=TEXT, fontweight="bold")

plt.tight_layout()
plt.savefig("images/portfolio_allocation.png", dpi=150,
            bbox_inches="tight", facecolor=BG)
plt.close()
print("✓ Chart 2 saved — portfolio_allocation.png")

# ── CHART 3 — Top 10 Holdings by Composite ESG ───────────────────────────────
top10 = df.nlargest(10, "composite_esg").sort_values("composite_esg")

fig, ax = plt.subplots(figsize=(10, 6), facecolor=BG)
ax.set_facecolor(CARD)

bar_colors = [WARN if v > top10["composite_esg"].quantile(0.7) else A1
              for v in top10["composite_esg"]]
bars = ax.barh(top10["company"], top10["composite_esg"],
               color=bar_colors, alpha=0.9, zorder=3, height=0.65)

for b in bars:
    ax.text(b.get_width() + 0.02, b.get_y() + b.get_height() / 2,
            f"{b.get_width():.2f}", va="center", fontsize=8, color=MUTED)

ax.set_xlabel("Composite ESG Score", fontsize=10, labelpad=10)
ax.set_title("Top 10 Holdings by ESG Exposure  |  Carbon + Water Risk",
             fontsize=12, fontweight="bold", color=TEXT, pad=14)
ax.legend(
    handles=[mpatches.Patch(color=WARN, label="High Risk"),
             mpatches.Patch(color=A1,   label="Moderate Risk")],
    frameon=False, fontsize=9, loc="lower right"
)

plt.tight_layout()
plt.savefig("images/top_holdings_exposure.png", dpi=150,
            bbox_inches="tight", facecolor=BG)
plt.close()
print("✓ Chart 3 saved — top_holdings_exposure.png")

# ── CHART 4 — Rebalancing Comparison ─────────────────────────────────────────
rebalanced = {
    "Energy": 0.04, "Utilities": 0.06, "Materials": 0.06,
    "Technology": 0.22, "Financials": 0.18,
    "Consumer Staples": 0.14, "Healthcare": 0.16,
    "Consumer Discretionary": 0.14,
}
si      = sector_risk.set_index("sector")
orig_c  = sector_agg.set_index("sector")["carbon_exposure"]
orig_w  = sector_agg.set_index("sector")["water_exposure"]
rebal_c = pd.Series({s: rebalanced[s] * si.loc[s, "carbon_intensity"]
                     for s in sector_agg["sector"]})
rebal_w = pd.Series({s: rebalanced[s] * si.loc[s, "water_intensity"]
                     for s in sector_agg["sector"]})

fig, axes = plt.subplots(1, 2, figsize=(13, 6), facecolor=BG)
for ax in axes:
    ax.set_facecolor(CARD)

x    = np.arange(len(sector_agg))
secs = sector_agg["sector"].values

axes[0].bar(x - 0.19, orig_c.values,  0.38, label="Original",   color=WARN, alpha=0.85, zorder=3)
axes[0].bar(x + 0.19, rebal_c.values, 0.38, label="Rebalanced", color=A1,   alpha=0.85, zorder=3)
axes[0].set_xticks(x)
axes[0].set_xticklabels(secs, rotation=35, ha="right", fontsize=8)
axes[0].set_title("Carbon Exposure: Original vs Rebalanced",
                  fontsize=11, fontweight="bold", color=TEXT)
axes[0].legend(frameon=False, fontsize=9)

axes[1].bar(x - 0.19, orig_w.values,  0.38, label="Original",   color="#f0883e", alpha=0.85, zorder=3)
axes[1].bar(x + 0.19, rebal_w.values, 0.38, label="Rebalanced", color=A2,        alpha=0.85, zorder=3)
axes[1].set_xticks(x)
axes[1].set_xticklabels(secs, rotation=35, ha="right", fontsize=8)
axes[1].set_title("Water Exposure: Original vs Rebalanced",
                  fontsize=11, fontweight="bold", color=TEXT)
axes[1].legend(frameon=False, fontsize=9)

plt.suptitle("Portfolio Rebalancing Impact on ESG Risk",
             fontsize=13, fontweight="bold", color=TEXT, y=1.01)
plt.tight_layout()
plt.savefig("images/rebalancing_comparison.png", dpi=150,
            bbox_inches="tight", facecolor=BG)
plt.close()
print("✓ Chart 4 saved — rebalancing_comparison.png")

# ── CHART 5 — Dual Exposure Scatter (Water Feature) ──────────────────────────
fig, ax = plt.subplots(figsize=(10, 7), facecolor=BG)
ax.set_facecolor(CARD)

sector_list  = list(sector_agg["sector"])
point_colors = [SECTOR_COLORS[sector_list.index(s) % len(SECTOR_COLORS)]
                for s in df["sector"]]

ax.scatter(df["carbon_exposure"], df["water_exposure"],
           c=point_colors, s=df["portfolio_weight"] * 1800,
           alpha=0.75, edgecolors=BG, linewidth=1.5, zorder=3)

for _, row in df.iterrows():
    if row["composite_esg"] > df["composite_esg"].quantile(0.75):
        ax.annotate(row["company"],
                    xy=(row["carbon_exposure"], row["water_exposure"]),
                    xytext=(5, 5), textcoords="offset points",
                    fontsize=7.5, color=MUTED)

ax.axvline(df["carbon_exposure"].median(), color=BORDER, linestyle="--", alpha=0.6)
ax.axhline(df["water_exposure"].median(),  color=BORDER, linestyle="--", alpha=0.6)

ax.text(df["carbon_exposure"].max() * 0.82, df["water_exposure"].max() * 0.88,
        "HIGH\nDUAL RISK", fontsize=8, color=WARN, fontweight="bold", alpha=0.8)
ax.text(0.01, df["water_exposure"].min() * 1.1,
        "LOW RISK", fontsize=8, color=A2, fontweight="bold", alpha=0.8)

ax.set_xlabel("Carbon Exposure  (weight × carbon intensity)", fontsize=10, labelpad=10)
ax.set_ylabel("Water Exposure  (weight × water intensity)",   fontsize=10, labelpad=10)
ax.set_title("Dual Exposure Map: Carbon vs Water Risk\n(bubble size = portfolio weight)",
             fontsize=12, fontweight="bold", color=TEXT, pad=14)
ax.legend(
    handles=[mpatches.Patch(color=SECTOR_COLORS[i % len(SECTOR_COLORS)], label=s)
             for i, s in enumerate(sector_list)],
    frameon=False, fontsize=8.5, loc="upper left", ncol=2
)

plt.tight_layout()
plt.savefig("images/water_carbon_scatter.png", dpi=150,
            bbox_inches="tight", facecolor=BG)
plt.close()
print("✓ Chart 5 saved — water_carbon_scatter.png")

print()
print("All 5 charts generated in images/ folder.")
