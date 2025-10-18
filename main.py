import os
import io
import csv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import imagehash

# -------- Config --------
PORT = int(os.getenv("PORT", "8080"))
USE_DB = os.getenv("USE_DB", "false").lower() == "true"

# Replace USERNAME[/REPO] with your GitHub Pages origin if you test from the site
ALLOWED_ORIGINS = [
    "https://USERNAME.github.io",
    "http://localhost:3000",
    "http://localhost:5173",
]

PHASH_CSV = "phashes.csv"  # must be present in the image

# -------- Helpers --------
def load_phashes(path: str):
    index = []
    if not os.path.exists(path):
        return index
    with open(path, encoding="utf-8") as fp:
        r = csv.DictReader(fp)
        for row in r:
            try:
                ph = imagehash.hex_to_hash(row["phash"])
                index.append({
                    "id": row.get("id") or row.get("name") or row.get("path"),
                    "path": row.get("path"),
                    "phash": ph,
                })
            except Exception:
                continue
    return index

def compute_phash_from_bytes(b: bytes):
    im = Image.open(io.BytesIO(b)).convert("RGB")
    return imagehash.phash(im)

def ham(a, b):
    return (a - b)

def csv_match(ph, top_k=5, threshold=18):  # looser default for initial tests
    scored = []
    for row in PHASH_INDEX:
        d = ham(ph, row["phash"])
        scored.append((int(d), row))
    scored.sort(key=lambda t: t[0])
    top = []
    for d, row in scored[:top_k]:
        if d <= threshold:
            top.append({
                "id": row["id"],
                "path": row["path"],
                "distance": d,
            })
    best = top[0]["distance"] if top else None
    return {
        "exists": bool(top),
        "best_distance": best,
        "threshold": threshold,
        "top_matches": top,
        "similar": top,
        "vector_error": None,
    }

# -------- Load data --------
PHASH_INDEX = load_phashes(PHASH_CSV)

# -------- Optional DB wiring (disabled unless USE_DB=true) --------
db = None
if USE_DB:
    # from your_db_module import init_db
    # db = init_db()
    pass

# -------- App and routes --------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/stats")
def stats():
    return {"phash_count": len(PHASH_INDEX)}

@app.post("/match")
async def match(file: UploadFile = File(...)):
    data = await file.read()
    ph = compute_phash_from_bytes(data)

    # If DB is ever enabled, branch here; for now CSV-only
    return csv_match(ph, top_k=5, threshold=18)
