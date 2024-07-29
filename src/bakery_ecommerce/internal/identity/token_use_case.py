from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from bakery_ecommerce.context_bus import ContextEventProtocol, impl_event
from bakery_ecommerce.internal.identity.token import (
    PrivateKeyProtocol,
    Token,
    TokenClaim,
    TokenUse,
)


@dataclass
@impl_event(ContextEventProtocol)
class CreateRefreshTokenEvent:
    pkey: PrivateKeyProtocol
    user_id: UUID

    @property
    def payload(self):
        return self


@dataclass
class CreateRefreshTokenResult:
    expires_at: int
    value: str


class CreateRefreshToken:
    __EXPIRE_AT_DELTA = timedelta(days=365)

    async def execute(self, params: CreateRefreshTokenEvent):
        token = Token()
        expire_at_next_year = int((datetime.now() + self.__EXPIRE_AT_DELTA).timestamp())
        token.add_claim(TokenClaim.EXPIRATION, expire_at_next_year)
        token.add_claim(TokenClaim.USER_ID, str(params.user_id))
        token.add_token_use(TokenUse.REFRESH_TOKEN)

        token_str = token.sign_token_as_jws(params.pkey)
        return CreateRefreshTokenResult(expire_at_next_year, token_str)


@dataclass
@impl_event(ContextEventProtocol)
class CreateAccessTokenEvent:
    pkey: PrivateKeyProtocol
    user_id: UUID

    @property
    def payload(self):
        return self


@dataclass
class CreateAccessTokenResult:
    expires_at: int
    value: str


class CreateAccessToken:
    __EXPIRE_AT_DELTA = timedelta(minutes=1)

    async def execute(self, params: CreateAccessTokenEvent):
        token = Token()
        expire_at_one_minute = int(
            (datetime.now() + self.__EXPIRE_AT_DELTA).timestamp()
        )
        token.add_claim(TokenClaim.EXPIRATION, expire_at_one_minute)
        token.add_claim(TokenClaim.USER_ID, str(params.user_id))
        token.add_token_use(TokenUse.ACCESS_TOKEN)

        token_str = token.sign_token_as_jws(params.pkey)
        return CreateAccessTokenResult(expire_at_one_minute, token_str)
