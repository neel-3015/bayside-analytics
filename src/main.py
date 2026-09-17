"""main.py — drop a CSV into data/incoming/, run this, get a report.

    .venv/bin/python src/main.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ingest import load_csv          # noqa: E402
from analyze import summarize        # noqa: E402
from report import build_report      # noqa: E402


def newest_csv(incoming: Path):
    files = list(incoming.glob("*.csv"))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def run(csv_path):
    df = load_csv(csv_path)
    results = summarize(df)
    pdf, charts = build_report(results, ROOT / "reports")
    return results, pdf, charts


def main():
    incoming = ROOT / "data" / "incoming"
    csv = newest_csv(incoming)
    if csv is None:
        print(f"ERROR: no CSV found in {incoming}. "
              "Drop a POS export there first.", file=sys.stderr)
        sys.exit(1)
    print(f"Using {csv.name}")
    results, pdf, charts = run(csv)
    s = results["summary"]
    print(f"  period        {s['start']:%m/%d/%Y} - {s['end']:%m/%d/%Y}")
    print(f"  revenue       ${s['gross_revenue']:,.2f}")
    print(f"  transactions  {s['n_transactions']:,}")
    print(f"  anomalies     {len(results['anomalies'])}")
    print(f"  report        {pdf}")


if __name__ == "__main__":
    main()
