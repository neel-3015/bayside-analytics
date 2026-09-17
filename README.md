# Bayside Liquor — Retail Analytics Pipeline

Turns a raw POS export CSV into a weekly sales report a store owner can
read in 30 seconds: revenue by category, top SKUs, day-of-week patterns,
and an anomaly list that catches price-keying mistakes.

## Why
The owner's problem was "I don't know what's actually selling." This
project turns that vague question into a schema, a pipeline, and a report.

## Layout
```
data/incoming/   drop POS export CSVs here (gitignored — never real data)
src/ingest.py    load + validate + clean (bad dates, dupes, signed refunds)
src/analyze.py   pandas summaries + z-score anomaly detection
src/report.py    matplotlib charts + PDF report
src/main.py      one command: newest CSV in -> report out
reports/         generated PDF + chart PNGs (gitignored)
```

## Run
```
.venv/bin/python src/main.py
```

## Data note
Development used `pos_export_simulated.csv` — a synthetic dataset modeled
on retail liquor POS exports (weekday/weekend weighting, category mix,
~0.5% refunds, planted price-keying anomalies). Real store exports are
gitignored and never committed.
