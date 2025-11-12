import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from sqlmodel import Session

from app.repository.models import User
from app.repository.types import str_to_id


def test_create_user_with_name_and_password(client: TestClient):
    # The expected value is 422, not 400 as this is not only a bad request,
    # but the payload is not processable by the backend, hence 422 is expected.
    payload = {
        "name": "Walter White",
        "password": "ABCD123456",
    }
    resp = client.post("/user/register", json=payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_user_with_name_only(client: TestClient):
    payload = {"name": "Walter White"}
    resp = client.post("/user/register", json=payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_user_with_password_only(client: TestClient):
    payload = {"password": "ABCD1234"}
    resp = client.post("/user/register", json=payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_user_with_email_only(client: TestClient):
    payload = {"email": "elon.musk@tesla.com"}
    resp = client.post("/user/register", json=payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_user_with_mobile_only(client: TestClient):
    payload = {"mobile": "+91 98432 69621"}
    resp = client.post("/user/register", json=payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize("email", ("heisenberg1234", "abc@@world.org", "7890"))
def test_create_user_with_email_invalid(email: str, client: TestClient):
    payload = {"email": email, "password": "secret-password@123"}
    resp = client.post("/user/register", json=payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize("mobile", ("heisenberg1234", "abc@@world.org", "7890"))
def test_create_user_with_mobile_invalid(mobile: str, client: TestClient):
    payload = {"mobile": mobile, "password": "changeit@9876"}
    resp = client.post("/user/register", json=payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_user_with_name_email_mobile(client: TestClient, session: Session):
    payload = {
        "email": "heisenberg@chemistry.org",
        "name": "Walter White",
        "password": "SayMyName!72",
        "mobile": "+91 65025 30000",
    }
    resp = client.post("/user/register", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()

    user_db = session.get(User, str_to_id(data["id"]))

    assert user_db is not None
    assert user_db.email == payload["email"]
    assert user_db.name == payload["name"]
    assert user_db.mobile == payload["mobile"]

    hasher = PasswordHash.recommended()
    assert hasher.verify("SayMyName!72", user_db.password_hash)


def test_create_user_with_email_mobile(client: TestClient, session: Session):
    payload = {
        "email": "heisenberg@chemistry.org",
        "password": "SayMyName!72",
        "mobile": "+91 65025 30000",
    }
    resp = client.post("/user/register", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()

    user_db = session.get(User, str_to_id(data["id"]))

    assert user_db is not None
    assert user_db.email == payload["email"]
    assert user_db.name is None
    assert user_db.mobile == payload["mobile"]


def test_create_user_with_mobile_valid(client: TestClient, session: Session):
    payload = {
        "mobile": "+353 21 234 5678",
        "password": "SayMyName!72",
    }
    resp = client.post("/user/register", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()

    user_db = session.get(User, str_to_id(data["id"]))

    assert user_db is not None
    assert user_db.email is None
    assert user_db.name is None
    assert user_db.mobile == payload["mobile"]


def test_user_obj_creation():
    user_db = User(
        name="Tony Stark",
        email="tony@stark.industries",
        mobile="+91 98654 89765",
        password_hash="super-hashed-password@123",
        enabled=False,
    )
    assert user_db.name == "Tony Stark"
    assert user_db.email == "tony@stark.industries"
    assert user_db.mobile == "+91 98654 89765"
    assert user_db.password_hash == "super-hashed-password@123"
    assert not user_db.enabled


def test_create_user_with_email_valid(client: TestClient, session: Session):
    payload = {
        "email": "heisenberg@chemistry.org",
        "password": "SayMyName!72",
    }
    resp = client.post("/user/register", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()

    user_db = session.get(User, str_to_id(data["id"]))

    assert user_db is not None
    assert user_db.email == payload["email"]
    assert user_db.name is None
    assert user_db.mobile is None


def test_duplicate_user_create(session: Session, client: TestClient):
    payload = {
        "name": "Walter White",
        "email": "heisenberg@chemistry.org",
        "password": "SayMyName!72",
        "mobile": "+91 65025 30000",
    }
    resp_suc = client.post("/user/register", json=payload)
    assert resp_suc.status_code == status.HTTP_201_CREATED

    resp_err = client.post("/user/register", json=payload)
    assert resp_err.status_code == status.HTTP_409_CONFLICT
    data_err = resp_err.json()
    assert data_err["code"] == "email_exists"

    payload["email"] = "new_email_same_mobile@abc.com"

    resp_err = client.post("/user/register", json=payload)
    assert resp_err.status_code == status.HTTP_409_CONFLICT
    data_err = resp_err.json()
    assert data_err["code"] == "mobile_exists"

    payload["mobile"] = "+91 95647 69690"

    resp_suc = client.post("/user/register", json=payload)
    assert resp_suc.status_code == status.HTTP_201_CREATED
