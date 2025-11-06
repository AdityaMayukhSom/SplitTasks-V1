from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.repository.session import create_db_and_tables
from app.routes.security import security_router
from app.routes.user import user_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="SplitTasks",
    summary="split tasks and pay, all in one application",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory="public"))
app.include_router(user_router, prefix="/user")
app.include_router(security_router)
