#!/usr/bin/env python3
import csv, json
from pathlib import Path

# === Automatically resolve to the folder this script lives in ===
BASE_DIR   = Path(__file__).resolve().parent
CSV_PATH   = BASE_DIR / "metadata_updated.csv"
JSON_PATH  = BASE_DIR / "metadata.json"

if not CSV_PATH.exists():
    print(f"❌ Cannot find {CSV_PATH}; make sure this script lives alongside your metadata_updated.csv")
    exit(1)

# 1) Read the CSV
with CSV_PATH.open(newline="", encoding="cp1252") as f:
    reader = csv.DictReader(f)
    data   = list(reader)

# (Optional) clean up each record here if you like:
# for r in data:
#     r["id"]          = r["id"].strip()
#     r["description"] = r["description"].strip()
#     r["letter"]      = r["letter"].strip().upper()

# 2) Write the JSON
with JSON_PATH.open("w", encoding="utf8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Exported {len(data)} records → {JSON_PATH}")
