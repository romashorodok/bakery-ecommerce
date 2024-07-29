from typing import Self

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

from joserfc import jwk
from joserfc.rfc7517 import types as rfc7517_types
from joserfc.rfc8812 import register_secp256k1


register_secp256k1()


class PrivateKeyES256K1:
    def __init__(self, eckey: jwk.ECKey) -> None:
        eckey.public_key
        self.__eckey = eckey
        self.__keyset = jwk.KeySet([self.__eckey])

    @classmethod
    def from_bytes(cls, raw: rfc7517_types.DictKey) -> Self:
        return cls(jwk.ECKey.import_key(raw))

    @classmethod
    def from_random(cls) -> Self:
        pkey = ec.generate_private_key(ec.SECP256K1())
        pkey_pem = pkey.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return cls(jwk.ECKey.import_key(pkey_pem))

    def jwk_sign_message(self):
        return self.__keyset.keys[0].as_dict()

    def kid(self) -> str | None:
        t = self.jwk_sign_message().get("kid")
        if isinstance(t, list):
            return t[0]
        return t

    def get_pkey(self) -> jwk.KeyFlexible:
        return self.__eckey

    def algorithm(self) -> str:
        return "ES256K"
