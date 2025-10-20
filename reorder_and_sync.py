import csv
from pathlib import Path

# —— CONFIG ——
MAIN      = Path("images/")
CSV       = Path("metadata_updated.csv")
PAD_WIDTH = 5
# ————————

# 1) Gather existing IDs from the filename stems
fronts = sorted(MAIN.glob("*_front.webp"))
if not fronts:
    raise RuntimeError("No *_front.webp files found in Main_Collection")

old_ids = [p.stem[:-6] for p in fronts]   # e.g. "00001"
old_ints = sorted(int(x) for x in old_ids)
old_ids_sorted = [f"{i:0{PAD_WIDTH}d}" for i in old_ints]

# 2) Build compact mapping old → new (closing any gaps)
mapping = {
    old: f"{idx+1:0{PAD_WIDTH}d}"
    for idx, old in enumerate(old_ids_sorted)
}

# 3) Phase-1 rename:    X_front/back.webp  →  __tmp__X_front/back.webp
for old in old_ids_sorted:
    for side in ("front","back"):
        src = MAIN / f"{old}_{side}.webp"
        if src.exists():
            tmp = MAIN / f"__tmp__{old}_{side}.webp"
            src.rename(tmp)

# 4) Phase-2 rename:    __tmp__X_front/back.webp  →  Y_front/back.webp
for tmp in MAIN.glob("__tmp__*_*.webp"):  # correct glob, no escaped dot
    name = tmp.stem                  # "__tmp__00007_front"
    _, rest = name.split("__tmp__",1)
    old, side = rest.split("_",1)    # ["00007","front"]
    new_id = mapping.get(old)
    if new_id:
        dst = MAIN / f"{new_id}_{side}.webp"
        tmp.rename(dst)
    else:
        print(f"⚠️ No mapping for old ID {old}; leaving {tmp.name}")

# 5) Read your existing metadata.csv (try UTF-8, else Latin-1)
try:
    with open(CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
except UnicodeDecodeError:
    with open(CSV, newline="", encoding="latin-1") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

# 6) Build a dict of old metadata by old ID
rows_by_id = {r["id"]: r for r in rows}

# 7) Assemble new metadata rows in compact order
new_rows = []
for old in old_ids_sorted:
    if old in rows_by_id:
        r = rows_by_id[old]
        r["id"] = mapping[old]   # update to new ID
        new_rows.append(r)
    else:
        # should not happen unless you manually deleted a row
        print(f"⚠️ Metadata missing for old ID {old}; skipping")

# 8) Append any brand-new files (those not in the old CSV)
all_new_ids = set(mapping.values())
existing_new_ids = {r["id"] for r in new_rows}
for nid in sorted(all_new_ids):
    if nid not in existing_new_ids:
        new_rows.append({"id":nid, "description":"", "country":"", "letter":""})

# 9) Write out metadata_updated.csv for your review
out_csv = CSV.parent / "metadata_updated.csv"
with open(out_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(new_rows)

print(f"✅ Renamed {len(mapping)} coaster pairs in {MAIN}")
print(f"✅ Wrote updated metadata to {out_csv}")

# 10) Cleanup any stray tmp files (just in case)
for tmp in MAIN.glob("__tmp__*_*.webp"):
    print(f"🧹 Removing leftover {tmp.name}")
    tmp.unlink()
print("✅ Cleanup complete.")
