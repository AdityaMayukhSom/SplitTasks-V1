from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Literal

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.responses import JSONResponse

from app.config.vars import JWTVars, JWTVarsDep
from app.repository.models import User
from app.repository.session import SessionDep
from app.repository.types import id_to_str, str_to_id
from app.routes.base_payload import BaseError, BasePayload
from app.utils.authentication import authenticate_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=True)
OAuth2SchemeDep = Annotated[str, Depends(oauth2_scheme)]


class TokenPayload(BasePayload):
    access_token: str
    token_type: str
    expires_in: int


class OAuthError(
    BaseError[
        Literal[
            "invalid_request",
            "invalid_client",
            "invalid_grant",
            "invalid_scope",
            "unauthorized_client",
            "unsupported_grant_type",
        ]
    ]
):
    pass


security_router = APIRouter()


def create_access_token(subject: str, jwt_vars: JWTVars) -> str:
    current_time = datetime.now(tz=timezone.utc)
    expiry_delta = timedelta(minutes=jwt_vars.expiry_minutes)
    expiry_time = current_time + expiry_delta
    payload = {
        # JWT subject has to be a string
        "sub": subject,
        "iat": current_time,
        "exp": expiry_time,
        "iss": jwt_vars.issuer,
    }
    encoded_jwt = jwt.encode(payload, jwt_vars.secret_key, algorithm=jwt_vars.signing_algo)
    return encoded_jwt


@security_router.post(
    "/token",
    response_model=TokenPayload,
    response_class=JSONResponse,
    tags=["security"],
    description="if the user account is disabled, no access token will be granted.",
)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
    jwt_vars: JWTVarsDep,
):
    try:
        user = authenticate_user(form_data.username, form_data.password, session)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=OAuthError(
                error="invalid_client",
                error_description="invalid client credentials",
            ).model_dump(),
        )

    if not user.enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=OAuthError(
                error="invalid_grant",
                error_description="user account is disabled, contact administrator",
            ).model_dump(),
        )

    access_token = create_access_token(id_to_str(user.id), jwt_vars)

    payload = TokenPayload(
        access_token=access_token,
        token_type="Bearer",
        expires_in=jwt_vars.expiry_minutes * 60,
    )

    return JSONResponse(
        content=payload.model_dump(mode="json"),
        status_code=status.HTTP_200_OK,
        headers={"cache-control": "no-store"},
    )


def get_current_user(token: OAuth2SchemeDep, jwt_vars: JWTVarsDep, session: SessionDep):
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            key=jwt_vars.secret_key,
            algorithms=[jwt_vars.signing_algo],
            issuer=jwt_vars.issuer,
            options={"require": ["sub", "exp", "iat", "iss"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=OAuthError(
                error="invalid_grant",
                error_description="jwt token expired, issue a new token",
            ).model_dump(),
            headers={"www-authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=OAuthError(
                error="invalid_request",
                error_description="invalid jwt token, could not proceed",
            ).model_dump(),
            headers={"www-authenticate": "Bearer"},
        )

    # JWT subject has to be a string
    jwt_subject: str | None = payload.get("sub")

    if jwt_subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=OAuthError(
                error="invalid_client",
                error_description="jwt subject not present in token",
            ).model_dump(),
            headers={"www-authenticate": "Bearer"},
        )

    user: User | None = session.get(User, str_to_id(jwt_subject))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=OAuthError(
                error="invalid_client",
                error_description="invalid credentials, no user exists, contact administrator",
            ).model_dump(),
            headers={"www-authenticate": "Bearer"},
        )

    # if the user account has been disabled,
    if not user.enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=OAuthError(
                error="invalid_grant",
                error_description="user account is disabled, contact administrator",
            ).model_dump(),
        )

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
