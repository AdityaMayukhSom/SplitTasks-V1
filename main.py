from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from repository.models import create_db_and_tables
from routes.currency import currency_router
from routes.user import user_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="SplitTasks", lifespan=lifespan)
app.include_router(currency_router, prefix="/currency")
app.include_router(user_router, prefix="/user")


def main():
    uvicorn.run(app="main:app", reload=True)


if __name__ == "__main__":
    main()
