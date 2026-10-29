from fastapi import FastAPI

from app.core.http.handlers import register_error_handlers


def create_app() -> FastAPI:
    app = FastAPI(title="Bright Path")
    register_error_handlers(app)
    return app


app = create_app()
