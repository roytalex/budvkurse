
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from api.deps import DB, get_current_user
from api.routes import auth, catalog, events, files, personal, users, locations, communications
from core.config import get_settings
from core.errors import AppError
from db.db import get_engine


@asynccontextmanager
async def lifespan(app):

    yield
    await get_engine().dispose()


app = FastAPI(title="Будь ВКурсе API", version="1.0.0",
              description="Города, школы, мероприятия и личные планы. Сначала войди через /auth/login, затем вставь access_token в Authorize.",
              lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins,
                   allow_credentials=False, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
                   allow_headers=["Authorization", "Content-Type"])


@app.exception_handler(AppError)
async def business_error(request: Request, exc: AppError):
    headers = {"WWW-Authenticate": "Bearer"} if exc.status == 401 else None
    return JSONResponse(status_code=exc.status, content={"detail": exc.detail}, headers=headers)


@app.exception_handler(IntegrityError)
async def database_conflict(request: Request, exc: IntegrityError):

    return JSONResponse(status_code=409, content={"detail": "Конфликт данных: запись уже существует или связана с другими данными"})


@app.get("/health", tags=["Проверка"], summary="Проверить доступность API и базы")
async def health(db: DB):
    await db.execute(text("SELECT 1"))
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api/v1")
for router in (users.router, catalog.router, events.router, personal.router, files.router, locations.router, communications.router):

    app.include_router(router, prefix="/api/v1", dependencies=[Depends(get_current_user)])



project_root = Path(__file__).resolve().parent.parent
for name in ("assets", "vendor"):
    directory = project_root / name
    if directory.is_dir():
        app.mount(f"/{name}", StaticFiles(directory=directory), name=name)
if (project_root / "frontend").is_dir():
    app.mount("/", StaticFiles(directory=project_root / "frontend", html=True), name="frontend")
