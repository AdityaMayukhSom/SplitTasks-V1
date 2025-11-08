import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.config.vars import JWTVars
from app.repository.types import id_to_str
from app.routes.security import create_access_token
from app.utils.authentication import store_user


@pytest.fixture(name="auth_token")
def auth_token_fixture(jwt_vars: JWTVars, session: Session):
    user = ("Otto Octavius", "otto@oscorp.com", "secret_password@123", "+49 30 901820")
    user_db = store_user(session, name=user[0], email=user[1], mobile=user[3], password=user[2])
    auth_token = create_access_token(id_to_str(user_db.id), jwt_vars)
    yield auth_token


def test_group_creation(auth_token: str, client: TestClient):
    payload = {"name": "Sinister 6", "currency": "USD"}
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.post("/group/create", json=payload, headers=headers)
    assert resp.status_code == status.HTTP_201_CREATED
