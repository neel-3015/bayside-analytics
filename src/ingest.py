"""ingest.py — read a POS export CSV, validate, clean.

Returns a tidy pandas DataFrame with columns:
  date (datetime64), time, register, transaction_id, category, item,
  qty (int), unit_price (float), line_total (float), is_refund (bool)
Raises ValueError with a friendly message on bad input.
"""
from pathlib import Path

import pandas as pd

REQUIRED = ["Date", "Time", "Register", "TransactionID", "Category",
            "Item", "Qty", "UnitPrice", "LineTotal", "IsRefund"]

RENAME = {
    "Date": "date", "Time": "time", "Register": "register",
    "TransactionID": "transaction_id", "Category": "category",
    "Item": "item", "Qty": "qty", "UnitPrice": "unit_price",
    "LineTotal": "line_total", "IsRefund": "is_refund",
}


def load_csv(path):
    path = Path(path)
    if not path.exists():
        raise ValueError(f"file not found: {path}")
    df = pd.read_csv(path, dtype=str)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")

    df = df.rename(columns=RENAME)
    df["date"] = pd.to_datetime(df["date"] + " " + df["time"],
                                errors="coerce")
    bad_dates = df["date"].isna().sum()
    df = df.dropna(subset=["date"])

    for col in ("qty", "unit_price", "line_total"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["qty", "unit_price", "line_total"])

    df["qty"] = df["qty"].astype(int)
    df["is_refund"] = (
        df["is_refund"].astype(str).str.strip().str.lower().isin(["true", "1", "yes"])
    )
    # Refunds may be flagged True with positive prices; make totals signed.
    df.loc[df["is_refund"], "line_total"] = -df.loc[df["is_refund"], "line_total"].abs()
    df.loc[df["is_refund"], "qty"] = -df.loc[df["is_refund"], "qty"].abs()

    before = len(df)
    df = df.drop_duplicates()
    dupes = before - len(df)

    df = df[df["date"].dt.date == df["date"].dt.date]  # no-op guard, keeps schema
    df = df.sort_values("date").reset_index(drop=True)
    df.attrs["dropped_bad_dates"] = int(bad_dates)
    df.attrs["dropped_dupes"] = int(dupes)
    return df
