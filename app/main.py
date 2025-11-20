from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.errors.conf import handler_dict
from app.middleware import ProcessTimeMiddleware

# from app.repository.session import create_db_and_tables
from app.routes.expense import expense_router
from app.routes.group import group_router
from app.routes.invitation import invitation_router
from app.routes.security import security_router
from app.routes.user import user_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    # create_db_and_tables()
    yield


app = FastAPI(
    title="SplitTasks",
    summary="split tasks and pay, all in one application",
    lifespan=lifespan,
    exception_handlers=handler_dict,
)
app.mount("/static", StaticFiles(directory="public"))
app.add_middleware(ProcessTimeMiddleware)
app.include_router(user_router, prefix="/user")
app.include_router(group_router, prefix="/group")
app.include_router(invitation_router, prefix="/invitation")
app.include_router(expense_router, prefix="/expense")
app.include_router(security_router)
