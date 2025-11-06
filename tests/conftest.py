import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# this is required as this file is first imported by pytest to configure the
# tests, hence automatically the app module is loaded, hence mentioning this
# sys.append only in conftest.py works for all the tests.
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from app.main import app
from app.config.vars import JWTVars, get_jwt_vars
from app.repository.session import get_session


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="jwt_vars")
def jwt_vars_fixture():
    jwt_random_256_bit_key = "b949e56300a94889c8c10371076c9adc60234ffd427d00514b7feafeb7b8f510"
    jwt_vars = JWTVars(
        JWT_SIGNING_ALGO="HS256",
        JWT_ISSUER="jwt-test-issuer",
        JWT_EXPIRY_MINUTES=30,
        JWT_SECRET_KEY=jwt_random_256_bit_key,
    )

    yield jwt_vars


@pytest.fixture(name="client")
def client_fixture(session: Session, jwt_vars: JWTVars):
    def get_session_override():
        return session

    def get_jwt_vars_override():
        return jwt_vars

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_jwt_vars] = get_jwt_vars_override

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()
