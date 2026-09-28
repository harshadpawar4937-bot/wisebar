try:
    from app.main import app
except Exception as exc:
    from fastapi import FastAPI

    app = FastAPI()
    detail = f"{type(exc).__name__}: {exc}"

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    def import_failed(path: str = ""):
        return {"ok": False, "error": detail}
