import asyncio
from datetime import datetime, timedelta
import pytest

from bakery_ecommerce.internal.identity.token import (
    InvalidTokenError,
    Token,
    TokenClaim,
    TokenUse,
)
from bakery_ecommerce.internal.identity.private_key import PrivateKeyES256K1


@pytest.mark.asyncio
async def test_token_validate_exp():
    token = Token()
    token.add_token_use(TokenUse.ACCESS_TOKEN)
    pkey = PrivateKeyES256K1.from_random()
    raw = token.sign_token_as_jws(pkey)
    assert raw

    token = Token.verify_jws_from_text(raw, pkey)

    with pytest.raises(InvalidTokenError) as e:
        token.validate()
    # Require expired claim
    assert "exp" in str(e.value)

    next_second = (datetime.now() + timedelta(seconds=1)).timestamp()
    token.add_claim(TokenClaim.EXPIRATION, int(next_second))
    raw = token.sign_token_as_jws(pkey)
    token = Token.verify_jws_from_text(raw, pkey)
    token.validate()

    await asyncio.sleep(1)
    with pytest.raises(InvalidTokenError) as e:
        token.validate()

    # Already expired
    assert "expired" in str(e.value)


def test_token_generate_twice_same_pkey():
    pkey = PrivateKeyES256K1.from_random()

    token = Token()
    payload_1 = token.sign_token_as_jws(pkey)
    payload_2 = token.sign_token_as_jws(pkey)
    assert payload_1 != payload_2
