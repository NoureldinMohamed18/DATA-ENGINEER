import sys
from pathlib import Path
import uvicorn

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.config import load_settings

if __name__ == "__main__":
    settings = load_settings()
    uvicorn.run("src.serve.api:app", host=settings["api"]["host"], port=settings["api"]["port"])
