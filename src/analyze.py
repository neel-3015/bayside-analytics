"""analyze.py — turn a tidy sales DataFrame into report-ready facts."""
import pandas as pd


def summarize(df):
    gross = df["line_total"].sum()
    refunds = df[df["is_refund"]]
    s = {
        "start": df["date"].min(),
        "end": df["date"].max(),
        "n_rows": len(df),
        "n_transactions": df["transaction_id"].nunique(),
        "gross_revenue": gross,
        "net_revenue": gross,  # refunds already signed negative in ingest
        "refund_count": len(refunds),
        "refund_value": -refunds["line_total"].sum(),
        "avg_transaction_value": gross / max(df["transaction_id"].nunique(), 1),
    }
    weekly = (
        df.assign(week=df["date"].dt.to_period("W"))
          .pivot_table(index="week", columns="category",
                       values="line_total", aggfunc="sum", fill_value=0)
    )
    top_skus = (
        df.groupby("item")["line_total"].sum()
          .sort_values(ascending=False).head(10)
    )
    dow = (
        df.assign(day=df["date"].dt.day_name())
          .pivot_table(index="day", values="line_total", aggfunc="sum")
          .reindex(["Monday", "Tuesday", "Wednesday", "Thursday",
                    "Friday", "Saturday", "Sunday"])
    )
    category_mix = df.groupby("category")["line_total"].sum().sort_values(ascending=False)
    anomalies = find_anomalies(df)
    return {
        "summary": s,
        "weekly_by_category": weekly,
        "top_skus": top_skus,
        "day_of_week": dow,
        "category_mix": category_mix,
        "anomalies": anomalies,
    }


def find_anomalies(df, ratio=10.0):
    """Flag lines whose unit price is > ratio x the item's median price.
    A keying error is always an OVER-key ($1,999 typed for $13.33), and
    with real sales volumes (dozens+ per item) the median is unaffected
    by the handful of errors in the data. Requires >=3 sales so a
    2-row item can't set its own baseline."""
    stats = df.groupby("item")["unit_price"].agg(["median", "count"])
    med = df["item"].map(stats["median"])
    cnt = df["item"].map(stats["count"])
    mask = (df["unit_price"] > ratio * med) & (cnt >= 3)
    out = df.loc[mask, ["date", "item", "category", "qty",
                        "unit_price", "line_total"]].copy()
    out["x_normal"] = (df["unit_price"] / med)[mask].round(1)
    return out.sort_values("date")
