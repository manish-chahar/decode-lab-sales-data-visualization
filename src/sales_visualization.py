"""
Sales Data Visualization
------------------------
Reads the orders dataset, computes the metrics used in the report, saves
five charts to outputs/charts/ and the supporting tables to outputs/tables/.

Run from the project root:
    python src/sales_visualization.py

Requirements: see requirements.txt
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# ---------------------------------------------------------------------------
# Paths and settings
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "raw" / "Dataset_for_Dat__Analytics.xlsx"
CHART_DIR = ROOT / "outputs" / "charts"
TABLE_DIR = ROOT / "outputs" / "tables"

# Statuses that are NOT counted as net revenue (assumption, see README)
NOT_NET_STATUSES = ["Cancelled", "Returned"]

# Colour rules from the project brief: one accent colour, everything else muted
ACCENT = "#1F6FEB"   # highlight colour (the "spotlight")
CONTEXT = "#B8C0CC"  # muted grey for context
TEXT = "#222222"

plt.rcParams.update({
    "text.parse_math": False,  # stop "$...$" being read as math, so dollar signs print as typed
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#888888",
    "axes.titlelocation": "left",
    "axes.titleweight": "bold",
    "axes.titlesize": 13,
    "axes.labelcolor": TEXT,
    "xtick.color": TEXT,
    "ytick.color": TEXT,
})


# ---------------------------------------------------------------------------
# 1. Load and check the data
# ---------------------------------------------------------------------------
def load_and_clean(path: Path) -> pd.DataFrame:
    """Load the Excel file and add the helper columns used by the charts."""
    df = pd.read_excel(path)

    # Blank coupon = the customer used no coupon. Label it so it can be charted.
    df["CouponCode"] = df["CouponCode"].fillna("No coupon")

    df["Date"] = pd.to_datetime(df["Date"])
    df["Quarter"] = df["Date"].dt.to_period("Q")
    df["IsNet"] = ~df["OrderStatus"].isin(NOT_NET_STATUSES)

    # Data check: TotalPrice should equal Quantity x UnitPrice on every row.
    # Stop early if this ever fails, so no chart is built on bad numbers.
    mismatch = (df["TotalPrice"] - df["Quantity"] * df["UnitPrice"]).abs() > 0.05
    if mismatch.any():
        raise ValueError(
            f"{mismatch.sum()} rows where TotalPrice != Quantity x UnitPrice"
        )

    if df["OrderID"].duplicated().any():
        raise ValueError("Duplicate OrderID values found")

    return df


# ---------------------------------------------------------------------------
# 2. Compute the metrics (every chart and headline number comes from here)
# ---------------------------------------------------------------------------
def compute_metrics(df: pd.DataFrame) -> dict:
    net = df[df["IsNet"]]

    quarterly = net.groupby("Quarter")["TotalPrice"].sum()
    by_product = net.groupby("Product")["TotalPrice"].sum().sort_values(ascending=False)
    status_counts = df["OrderStatus"].value_counts()
    by_referral = net.groupby("ReferralSource")["TotalPrice"].sum().sort_values(ascending=False)
    aov_by_coupon = df.groupby("CouponCode")["TotalPrice"].mean().sort_values(ascending=False)

    avg_2023 = quarterly[quarterly.index.year == 2023].mean()
    avg_2025 = quarterly[quarterly.index.year == 2025].mean()

    metrics = {
        "total_orders": len(df),
        "gross_order_value": df["TotalPrice"].sum(),
        "net_revenue": net["TotalPrice"].sum(),
        "not_net_share": 1 - df["IsNet"].mean(),
        "quarterly": quarterly,
        "avg_quarter_2023": avg_2023,
        "avg_quarter_2025": avg_2025,
        "by_product": by_product,
        "product_spread": by_product.max() - by_product.min(),
        "status_counts": status_counts,
        "by_referral": by_referral,
        "referral_gap": by_referral.iloc[0] / by_referral.iloc[-1] - 1,
        "aov_by_coupon": aov_by_coupon,
        "aov_min": aov_by_coupon.min(),
        "aov_max": aov_by_coupon.max(),
    }
    return metrics


def save_tables(m: dict) -> None:
    """Write the summary tables to outputs/tables/ as CSV files."""
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    q = m["quarterly"].rename("net_revenue").reset_index()
    q["Quarter"] = q["Quarter"].astype(str)
    q.to_csv(TABLE_DIR / "quarterly_net_revenue.csv", index=False)

    m["by_product"].rename("net_revenue").to_csv(TABLE_DIR / "net_revenue_by_product.csv")
    m["status_counts"].rename("orders").to_csv(TABLE_DIR / "orders_by_status.csv")
    m["by_referral"].rename("net_revenue").to_csv(TABLE_DIR / "net_revenue_by_referral.csv")
    m["aov_by_coupon"].rename("avg_order_value").to_csv(TABLE_DIR / "avg_order_value_by_coupon.csv")


# ---------------------------------------------------------------------------
# 3. Chart helpers
# ---------------------------------------------------------------------------
def money_k(value: float) -> str:
    return f"${value / 1000:,.0f}K"


def add_title(ax, title: str, subtitle: str) -> None:
    """Action title (the conclusion) plus a smaller line explaining the metric."""
    ax.set_title(title, pad=34)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=10, color="#555555")


def save(fig, filename: str) -> None:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(CHART_DIR / filename, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 4. The five charts
# ---------------------------------------------------------------------------
def chart_quarterly_trend(m: dict) -> None:
    q = m["quarterly"]
    labels = [f"Q{p.quarter}\n{p.year}" for p in q.index]
    values = q.values

    fig, ax = plt.subplots(figsize=(11, 6))
    x = range(len(values))
    ax.plot(x, values, color=ACCENT, linewidth=2.8, marker="o", markersize=7)

    for xi, v in zip(x, values):
        ax.annotate(money_k(v), (xi, v), textcoords="offset points",
                    xytext=(0, 11), ha="center", fontsize=10, color=TEXT)

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, values.max() * 1.25)  # starts at zero: no exaggerated slope
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: money_k(v)))
    ax.grid(axis="y", color="#E6E6E6", linewidth=0.8)
    ax.set_axisbelow(True)

    add_title(
        ax,
        f"Quarterly net revenue fell from about {money_k(m['avg_quarter_2023'])} "
        f"(2023 average) to {money_k(m['avg_quarter_2025'])} (2025 average)",
        "Net revenue = orders not Cancelled or Returned.  "
        "2025 covers January to June only.",
    )
    save(fig, "01_quarterly_net_revenue_trend.png")


def chart_revenue_by_product(m: dict) -> None:
    s = m["by_product"].sort_values()  # ascending so the largest is on top
    colors = [ACCENT if v == m["by_product"].max() else CONTEXT for v in s.values]

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.barh(s.index, s.values, color=colors, height=0.6)
    for bar, v in zip(bars, s.values):
        ax.text(v + 1500, bar.get_y() + bar.get_height() / 2, money_k(v),
                va="center", fontsize=10, color=TEXT)

    ax.set_xlim(0, s.max() * 1.15)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: money_k(v)))
    ax.set_xlabel("Net revenue")

    top_product = m["by_product"].index[0]
    n_products = len(m["by_product"])
    add_title(
        ax,
        f"{top_product} leads net revenue, but all {n_products} products "
        f"sit within {money_k(m['product_spread'])} of each other",
        "Net revenue by product.  Bars start at zero.",
    )
    save(fig, "02_net_revenue_by_product.png")


def chart_order_status(m: dict) -> None:
    s = m["status_counts"].sort_values()
    total = s.sum()
    colors = [ACCENT if status in NOT_NET_STATUSES else CONTEXT for status in s.index]

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.barh(s.index, s.values, color=colors, height=0.6)
    for bar, v in zip(bars, s.values):
        ax.text(v + 3, bar.get_y() + bar.get_height() / 2,
                f"{v:,} orders ({v / total:.0%})", va="center", fontsize=10, color=TEXT)

    ax.set_xlim(0, s.max() * 1.3)
    ax.set_xlabel("Number of orders")

    add_title(
        ax,
        f"{m['not_net_share']:.0%} of all orders were cancelled or returned",
        "Highlighted bars: Cancelled and Returned.  Bars start at zero.",
    )
    save(fig, "03_order_status_breakdown.png")


def chart_referral_revenue(m: dict) -> None:
    s = m["by_referral"]
    colors = [ACCENT if i == 0 else CONTEXT for i in range(len(s))]

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.bar(s.index, s.values, color=colors, width=0.6)
    for bar, v in zip(bars, s.values):
        ax.annotate(money_k(v), (bar.get_x() + bar.get_width() / 2, v),
                    textcoords="offset points", xytext=(0, 6),
                    ha="center", fontsize=10, color=TEXT)

    ax.set_ylim(0, s.max() * 1.15)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: money_k(v)))
    ax.set_ylabel("Net revenue")

    add_title(
        ax,
        f"Instagram brings in {m['referral_gap']:.0%} more net revenue "
        f"than the Referral channel",
        "Net revenue by referral source.  Bars start at zero.",
    )
    save(fig, "04_net_revenue_by_referral_source.png")


def chart_coupon_order_value(m: dict) -> None:
    s = m["aov_by_coupon"]

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.bar(s.index, s.values, color=CONTEXT, width=0.6)
    for bar, v in zip(bars, s.values):
        ax.annotate(f"${v:,.0f}", (bar.get_x() + bar.get_width() / 2, v),
                    textcoords="offset points", xytext=(0, 6),
                    ha="center", fontsize=10, color=TEXT)

    ax.set_ylim(0, s.max() * 1.2)  # zero baseline keeps the comparison honest
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.set_ylabel("Average order value")
    ax.set_xlabel("Coupon code used")

    add_title(
        ax,
        f"Coupon codes do not change order size: averages sit between "
        f"${m['aov_min']:,.0f} and ${m['aov_max']:,.0f}",
        "Average TotalPrice per order, all statuses.  "
        "The dataset's TotalPrice has no coupon discount applied.",
    )
    save(fig, "05_avg_order_value_by_coupon.png")


# ---------------------------------------------------------------------------
# 5. Run everything
# ---------------------------------------------------------------------------
def main() -> None:
    df = load_and_clean(DATA_FILE)
    m = compute_metrics(df)
    save_tables(m)

    chart_quarterly_trend(m)
    chart_revenue_by_product(m)
    chart_order_status(m)
    chart_referral_revenue(m)
    chart_coupon_order_value(m)

    print(f"Orders: {m['total_orders']:,}")
    print(f"Gross order value: ${m['gross_order_value']:,.0f}")
    print(f"Net revenue: ${m['net_revenue']:,.0f}")
    print(f"Cancelled or returned share: {m['not_net_share']:.1%}")
    print("Charts saved to outputs/charts/, tables to outputs/tables/")


if __name__ == "__main__":
    main()
