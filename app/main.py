from fastapi import FastAPI

from app.core.http.handlers import register_error_handlers
from app.schedule.router import router as schedule_router


def create_app() -> FastAPI:
    app = FastAPI(title="Bright Path")
    register_error_handlers(app)
    app.include_router(schedule_router)
    return app


app = create_app()
