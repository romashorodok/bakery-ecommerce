from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

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


def register_handler(router: APIRouter):
    router.include_router(api, prefix="/identity")
