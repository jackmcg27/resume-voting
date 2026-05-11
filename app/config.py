import os
from pathlib import Path

PORT = int(os.environ.get("PORT", 8000))

ROOT = Path(__file__).parent.parent
UPLOAD_DIR = ROOT / "uploads"
STATIC_DIR = ROOT / "static"

UPLOAD_DIR.mkdir(exist_ok=True)
