import pytest
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from sqlmodel import Session

from app.repository.models import User
from app.routes.user import UserRegister

testdata = [("Otto Octavius", "otto.octavius@gmail.com", "spiderman")]


@pytest.mark.parametrize(["name", "email", "password"], testdata)
def test_user_creation(name: str, email: str, password: str, client: TestClient, session: Session):
    user_register = UserRegister(email=email, full_name=name, password=password)
    resp = client.post("/user/register", json=jsonable_encoder(user_register))

    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()

    assert data["email"] == user_register.email

    user_db = session.get(User, data["id"])

    assert user_db is not None
    assert user_db.email == user_register.email
    assert user_db.full_name == user_register.full_name

    hasher = PasswordHash.recommended()
    assert hasher.verify(user_register.password, user_db.hashed_password)
