# hash_all.py
import os, csv
from PIL import Image, ImageOps
import imagehash

# Point to your images folder (Windows raw string)
IMAGE_DIR = r"C:\Users\ASUS GAMING\Documents\GitHub\Sberatele_Podtacku\images"
OUTPUT_CSV = "phashes.csv"

def normalize(pil_img: Image.Image) -> Image.Image:
    """
    Basic normalization to make hashes more robust to lighting/background:
    - Convert to grayscale
    - Resize to a stable working size before hashing
    """
    g = ImageOps.grayscale(pil_img)
    g = g.resize((512, 512), Image.LANCZOS)
    return g

rows = []
supported = (".jpg", ".jpeg", ".png", ".webp")
for root, _, files in os.walk(IMAGE_DIR):
    for f in files:
        if f.lower().endswith(supported):
            path = os.path.join(root, f)
            try:
                with Image.open(path) as im:
                    img = im.convert("RGB")
                g = normalize(img)
                ph = imagehash.phash(g, hash_size=8)      # 64-bit pHash
                wh = imagehash.whash(g, hash_size=8)      # 64-bit wavelet hash
                rows.append({
                    "path": path.replace("\\", "/"),
                    "phash": str(ph),
                    "whash": str(wh)
                })
            except Exception as e:
                print("Skip:", path, e)

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as fp:
    w = csv.DictWriter(fp, fieldnames=["path","phash","whash"])
    w.writeheader()
    w.writerows(rows)

print(f"Wrote {len(rows)} hashes to {OUTPUT_CSV}")
