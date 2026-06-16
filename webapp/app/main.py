"""FastAPI app local: serve a UI e orquestra a API remota."""
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import settings
from app.jobs.manager import JobManager
from app.jobs.runner import JobRunner
from app.jobs.store import JobStore
from app.myp_client import MypClient
from app.status_tracker import StatusTracker
from app.routers import inventory_api, jobs_api, pages, single_api, util_api

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = httpx.AsyncClient(timeout=settings.http_timeout_seconds)
    store = JobStore(settings.db_file)
    store.init()
    mypclient = MypClient(client, settings.base_url)
    tracker = StatusTracker(settings.dynamo_table, settings.aws_region)
    runner = JobRunner(store, mypclient, tracker, settings)
    manager = JobManager(store, runner)

    app.state.client = client
    app.state.store = store
    app.state.mypclient = mypclient
    app.state.manager = manager

    await manager.resume_active()
    try:
        yield
    finally:
        await client.aclose()


app = FastAPI(title="MypCards — Gestor de Estoque (local)", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(util_api.router)
app.include_router(jobs_api.router)
app.include_router(single_api.router)
app.include_router(inventory_api.router)
app.include_router(pages.router)
