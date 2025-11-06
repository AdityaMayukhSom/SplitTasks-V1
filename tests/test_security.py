from datetime import datetime, timezone

import jwt
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from sqlmodel import Session

from app.config.vars import JWTVars
from app.repository.models import User

auth_form_headers = {"content-type": "application/x-www-form-urlencoded"}

testdata = [
    ("Tony Stark", "tony.stark@avengers.com", "ILovePepperPotts", "+61 6502530000"),
    ("Thor Odinson", "thor.odinson@avengers.com", "JaneFosterOrMjolnir", "+91 6502530000"),
]


def store_user(name: str, email: str, password: str, mobile_number: str, enabled: bool, session: Session):
    hasher = PasswordHash.recommended()
    user_db = User(
        full_name=name,
        email=email,
        hashed_password=hasher.hash(password),
        enabled=enabled,
        mobile_number=mobile_number,
    )
    session.add(user_db)
    session.commit()
    session.refresh(user_db)
    return user_db


@pytest.mark.parametrize(["name", "email", "password", "mobile_number"], testdata)
def test_token_generation_authorized_access(
    name: str, email: str, password: str, mobile_number: str, client: TestClient, session: Session, jwt_vars: JWTVars
):
    user_db = store_user(name, email, password, mobile_number, True, session)

    # we need to discard microsecond as jwt uses unix timestamps which uses seconds as least count
    before_token_time = datetime.now(tz=timezone.utc).replace(microsecond=0)
    payload = {"username": email, "password": password}
    resp = client.post("/token", data=payload, headers=auth_form_headers)
    after_token_time = datetime.now(tz=timezone.utc)

    data = resp.json()

    assert resp.status_code == status.HTTP_200_OK
    assert resp.headers.get("cache-control") == "no-store"
    assert data["token_type"] == "Bearer"

    token = data["access_token"]
    assert token is not None

    jwt_payload = jwt.decode(token, jwt_vars.secret_key, algorithms=[jwt_vars.signing_algo])

    assert jwt_payload.get("iss") == jwt_vars.issuer
    assert jwt_payload.get("sub") == str(user_db.id)

    iat_datetime = datetime.fromtimestamp(jwt_payload.get("iat"), timezone.utc)
    assert before_token_time <= iat_datetime
    assert iat_datetime <= after_token_time


@pytest.mark.parametrize(["name", "email", "password", "mobile_number"], testdata)
def test_token_generation_user_does_not_exist(
    name: str, email: str, password: str, mobile_number: str, client: TestClient, session: Session, jwt_vars: JWTVars
):
    payload = {"username": email, "password": password}
    resp = client.post("/token", data=payload, headers=auth_form_headers)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize(["name", "email", "password", "mobile_number"], testdata)
def test_token_generation_user_exists_wrong_password(
    name: str, email: str, password: str, mobile_number: str, client: TestClient, session: Session, jwt_vars: JWTVars
):
    store_user(name, email, password, mobile_number, True, session)
    payload = {"username": email, "password": "wrong-password"}
    resp = client.post("/token", data=payload, headers=auth_form_headers)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize(["name", "email", "password", "mobile_number"], testdata)
def test_token_generation_user_exists_but_disabled(
    name: str, email: str, password: str, mobile_number: str, client: TestClient, session: Session, jwt_vars: JWTVars
):
    store_user(name, email, password, mobile_number, False, session)
    payload = {"username": email, "password": password}
    resp = client.post("/token", data=payload, headers=auth_form_headers)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
