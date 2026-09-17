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


def find_anomalies(df, z_thresh=3.5):
    """Flag lines whose line_total z-score within their item is extreme
    (catches price-keying errors like $1,333 on a $13 wine)."""
    stats = df.groupby("item")["line_total"].agg(["mean", "std"])
    joined = df.join(stats, on="item", rsuffix="_item")
    z = (joined["line_total"] - joined["mean"]) / joined["std"].replace(0, pd.NA)
    flags = joined[z.abs() > z_thresh]
    cols = ["date", "item", "category", "qty", "unit_price", "line_total"]
    out = flags[cols].copy()
    out["z"] = z[abs(z) > z_thresh]
    return out.sort_values("date")
