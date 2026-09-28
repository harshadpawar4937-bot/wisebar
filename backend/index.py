import sys
from pathlib import Path

from fastapi import FastAPI

sys.path.insert(0, str(Path(__file__).resolve().parent))

app = FastAPI(title="WISEBAR API", version="1.0.0")

try:
    from app.main import app as shop_app

    app = shop_app
except Exception as exc:
    startup_error = f"{type(exc).__name__}: {exc}"

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    def import_failed(path: str = ""):
        return {"ok": False, "service": "wisebar", "error": startup_error, "path": path}
