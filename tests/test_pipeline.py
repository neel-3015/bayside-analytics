"""Fixture: dupe row, positive-priced refund, bad date, planted $1999 keying error."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

HEADER = ("Date,Time,Register,TransactionID,Category,Item,"
          "Qty,UnitPrice,LineTotal,IsRefund")
NORMAL_ROSE = [
    "03/16/2026,11:05,1,5,Wine,Test rose,1,13.33,13.33,False",
    "03/16/2026,11:06,1,6,Wine,Test rose,1,12.90,12.90,False",
]
ROWS = [
    "03/15/2026,10:00,1,1,Beer,Test lager,2,5.00,10.00,False",
    "03/15/2026,10:00,1,1,Beer,Test lager,2,5.00,10.00,False",  # dupe
    "03/16/2026,11:00,1,2,Wine,Test rose,1,13.33,13.33,True",   # refund
    *NORMAL_ROSE,
    "notadate,12:00,1,3,Beer,Test lager,1,5.00,5.00,False",      # bad date
    "03/17/2026,12:00,1,4,Wine,Test rose,1,1999.00,1999.00,False",  # planted
]


@pytest.fixture
def sales_df(tmp_path):
    from ingest import load_csv
    csv = tmp_path / "t.csv"
    csv.write_text(HEADER + "\n" + "\n".join(ROWS) + "\n")
    return load_csv(csv)


def test_cleaning(sales_df):
    assert len(sales_df) == 5
    assert sales_df.attrs["dropped_dupes"] == 1
    assert sales_df.attrs["dropped_bad_dates"] == 1


def test_refunds_signed_negative(sales_df):
    r = sales_df[sales_df["is_refund"]]
    assert (r["line_total"] < 0).all() and (r["qty"] < 0).all()


def test_revenue_math(sales_df):
    from analyze import summarize
    s = summarize(sales_df)["summary"]
    assert abs(s["net_revenue"] - 2021.90) < 0.01
    assert abs(s["refund_value"] - 13.33) < 0.01


def test_planted_anomaly_caught_and_only_it(sales_df):
    from analyze import summarize
    anom = summarize(sales_df)["anomalies"]
    assert len(anom) == 1
    assert anom.iloc[0]["unit_price"] == 1999.0


def test_discounts_and_volume_not_flagged(sales_df):
    """A $19.90 two-pack of the same lager must NOT be an anomaly."""
    from analyze import find_anomalies
    assert find_anomalies(sales_df)["item"].eq("Test lager").sum() == 0


def test_missing_columns_error(tmp_path):
    from ingest import load_csv
    bad = tmp_path / "bad.csv"
    bad.write_text("Date,Item\n03/15/2026,X\n")
    try:
        load_csv(bad)
        assert False, "should have raised"
    except ValueError as e:
        assert "missing required columns" in str(e)
