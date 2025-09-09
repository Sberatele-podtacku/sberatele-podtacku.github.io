#!/usr/bin/env python3
"""
Retakes_New_Coasters.py

Same pipeline and folders as New_Coasters.py, but for RETAKES:
- Reads JPEGs from new_coaster/
- Writes BG-removed PNGs to recenter_nobg/
- Writes centered PNGs (2000x2000) to recenter_png/
- Writes TWO WEBPs to recenter_webp/:
    <basename>.webp           (full-size on canvas, Q=85)
    <basename>_thumb.webp     (thumbnail, THUMB_SIZE, Q=85)
- NO renaming to numeric IDs, NO moving into images/ or thumbs/, NO CSV updates.

You will manually replace the existing files later.
"""

import os
import numpy as np
from PIL import Image
from rembg import remove

# ─── CONFIG ───────────────────────────────────────────────────────────────
BASE_DIR         = r"C:\Users\ASUS GAMING\Documents\GitHub\Sberatele_Podtacku"
SOURCE_JPG       = os.path.join(BASE_DIR, "new_coaster")
REMOVE_BG_OUT    = os.path.join(BASE_DIR, "recenter_nobg")
RESIZED_OUT      = os.path.join(BASE_DIR, "recenter_png")
WEBP_RESIZED_DIR = os.path.join(BASE_DIR, "recenter_webp")

CANVAS_SIZE      = (2000, 2000)
ALPHA_THRESHOLD  = 5
THUMB_SIZE       = (300, 300)   # matches original script's thumbnail size
WEBP_QUALITY     = 85
# ──────────────────────────────────────────────────────────────────────────

os.makedirs(REMOVE_BG_OUT, exist_ok=True)
os.makedirs(RESIZED_OUT, exist_ok=True)
os.makedirs(WEBP_RESIZED_DIR, exist_ok=True)

def log(msg):
    print(msg, flush=True)

# ─── STEP 1: REMOVE BACKGROUND ────────────────────────────────────────────
files = [f for f in os.listdir(SOURCE_JPG) if f.lower().endswith(('.jpg','.jpeg'))]
total = len(files)
log(f"Found {total} JPG(s) in {SOURCE_JPG}")

for index, filename in enumerate(files, start=1):
    input_path = os.path.join(SOURCE_JPG, filename)
    output_path = os.path.join(REMOVE_BG_OUT, os.path.splitext(filename)[0] + '.png')

    try:
        with open(input_path, 'rb') as i, open(output_path, 'wb') as o:
            o.write(remove(i.read()))
        log(f"✅ BG Removed {index}/{total}: {filename}")
    except Exception as e:
        log(f"❌ Error with {filename}: {e}")

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
        ys, xs = np.nonzero(mask)
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
    log(f"✓ Resized + Centered: {fname}")

# ─── STEP 2.5: CONVERT RESIZED PNGs TO WEBP (Q85) + THUMBS ───────────────
converted = 0
for fname in os.listdir(RESIZED_OUT):
    if not fname.lower().endswith(".png"):
        continue

    input_path = os.path.join(RESIZED_OUT, fname)
    base = os.path.splitext(fname)[0]
    out_full  = os.path.join(WEBP_RESIZED_DIR, base + ".webp")
    out_thumb = os.path.join(WEBP_RESIZED_DIR, base + "_thumb.webp")

    try:
        img = Image.open(input_path).convert("RGBA")
        # full
        img.save(out_full, "WEBP", quality=WEBP_QUALITY, method=6)
        # thumb
        thumb = img.copy()
        thumb.thumbnail(THUMB_SIZE, Image.LANCZOS)
        thumb.save(out_thumb, "WEBP", quality=WEBP_QUALITY, method=6)

        converted += 1
        log(f"🔄 Saved: {out_full}  +  {out_thumb}")
    except Exception as e:
        log(f"❌ Failed to convert {fname} to WEBP: {e}")

log(f"Done. Converted {converted} file(s). Review files in {WEBP_RESIZED_DIR} and move/replace manually.")
