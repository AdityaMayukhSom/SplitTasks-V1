from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel

from app.config.vars import get_db_vars
from app.repository.models import EngineDep, get_engine


def get_session(engine: EngineDep):
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def create_db_and_tables():
    engine = get_engine(get_db_vars())
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
