from json import loads
from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from nats.aio.client import Client as NATS

from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

from bakery_ecommerce import dependencies
from bakery_ecommerce.composable import Composable, set_key
from bakery_ecommerce.context_bus import ContextBus, ContextExecutor

from bakery_ecommerce.internal.identity import (
    private_key_use_case,
    token_use_case,
    user_use_cases,
)
from bakery_ecommerce.internal.identity.store.user_model import User
from bakery_ecommerce.internal.identity.token import Token, TokenClaim, TokenUse
from bakery_ecommerce.internal.store.query import QueryProcessor


api = APIRouter()

route = "/"


def _login_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    tx: AsyncSession = Depends(dependencies.request_transaction),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    validate_user_password = user_use_cases.ValidateUserPassword(context, tx, queries)
    create_private_key = private_key_use_case.CreatePrivateKey(context, tx, queries)
    create_access_token = token_use_case.CreateAccessToken()
    create_refresh_token = token_use_case.CreateRefreshToken()
    return (
        context
        | ContextExecutor(
            user_use_cases.ValidateUserPasswordEvent,
            lambda e: validate_user_password.execute(e),
        )
        | ContextExecutor(
            user_use_cases.UserValidPasswordEvent,
            lambda e: create_private_key.execute(
                private_key_use_case.CreatePrivateKeyEvent(
                    user_id=e.user.id,
                )
            ),
        )
        | ContextExecutor(
            private_key_use_case.PrivateKeyCreatedEvent,
            lambda e: create_refresh_token.execute(
                token_use_case.CreateRefreshTokenEvent(
                    pkey=e.pkey,
                    user_id=e.user_id,
                )
            ),
        )
        | ContextExecutor(
            private_key_use_case.PrivateKeyCreatedEvent,
            lambda e: create_access_token.execute(
                token_use_case.CreateAccessTokenEvent(
                    pkey=e.pkey,
                    user_id=e.user_id,
                )
            ),
        )
    )


class LoginRequestBody(BaseModel):
    email: str
    password: str


@api.post(path=f"{route}login")
async def login(
    body: LoginRequestBody,
    context: Annotated[ContextBus, Depends(_login_request__context_bus)],
):
    await context.publish(
        user_use_cases.ValidateUserPasswordEvent(
            email=body.email, password=body.password
        )
    )

    try:
        result = await context.gather()
    except user_use_cases.InvalidEmailError as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=e.args)
    except user_use_cases.InvalidPasswordHashError as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=e.args)
    except Exception as e:
        raise e

    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        token_use_case.CreateAccessTokenResult,
        lambda resp, access_token: set_key(resp, "access_token", access_token),
    )
    cmp.reducer(
        token_use_case.CreateRefreshTokenResult,
        lambda resp, refresh_token: set_key(resp, "refresh_token", refresh_token),
    )

    resp = cmp.reduce(result.flatten())
    return resp


class RegisterRequestBody(BaseModel):
    first_name: str
    last_name: str
    password: str
    email: str


def _register_request__context_bus(
    tx: AsyncSession = Depends(dependencies.request_transaction),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
    context: ContextBus = Depends(dependencies.request_context_bus),
) -> ContextBus:
    create_user = user_use_cases.CreateUser(context, tx, queries)
    create_private_key = private_key_use_case.CreatePrivateKey(context, tx, queries)
    create_access_token = token_use_case.CreateAccessToken()
    create_refresh_token = token_use_case.CreateRefreshToken()
    return (
        context
        | ContextExecutor(
            user_use_cases.CreateUserEvent,
            lambda e: create_user.execute(e),
        )
        | ContextExecutor(
            user_use_cases.UserCreatedEvent,
            lambda e: create_private_key.execute(
                private_key_use_case.CreatePrivateKeyEvent(user_id=e.id)
            ),
        )
        | ContextExecutor(
            private_key_use_case.PrivateKeyCreatedEvent,
            lambda e: create_refresh_token.execute(
                token_use_case.CreateRefreshTokenEvent(
                    pkey=e.pkey,
                    user_id=e.user_id,
                )
            ),
        )
        | ContextExecutor(
            private_key_use_case.PrivateKeyCreatedEvent,
            lambda e: create_access_token.execute(
                token_use_case.CreateAccessTokenEvent(
                    pkey=e.pkey,
                    user_id=e.user_id,
                )
            ),
        )
    )


@api.post(path=f"{route}")
async def register(
    body: RegisterRequestBody,
    context: Annotated[ContextBus, Depends(_register_request__context_bus)],
    tx: AsyncSession = Depends(dependencies.request_transaction),
):
    await context.publish(
        user_use_cases.CreateUserEvent(
            first_name=body.first_name,
            last_name=body.last_name,
            password=body.password,
            email=body.email,
        )
    )

    try:
        result = await context.gather()
    except IntegrityError as e:
        await tx.rollback()
        print("Error occured on register context. Err:", e)
        base_e = e.orig
        if not base_e:
            raise e
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="User already exist or something goes wrong",
        )
    except Exception as e:
        await tx.rollback()
        print("Error occured on register context. Err:", e)
        raise e

    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        User,
        lambda resp, user: set_key(
            resp,
            "user",
            {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
            },
        ),
    )
    cmp.reducer(
        token_use_case.CreateAccessTokenResult,
        lambda resp, access_token: set_key(resp, "access_token", access_token),
    )
    cmp.reducer(
        token_use_case.CreateRefreshTokenResult,
        lambda resp, refresh_token: set_key(resp, "refresh_token", refresh_token),
    )

    resp = cmp.reduce(result.flatten())
    return resp


async def verify_token(
    authorization: Annotated[str, Header()],
    nc: Annotated[NATS, Depends(dependencies.request_nats_session)],
    tx: AsyncSession = Depends(dependencies.request_transaction),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> Token:
    token = authorization.split("Bearer ")[1]
    signature = Token.extract_signature_jws_from_text(token)
    payload = loads(signature.payload)
    if not isinstance(payload, dict) or len(payload) == 0:
        # 403 must be me returned when token expired
        # On 401 token must be removed
        raise HTTPException(status_code=401, detail="Missing token payload")

    user_id = payload.get(TokenClaim.USER_ID)
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing user_id claim")

    if payload.get(TokenClaim.TOKEN_USE) != TokenUse.ACCESS_TOKEN:
        raise HTTPException(status_code=401, detail="Provide access token")

    headers = signature.headers()
    kid = headers.get("kid")
    if not kid:
        raise HTTPException(status_code=401, detail="Missing kid header")

    get_private_key = private_key_use_case.GetPrivateKeySession(nc, tx, queries)

    private_key = await get_private_key.execute(
        private_key_use_case.GetPrivateKeySessionEvent(
            kid=kid,
            user_id=user_id,
        )
    )

    try:
        token = Token.verify_jws_from_text(token, private_key)
        token.validate()
        return token
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"{e}")


@api.post(path=f"{route}token-info", dependencies=[Depends(verify_token)])
async def token_info(token: Token = Depends(verify_token)):
    return {"token": token.info()}


async def verify_refresh_token(
    authorization: Annotated[str, Header()],
    nc: Annotated[NATS, Depends(dependencies.request_nats_session)],
    tx: AsyncSession = Depends(dependencies.request_transaction),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
):
    token = authorization.split("Bearer ")[1]
    signature = Token.extract_signature_jws_from_text(token)
    payload = loads(signature.payload)
    if not isinstance(payload, dict) or len(payload) == 0:
        # 403 must be me returned when token expired
        # On 401 token must be removed
        raise HTTPException(status_code=401, detail="Missing token payload")

    user_id = payload.get(TokenClaim.USER_ID)
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing user_id claim")

    if payload.get(TokenClaim.TOKEN_USE) != TokenUse.REFRESH_TOKEN:
        raise HTTPException(status_code=401, detail="Provide refresh token")

    headers = signature.headers()
    kid = headers.get("kid")
    if not kid:
        raise HTTPException(status_code=401, detail="Missing kid header")

    get_private_key = private_key_use_case.GetPrivateKeySession(nc, tx, queries)

    private_key = await get_private_key.execute(
        private_key_use_case.GetPrivateKeySessionEvent(
            kid=kid,
            user_id=user_id,
        )
    )

    try:
        token = Token.verify_jws_from_text(token, private_key)

        return token
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"{e}")


def _refresh_access_token_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
) -> ContextBus:
    create_access_token = token_use_case.CreateAccessToken()
    create_refresh_token = token_use_case.CreateRefreshToken()
    return (
        context
        | ContextExecutor(
            token_use_case.CreateRefreshTokenEvent,
            lambda e: create_refresh_token.execute(
                token_use_case.CreateRefreshTokenEvent(
                    pkey=e.pkey,
                    user_id=e.user_id,
                )
            ),
        )
        | ContextExecutor(
            token_use_case.CreateAccessTokenEvent,
            lambda e: create_access_token.execute(
                token_use_case.CreateAccessTokenEvent(
                    pkey=e.pkey,
                    user_id=e.user_id,
                )
            ),
        )
    )


@api.post(
    path=f"{route}refresh-access-token", dependencies=[Depends(verify_refresh_token)]
)
async def refresh_access_token(
    token: Annotated[Token, Depends(verify_refresh_token)],
    context: Annotated[ContextBus, Depends(_refresh_access_token_request__context_bus)],
):
    private_key = token.private_key()
    if not private_key:
        raise HTTPException(
            status_code=401, detail="Missing private key after refresh token validate"
        )

    try:
        user_id = token.user_id()
        if not user_id:
            raise ValueError()
    except Exception:
        raise HTTPException(
            status_code=401, detail="Invalid user id after refresh token validate"
        )

    await context.publish(
        token_use_case.CreateRefreshTokenEvent(
            pkey=private_key,
            user_id=user_id,
        )
    )

    await context.publish(
        token_use_case.CreateAccessTokenEvent(
            pkey=private_key,
            user_id=user_id,
        )
    )

    result = await context.gather()

    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        token_use_case.CreateAccessTokenResult,
        lambda resp, access_token: set_key(resp, "access_token", access_token),
    )
    cmp.reducer(
        token_use_case.CreateRefreshTokenResult,
        lambda resp, refresh_token: set_key(resp, "refresh_token", refresh_token),
    )
    resp = cmp.reduce(result.flatten())
    return resp


async def verify_any_token(
    authorization: Annotated[str, Header()],
    nc: Annotated[NATS, Depends(dependencies.request_nats_session)],
    tx: AsyncSession = Depends(dependencies.request_transaction),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
):
    token = authorization.split("Bearer ")[1]
    signature = Token.extract_signature_jws_from_text(token)
    payload = loads(signature.payload)
    if not isinstance(payload, dict) or len(payload) == 0:
        # 403 must be me returned when token expired
        # On 401 token must be removed
        raise HTTPException(status_code=401, detail="Missing token payload")

    user_id = payload.get(TokenClaim.USER_ID)
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing user_id claim")

    headers = signature.headers()
    kid = headers.get("kid")
    if not kid:
        raise HTTPException(status_code=401, detail="Missing kid header")

    get_private_key = private_key_use_case.GetPrivateKeySession(nc, tx, queries)

    private_key = await get_private_key.execute(
        private_key_use_case.GetPrivateKeySessionEvent(
            kid=kid,
            user_id=user_id,
        )
    )

    try:
        token = Token.verify_jws_from_text(token, private_key)

        return token
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"{e}")


@api.delete(path=f"{route}", dependencies=[Depends(verify_any_token)])
def blacklist_token():
    print("TODO: backlist token on logout")
    return {"resutl": "TODO"}


def register_handler(router: APIRouter):
    router.include_router(api, prefix="/identity")
