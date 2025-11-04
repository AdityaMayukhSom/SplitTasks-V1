import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from sqlmodel import Session

from app.repository.models import User
from app.routes.user import UserRegister

testdata = [
    ("Albert Einstein", "albert.e@princeton.edu", "PhotoElectric@1905"),
    ("Walter White", "heisenberg@abqchem.com", "SayMyName!"),
]


@pytest.mark.parametrize(["name", "email", "password"], testdata)
def test_user_creation(name: str, email: str, password: str, client: TestClient, session: Session):
    user_register = UserRegister(email=email, full_name=name, password=password)
    resp = client.post("/user/register", json=user_register.model_dump())

    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()

    assert data["email"] == user_register.email

    user_db = session.get(User, data["id"])

    assert user_db is not None
    assert user_db.email == user_register.email
    assert user_db.full_name == user_register.full_name

    hasher = PasswordHash.recommended()
    assert hasher.verify(user_register.password, user_db.hashed_password)


@pytest.mark.parametrize(["name", "email", "password"], testdata)
def test_duplicate_user_via_api(name: str, email: str, password: str, client: TestClient, session: Session):
    user_register = UserRegister(email=email, full_name=name, password=password)
    payload = user_register.model_dump()

    resp_suc = client.post("/user/register", json=payload)
    assert resp_suc.status_code == status.HTTP_201_CREATED
    data_suc = resp_suc.json()
    assert data_suc["email"] == email

    resp_err = client.post("/user/register", json=payload)
    assert resp_err.status_code == status.HTTP_409_CONFLICT
    data_err = resp_err.json()
    assert data_err["detail"]["error"] == "duplicate_email"
