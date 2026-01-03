import os
import re
import numpy as np
import pandas as pd
from PIL import Image
from rembg import remove

# ─── CONFIG ───────────────────────────────────────────────────────────────
BASE_DIR         = r"C:\Users\ASUS GAMING\Documents\GitHub\Sberatele_Podtacku"
SOURCE_JPG       = os.path.join(BASE_DIR, "new_coaster")
REMOVE_BG_OUT    = os.path.join(BASE_DIR, "recenter_nobg")
RESIZED_OUT      = os.path.join(BASE_DIR, "recenter_png")
WEBP_RESIZED_DIR = os.path.join(BASE_DIR, "recenter_webp")
IMAGES_DIR       = os.path.join(BASE_DIR, "images")
THUMBS_DIR       = os.path.join(IMAGES_DIR, "thumbs")
METADATA_CSV     = os.path.join(BASE_DIR, "metadata_updated.csv")

CANVAS_SIZE      = (2000, 2000)
ALPHA_THRESHOLD  = 5
THUMB_SIZE       = (300, 300)
WEBP_QUALITY     = 85
# ──────────────────────────────────────────────────────────────────────────

os.makedirs(REMOVE_BG_OUT, exist_ok=True)
os.makedirs(RESIZED_OUT, exist_ok=True)
os.makedirs(WEBP_RESIZED_DIR, exist_ok=True)
os.makedirs(THUMBS_DIR, exist_ok=True)

# ─── STEP 1: REMOVE BACKGROUND ────────────────────────────────────────────
files = [f for f in os.listdir(SOURCE_JPG) if f.lower().endswith('.jpg')]
total = len(files)

for index, filename in enumerate(files, start=1):
    input_path = os.path.join(SOURCE_JPG, filename)
    output_path = os.path.join(REMOVE_BG_OUT, os.path.splitext(filename)[0] + '.png')

    try:
        with open(input_path, 'rb') as i:
            with open(output_path, 'wb') as o:
                o.write(remove(i.read()))
        print(f"✅ BG Removed {index}/{total}: {filename}")
    except Exception as e:
        print(f"❌ Error with {filename}: {e}")

# ─── STEP 2: RESIZE AND CENTER ON TRANSPARENT CANVAS ─────────────────────
for fname in os.listdir(REMOVE_BG_OUT):
    if not fname.lower().endswith(".png"):
        continue

    path_in = os.path.join(REMOVE_BG_OUT, fname)
    path_out = os.path.join(RESIZED_OUT, fname)

    img = Image.open(path_in).convert("RGBA")
    alpha = img.getchannel("A")
    mask = np.array(alpha) > ALPHA_THRESHOLD

    if not mask.any():
        cropped = img
    else:
        ys, xs = mask.nonzero()
        bbox = (xs.min(), ys.min(), xs.max()+1, ys.max()+1)
        cropped = img.crop(bbox)

    scale = min(CANVAS_SIZE[0] / cropped.width, CANVAS_SIZE[1] / cropped.height)
    new_size = (int(cropped.width * scale), int(cropped.height * scale))
    resized = cropped.resize(new_size, Image.LANCZOS)

    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    x = (CANVAS_SIZE[0] - resized.width) // 2
    y = (CANVAS_SIZE[1] - resized.height) // 2
    canvas.paste(resized, (x, y), resized)

    canvas.save(path_out, "PNG", optimize=True)
    print(f"✓ Resized + Centered: {fname}")

# ─── STEP 2.5: CONVERT RESIZED PNGs TO WEBP (Q85) ─────────────────────────
webp_files = []

for fname in os.listdir(RESIZED_OUT):
    if not fname.lower().endswith(".png"):
        continue

    input_path = os.path.join(RESIZED_OUT, fname)
    output_path = os.path.join(WEBP_RESIZED_DIR, os.path.splitext(fname)[0] + ".webp")

    try:
        img = Image.open(input_path).convert("RGBA")
        img.save(output_path, "WEBP", quality=WEBP_QUALITY, method=6)
        webp_files.append(os.path.basename(output_path))
        print(f"🔄 Converted to WEBP: {output_path}")
    except Exception as e:
        print(f"❌ Failed to convert {fname} to WEBP: {e}")

# ─── STEP 3: RENAME, MOVE TO images/, CREATE THUMBS ───────────────────────
pattern = re.compile(r"(\d+)_([a-z]+)\.(jpg|png|webp)$", re.IGNORECASE)
existing_numbers = [
    int(match.group(1))
    for f in os.listdir(IMAGES_DIR)
    if (match := pattern.match(f))
]
next_num = max(existing_numbers, default=0) + 1

recenter_files = sorted([f for f in os.listdir(WEBP_RESIZED_DIR) if f.lower().endswith(".webp")])
if len(recenter_files) % 2 != 0:
    raise ValueError("❌ Number of WEBPs is not even. Expected front/back pairs.")

new_ids = []

for i in range(0, len(recenter_files), 2):
    front_file = recenter_files[i]
    back_file = recenter_files[i + 1]

    for suffix, src_file in zip(["front", "back"], [front_file, back_file]):
        new_base = f"{next_num:05d}_{suffix}"
        src_path = os.path.join(WEBP_RESIZED_DIR, src_file)
        final_path = os.path.join(IMAGES_DIR, new_base + ".webp")
        thumb_path = os.path.join(THUMBS_DIR, new_base + ".webp")

        os.rename(src_path, final_path)
        print(f"✓ Moved: {src_file} → {final_path}")

        with Image.open(final_path) as img:
            thumb = img.copy()
            thumb.thumbnail(THUMB_SIZE, Image.LANCZOS)
            thumb.save(thumb_path, "WEBP", quality=85)
            print(f"✓ Thumb: {thumb_path}")

    new_ids.append(f"{next_num:05d}")
    next_num += 1

# ─── STEP 4: UPDATE metadata_updated.csv SAFELY ──────────────────────────
try:
    df_existing = pd.read_csv(METADATA_CSV, encoding='cp1252')
    df_existing.columns = df_existing.columns.str.strip().str.lower()
    existing_ids = set(df_existing["id"].astype(str))
except FileNotFoundError:
    df_existing = pd.DataFrame(columns=["id"])
    existing_ids = set()

ids_to_add = sorted(set(new_ids) - existing_ids)
new_df = pd.DataFrame({"id": ids_to_add})

if ids_to_add:
    df_final = pd.concat([df_existing, new_df], ignore_index=True)
    try:
        df_final.to_csv(METADATA_CSV, index=False, encoding='utf-8-sig')
        print(f"📄 metadata_updated.csv updated with {len(ids_to_add)} new IDs.")
    except PermissionError:
        print("❌ ERROR: Cannot write to metadata_updated.csv — is it open in Excel?")
else:
    print("ℹ️ No new IDs to add — CSV already up to date.")
