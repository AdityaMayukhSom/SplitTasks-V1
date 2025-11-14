from datetime import datetime, timezone

import jwt
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.config.vars import JWTVars
from app.repository.types import id_to_str
from app.utils.authentication import store_user

auth_form_headers = {"content-type": "application/x-www-form-urlencoded"}

testdata = (
    ("tony.stark@avengers.com", "ILovePepperPotts"),
    ("thor.odinson@avengers.com", "JaneFosterOrMjolnir"),
    ("+44 2030484377", "EnglandOhEngland$2000"),
    ("+91 9843269621", "JaneFosterOrMjolnir"),
)


@pytest.mark.parametrize("username,password", testdata)
def test_security_token_generation(
    username: str, password: str, client: TestClient, session: Session, jwt_vars: JWTVars
):
    user_db = store_user(session, username=username, password=password)

    # we need to discard microsecond as jwt uses unix timestamps which uses seconds as least count
    before_token_time = datetime.now(tz=timezone.utc).replace(microsecond=0)
    payload = {"username": username, "password": password}
    resp = client.post("/token", data=payload, headers=auth_form_headers)
    after_token_time = datetime.now(tz=timezone.utc)

    data = resp.json()

    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.headers.get("cache-control") == "no-store"
    assert data["token_type"] == "Bearer"

    token = data["access_token"]
    assert token is not None

    jwt_payload = jwt.decode(token, jwt_vars.secret_key, algorithms=[jwt_vars.signing_algo])

    assert jwt_payload.get("iss") == jwt_vars.issuer
    assert jwt_payload.get("sub") == id_to_str(user_db.id)

    iat_datetime = datetime.fromtimestamp(jwt_payload.get("iat"), timezone.utc)
    assert before_token_time <= iat_datetime
    assert iat_datetime <= after_token_time


@pytest.mark.parametrize("username,password", testdata)
def test_security_user_does_not_exist(
    username: str, password: str, client: TestClient, session: Session, jwt_vars: JWTVars
):
    payload = {"username": username, "password": password}
    resp = client.post("/token", data=payload, headers=auth_form_headers)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("username,password", testdata)
def test_security_user_exists_wrong_password(
    username: str, password: str, client: TestClient, session: Session, jwt_vars: JWTVars
):
    store_user(session, username=username, password=password)
    payload = {"username": username, "password": "wrong-password-1234"}
    resp = client.post("/token", data=payload, headers=auth_form_headers)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("username,password", testdata)
def test_security_user_exists_disabled(
    username: str, password: str, client: TestClient, session: Session, jwt_vars: JWTVars
):
    store_user(session, username=username, password=password, enabled=False)
    payload = {"username": username, "password": password}
    resp = client.post("/token", data=payload, headers=auth_form_headers)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
