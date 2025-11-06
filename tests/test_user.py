import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from sqlmodel import Session

from app.repository.models import User
from app.repository.types import str_to_id

testdata = [
    ("Albert Einstein", "albert.e@princeton.edu", "PhotoElectric@1905", "+1 650-253-0000"),
    ("Walter White", "heisenberg@abqchem.com", "SayMyName!", "+91 650-253-0000"),
]


@pytest.mark.parametrize(["name", "email", "password", "mobile_number"], testdata)
def test_user_creation(name: str, email: str, password: str, mobile_number: str, client: TestClient, session: Session):
    payload = {
        "email": email,
        "full_name": name,
        "password": password,
        "mobile_number": mobile_number,
    }
    resp = client.post("/user/register", json=payload)

    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()

    assert data["email"] == email

    user_db = session.get(User, str_to_id(data["id"]))

    assert user_db is not None
    assert user_db.email == email
    assert user_db.full_name == name

    hasher = PasswordHash.recommended()
    assert hasher.verify(password, user_db.hashed_password)


@pytest.mark.parametrize(["name", "email", "password", "mobile_number"], testdata)
def test_duplicate_user_via_api(name: str, email: str, password: str, mobile_number: str, client: TestClient):
    payload = {
        "email": email,
        "full_name": name,
        "password": password,
        "mobile_number": mobile_number,
    }
    resp_suc = client.post("/user/register", json=payload)
    assert resp_suc.status_code == status.HTTP_201_CREATED
    data_suc = resp_suc.json()
    assert data_suc["email"] == email

    resp_err = client.post("/user/register", json=payload)
    assert resp_err.status_code == status.HTTP_409_CONFLICT
    data_err = resp_err.json()
    assert data_err["detail"]["error"] == "email_exists"
