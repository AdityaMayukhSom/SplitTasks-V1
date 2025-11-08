import pytest
from email_validator import EmailNotValidError
from phonenumbers.phonenumberutil import NumberParseException
from pwdlib import PasswordHash
from sqlmodel import Session

from app.repository.models import User
from app.utils.authentication import store_user, get_validated_username, MobileNotValidError

testdata_email = (
    ("tony.stark@avengers.com", "ILovePepperPotts"),
    ("thor.odinson@avengers.com", "JaneFosterOrMjolnir"),
)

testdata_mobile = (
    ("+44 20 3048 4377", "EnglandOhEngland$2000"),
    ("+91 98432 69621", "JaneFosterOrMjolnir"),
)


@pytest.mark.parametrize("username,password", testdata_email + testdata_mobile)
def test_store_user_username_only(username: str, password: str, session: Session):
    user_created = store_user(session, username=username, password=password)
    user_db = session.get(User, user_created.id)

    assert user_db.id == user_created.id

    if username.find("@") != -1:
        assert user_created.email == username
        assert user_db.email == username
    else:
        assert user_created.mobile == username
        assert user_db.mobile == username

    assert user_created.name is None
    assert user_db.name is None

    hasher = PasswordHash.recommended()
    assert hasher.verify(password, user_created.password_hash)
    assert hasher.verify(password, user_db.password_hash)

    assert user_created.enabled is True
    assert user_db.enabled is True

    assert user_created.dob is None
    assert user_db.dob is None


testdata_email_mobile = (
    ("tony.stark@avengers.com", "+44 20 3048 4377", "ILovePepperPotts"),
    ("thor.odinson@avengers.com", "+91 98432 69621", "JaneFosterOrMjolnir"),
)


@pytest.mark.parametrize("email,mobile,password", testdata_email_mobile)
def test_store_user_username_email_same(email: str, mobile: str, password: str, session: Session):
    with pytest.raises(Exception):
        store_user(session, username=email, email=email, password=password)


@pytest.mark.parametrize("email,mobile,password", testdata_email_mobile)
def test_store_user_username_mobile_same(email: str, mobile: str, password: str, session: Session):
    with pytest.raises(Exception):
        store_user(session, username=mobile, mobile=mobile, password=password)


@pytest.mark.parametrize("email,mobile,password", testdata_email_mobile)
def test_store_user_username_exclusion_email_mobile(email: str, mobile: str, password: str, session: Session):
    with pytest.raises(Exception):
        store_user(session, username='test-username', email=email, mobile=mobile, password=password)


@pytest.mark.parametrize("email,mobile,password", testdata_email_mobile)
def test_store_user_email_mobile_swap(email: str, mobile: str, password: str, session: Session):
    with pytest.raises(EmailNotValidError):
        store_user(session, email=mobile, mobile=email, password=password)


@pytest.mark.parametrize("email,mobile,password", testdata_email_mobile)
def test_store_user_email_invalid(email: str, mobile: str, password: str, session: Session):
    with pytest.raises(EmailNotValidError):
        store_user(session, email=mobile, mobile=mobile, password=password)


@pytest.mark.parametrize("email,mobile,password", testdata_email_mobile)
def test_store_user_mobile_invalid(email: str, mobile: str, password: str, session: Session):
    with pytest.raises(NumberParseException):
        store_user(session, email=email, mobile=email, password=password)


def test_store_user_no_username_email_mobile(session: Session):
    with pytest.raises(Exception):
        store_user(session, password="secret-password-123")


testdata_username_success = (
    ('+91 9765768920', 'mobile', '+91 97657 68920'),
    ('elon.musk@twitter.com', 'email', 'elon.musk@twitter.com'),
    (" Test.User@Twitter.COM ", "unknown", "test.user@twitter.com"),
    ("another@devstream.in", "email", "another@devstream.in"),
    ("9876543210", "unknown", "+91 98765 43210"),
    ("+7 4951234567", "mobile", "+7 495 123-45-67"),
    (None, "unknown", None)
)


@pytest.mark.parametrize("username,username_type,expected_output", testdata_username_success)
def test_username_validation_success(username: str, username_type, expected_output):
    result = get_validated_username(username, username_type=username_type)
    assert result == expected_output


testdata_username_failure = (
    (12345, "unknown", ValueError),
    ("invalid-email-format", "email", EmailNotValidError),
    ("+919765768920", "email", EmailNotValidError),
    ("invalid@.com", "unknown", EmailNotValidError),
    ("valid@tesla.com", "mobile", NumberParseException),
    ("12", "mobile", MobileNotValidError),
    ("45", "unknown", MobileNotValidError)
)


@pytest.mark.parametrize("username,username_type,expected_exception", testdata_username_failure)
def test_username_validation_failure(username: str, username_type, expected_exception):
    with pytest.raises(expected_exception):
        get_validated_username(username, username_type=username_type)
