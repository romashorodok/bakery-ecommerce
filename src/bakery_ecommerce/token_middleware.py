from json import loads
from typing import Annotated
from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce import dependencies

from bakery_ecommerce.internal.identity import (
    private_key_use_case,
)
from bakery_ecommerce.internal.identity.token import Token, TokenClaim, TokenUse
from bakery_ecommerce.internal.store.query import QueryProcessor


def verify_token_factory(
    token_use_types: list[TokenUse] = [TokenUse.ACCESS_TOKEN],
    validate_token: bool = True,  # For refresh_token validity, check if it blacklisted
):
    async def verify_token(
        authorization: Annotated[str, Header()],
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

        if payload.get(TokenClaim.TOKEN_USE) not in token_use_types:
            raise HTTPException(
                status_code=401, detail=f"Provide {token_use_types} token"
            )

        headers = signature.headers()
        kid = headers.get("kid")
        if not kid:
            raise HTTPException(status_code=401, detail="Missing kid header")

        get_private_key = private_key_use_case.GetPrivateKeySession(tx, queries)

        private_key = await get_private_key.execute(
            private_key_use_case.GetPrivateKeySessionEvent(
                kid=kid,
                user_id=user_id,
            )
        )

        try:
            token = Token.verify_jws_from_text(token, private_key)

            if validate_token:
                token.validate()

            return token
        except Exception as e:
            raise HTTPException(status_code=403, detail=f"{e}")

    return verify_token


verify_access_token = verify_token_factory([TokenUse.ACCESS_TOKEN], True)
verify_refresh_token = verify_token_factory([TokenUse.REFRESH_TOKEN], False)
verify_any_token = verify_token_factory(
    [TokenUse.ACCESS_TOKEN, TokenUse.REFRESH_TOKEN],
    validate_token=False,
)
