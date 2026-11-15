# Sales Data Visualization

Charts and a short written report that turn 1,200 e-commerce orders (January 2023 to June 2025) into five clear insights for business decisions. Built as Project 4 (Data Visualization) of the DecodeLabs Data Analytics track.

## Key findings

| # | Finding | Chart |
|---|---------|-------|
| 1 | Quarterly net revenue fell from about $83K (2023 average) to about $57K (2025 average) | [01](outputs/charts/01_quarterly_net_revenue_trend.png) |
| 2 | Printer leads net revenue, but all 7 products sit within $26K of each other | [02](outputs/charts/02_net_revenue_by_product.png) |
| 3 | 41% of all orders were cancelled or returned | [03](outputs/charts/03_order_status_breakdown.png) |
| 4 | Instagram brings in 33% more net revenue than the Referral channel | [04](outputs/charts/04_net_revenue_by_referral_source.png) |
| 5 | Coupon codes do not change order size (averages between $1,036 and $1,070) | [05](outputs/charts/05_avg_order_value_by_coupon.png) |

The full story, written in Situation, Complication, Resolution form, is in [`reports/insights_report.md`](reports/insights_report.md).

## Project structure

```
sales-data-visualization/
├── data/
│   └── raw/                      # Original dataset (not modified)
├── outputs/
│   ├── charts/                   # Five PNG charts
│   └── tables/                   # Summary CSVs used for the charts
├── reports/
│   └── insights_report.md        # SCR narrative and recommendations
├── src/
│   └── sales_visualization.py    # Cleans data, computes metrics, draws charts
├── .gitignore
├── requirements.txt
└── README.md
```

## How to run

1. Clone the repository and open a terminal in the project folder.
2. (Recommended) create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the script from the project root:
   ```bash
   python src/sales_visualization.py
   ```

The script rebuilds every chart and table from the raw data, so the outputs always match the code.

## Method

- **Net revenue** means order value for orders that are not *Cancelled* or *Returned*. *Pending* orders are included, which is an assumption (see limitations).
- **Quarterly trend** uses quarters, not months, to smooth out small monthly counts (about 40 orders per month).
- **Average order value** uses the `TotalPrice` column for all orders.
- **Chart rules** follow the project brief: one accent colour to highlight the key point, grey for context, direct labels instead of legends, no 3D effects, no pie charts, and bars that start at zero.
- **Data checks** run before any chart is drawn. The script stops if `TotalPrice` does not equal `Quantity × UnitPrice` on every row, or if `OrderID` has duplicates. Both checks passed.

## Limitations

- **2025 is a partial year** (January to June only). Comparisons use quarterly averages, not annual totals.
- **Pending orders are counted as net revenue.** 117 orders from 2023 are still Pending, so net revenue may be overstated.
- **`TotalPrice` does not include coupon discounts.** Coupon impact on real revenue cannot be measured from this file.
- **All shipping addresses read "Main St".** Geographic analysis is not possible.
- **Cancellation causes are not in the data**, so the report suggests areas to investigate rather than confirmed causes.

## Requirements

Python 3.9 or newer. Packages are listed in `requirements.txt`: pandas, matplotlib and openpyxl.

## Author

Manish Chahar
