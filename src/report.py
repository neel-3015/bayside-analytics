"""report.py — turn analyze.summarize() results into charts + a PDF."""
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # no window needed; we just save files
import matplotlib.pyplot as plt


def _charts(results, out_dir):
    paths = []
    s = results["summary"]

    # 1. Weekly revenue by category (stacked bars)
    weekly = results["weekly_by_category"]
    ax = weekly.plot(kind="bar", stacked=True, figsize=(10, 5),
                     ylabel="Revenue ($)")
    ax.set_title("Weekly revenue by category")
    ax.set_xticks(range(len(weekly)))
    ax.set_xticklabels([str(p) for p in weekly.index], rotation=45, ha="right")
    p = out_dir / "chart_weekly.png"
    ax.figure.savefig(p, bbox_inches="tight")
    paths.append(p)

    # 2. Day-of-week totals
    ax = results["day_of_week"].plot(kind="bar", figsize=(8, 4), legend=False,
                                     ylabel="Revenue ($)")
    ax.set_title("Revenue by day of week")
    p = out_dir / "chart_dow.png"
    ax.figure.savefig(p, bbox_inches="tight")
    paths.append(p)

    # 3. Top 10 SKUs
    ax = results["top_skus"].plot(kind="barh", figsize=(8, 5), legend=False,
                                  xlabel="Revenue ($)")
    ax.invert_yaxis()
    ax.set_title("Top 10 items by revenue")
    p = out_dir / "chart_top10.png"
    ax.figure.savefig(p, bbox_inches="tight")
    paths.append(p)

    plt.close("all")
    return paths


PDF_HEAD = """%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]
/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Courier>>endobj
"""


def _text_pdf(lines, out_path):
    """Minimal hand-rolled PDF: one page, monospace text. No deps."""
    body = "BT /F1 9 Tf 40 752 Td 13 TL\n"
    for ln in lines:
        safe = ln.replace("\\", "").replace("(", "").replace(")", "")
        safe = safe.encode("ascii", "replace").decode()[:110]
        body += f"({safe}) Tj T*\n"
    body += "ET"
    stream = f"4 0 obj<</Length {len(body)}>>stream\n{body}\nendstream endobj\n"
    out_path.write_bytes((PDF_HEAD + stream +
                          "trailer<</Root 1 0 R>>\n%%EOF").encode())
    return out_path


def build_report(results, out_dir="."):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    charts = _charts(results, out_dir)

    s = results["summary"]
    lines = [
        "BAYSIDE LIQUOR - WEEKLY SALES REPORT",
        f"Generated {datetime.now():%Y-%m-%d %H:%M}",
        f"Period: {s['start']:%m/%d/%Y} - {s['end']:%m/%d/%Y}",
        "=" * 60,
        "",
        f"  Gross revenue        ${s['gross_revenue']:>12,.2f}",
        f"  Transactions         {s['n_transactions']:>13,}",
        f"  Avg transaction      ${s['avg_transaction_value']:>12,.2f}",
        f"  Refunds              {s['refund_count']:>13,}  (${s['refund_value']:,.2f})",
        "",
        "REVENUE BY CATEGORY",
        "-" * 60,
    ]
    for cat, val in results["category_mix"].items():
        lines.append(f"  {cat:<12} ${val:>12,.2f}")
    lines += ["", "TOP 10 ITEMS", "-" * 60]
    for item, val in results["top_skus"].items():
        lines.append(f"  {item:<24} ${val:>12,.2f}")
    anom = results["anomalies"]
    lines += ["", f"ANOMALIES TO CHECK ({len(anom)})", "-" * 60]
    if anom.empty:
        lines.append("  none")
    for _, r in anom.head(20).iterrows():
        lines.append(f"  {r['date']:%m/%d %H:%M}  {r['item']:<22} "
                     f"${r['line_total']:>10,.2f}  ({r['x_normal']:.0f}x normal)")
    lines += ["", "Charts saved as PNG next to this PDF."]

    pdf = out_dir / f"report_{datetime.now():%Y-%m-%d}.pdf"
    _text_pdf(lines, pdf)
    return pdf, charts
