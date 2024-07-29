from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, Self

from joserfc import jwk, jwt


class PrivateKeyProtocol(Protocol):
    def get_pkey(self) -> jwk.KeyFlexible: ...
    def algorithm(self) -> str: ...
    def kid(self) -> str | None: ...


class TokenUse(StrEnum):
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"


class TokenClaim(StrEnum):
    ISSUER = "iss"
    EXPIRATION = "exp"
    AUDIENCE = "aud"
    SUBJECT = "sub"

    USER_ID = "user:id"


class InvalidSignatureError(Exception): ...


class InvalidTokenError(Exception): ...


class Token:
    def __init__(self) -> None:
        self.__claims = dict[str, Any]()
        self.__headers = dict[str, Any]()

    def validate(self):
        claims_registry = jwt.JWTClaimsRegistry(
            now=int(datetime.now().timestamp()),
            leeway=-1,
            exp={"essential": True},
        )

        try:
            claims_registry.validate(self.__claims)
        except Exception as e:
            raise InvalidTokenError(e)

    @classmethod
    def verify_jws_from_text(cls, key: str, public_key: PrivateKeyProtocol) -> Self:
        try:
            jws_signature = jwt.decode(
                key, public_key.get_pkey(), [public_key.algorithm()]
            )
        except Exception as e:
            raise InvalidSignatureError(e)

        token = cls()
        token.__headers = jws_signature.header
        token.__claims = jws_signature.claims
        return token

    def sign_token_as_jws(self, private_key: PrivateKeyProtocol):
        """
        For jws, a private key is used for encode, and a public key is used for decode.

        The encode will use a private key to sign, and the decode will use a public key to verify.
        """
        headers = {"alg": private_key.algorithm(), "kid": private_key.kid()}
        return jwt.encode(
            headers,
            self.__claims,
            private_key.get_pkey(),
            [private_key.algorithm()],
        )

    @classmethod
    def verify_jwe_from_text(cls, key: str, private_key: PrivateKeyProtocol) -> Self:
        raise NotImplementedError("Implement Token.verify_jwe_from_text")

    def sign_token_as_jwe(self, public_key: PrivateKeyProtocol) -> Self:
        """
        For jwe, a public key is used for encode, and a private key is used for decode.

        The encode will use a public key to encrypt, and the decode will use a private key to decrypt.
        """
        raise NotImplementedError("Implement Token.sign_token_as_jwe")

    def add_token_use(self, token_use: TokenUse):
        self.__claims["token_use"] = str(token_use)

    def add_claim(self, claim: TokenClaim, value: Any):
        self.__claims[claim] = value

    def __repr__(self) -> str:
        return f"Token(__claims={self.__claims}, __header={self.__headers})"
