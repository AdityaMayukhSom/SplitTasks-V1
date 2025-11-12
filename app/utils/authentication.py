import logging
from typing import Literal, overload

from email_validator import validate_email
from phonenumbers import PhoneNumberFormat, format_number, parse as pn_parse
from phonenumbers.phonenumberutil import is_valid_number
from pwdlib import PasswordHash
from sqlmodel import Session, col, select

from app.repository.models import User


class MobileNotValidError(Exception):
    pass


class UserDoesNotExistError(Exception):
    pass


class InvalidPasswordError(Exception):
    pass


UsernameType = Literal["unknown", "email", "mobile"]


@overload
def get_validated_username(username: None, *, username_type: UsernameType = "unknown") -> None: ...
@overload
def get_validated_username(username: str, *, username_type: UsernameType = "unknown") -> str: ...
def get_validated_username(username: str | None, *, username_type: UsernameType = "unknown"):
    if username is None:
        return username

    # always store usernames (especially emails) in lower case so that duplicates
    # that only differ in case throws not unique error when storing in database
    # although the local part of the email can be case-sensitive, no widely used
    # email provider uses case-sensitive comparison for local part, so use lower case
    # https://stackoverflow.com/questions/9807909/are-email-addresses-case-sensitive
    username_lower: str = username.strip().lower()
    if len(username_lower) == 0:
        raise ValueError("username cannot be empty")

    if username_type == "unknown":
        username_type = "email" if username_lower.find("@") != -1 else "mobile"

    if username_type == "email":
        email_obj = validate_email(username_lower)
        return email_obj.normalized
    else:
        mobile_obj = pn_parse(username_lower, "IN")
        if not is_valid_number(mobile_obj):
            raise MobileNotValidError("given mobile is not valid")
        mobile_norm = str(format_number(mobile_obj, PhoneNumberFormat.INTERNATIONAL))
        return mobile_norm


def store_user(
    session: Session,
    *,
    username: str | None = None,
    name: str | None = None,
    email: str | None = None,
    mobile: str | None = None,
    password: str,
    enabled: bool = True,
) -> User:
    """
    Creates and stores a new user record.

    The primary identifier (username, email, or mobile) must be provided
    in a mutually exclusive fashion to avoid ambiguity.

    :param session: The database session.
    :param username: The primary identifier (email or mobile number). If provided,
                     'email' and 'mobile' kwargs must be None.
    :param name: The user's full name.
    :param email: The user's email address. Must be None if 'username' is provided.
    :param mobile: The user's mobile number. Must be None if 'username' is provided.
    :param password: The plain-text password to be hashed and stored.
    :param enabled: Initial active status of the user account. Defaults to True.
    :raises ValueError: If multiple conflicting identifier parameters (username
                        combined with email/mobile) are provided.
    :return: The newly created User object.
    """
    if username is None and email is None and mobile is None:
        raise ValueError("username, email and mobile cannot be None together")

    if username is not None and (email is not None or mobile is not None):
        raise ValueError("either pass username or use email and mobile as kwargs")

    # It is possible that mobile which does not contain @ symbol is still an invalid one,
    # This is_mobile check is done for very basic segregation purpose, the mobile number
    # will be validated in the get_validated_username function which is called before storing
    # the user into the database, thus we make sure that no invalid email or mobile number
    # is stored into the database.
    username_is_mobile = username is not None and username.find("@") == -1
    username_is_email = username is not None and username.find("@") != -1

    if username_is_email and email is None:
        # here email is None before assignment
        logging.info("username provided, contains `at` symbol and email not provided")
        email = username

    if username_is_mobile and mobile is None:
        # here mobile is None before assignment
        logging.info("username provided, does not contains `at` symbol and mobile not provided")
        mobile = username

    val_email = get_validated_username(email, username_type="email")
    val_mobile = get_validated_username(mobile, username_type="mobile")

    hasher = PasswordHash.recommended()
    pw_hash = hasher.hash(password)

    user_db = User(name=name, email=val_email, mobile=val_mobile, password_hash=pw_hash, enabled=enabled)

    session.add(user_db)
    session.commit()
    session.refresh(user_db)

    return user_db


def authenticate_user(username: str, password: str, session: Session) -> User:
    username_parsed = get_validated_username(username)
    if username.find("@") != -1:
        logging.info("trying to authenticate using email")
        user_stmt = select(User).where(col(User.email) == username_parsed)
    else:
        logging.info("trying to authenticate using mobile")
        user_stmt = select(User).where(col(User.mobile) == username_parsed)

    user = session.exec(user_stmt).one_or_none()
    if user is None:
        raise UserDoesNotExistError("no user exists with given username", username)
    hasher = PasswordHash.recommended()
    if not hasher.verify(password, user.password_hash):
        raise InvalidPasswordError("invalid password provided")
    return user
