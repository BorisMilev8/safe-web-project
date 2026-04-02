from fastapi import FastAPI
from fastapi. middleware.cors import CORSMiddleware
from pathlib import Path
import json

app = FastAPI(title="Safe Web Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "safe_web_results_real.json"

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/results")
def results():
    if not DATA_FILE.exists():
        return {
            "generated_at": None,
            "results": [],
            "message": "No results file found yet. Run safe_web_mvp.py locally first."
        }

    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)
