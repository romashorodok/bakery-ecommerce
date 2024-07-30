from joserfc import jwt

from bakery_ecommerce.internal.identity.private_key import PrivateKeyES256K1


def test_private_key_es256():
    es256 = PrivateKeyES256K1.from_random()
    es256_restore = PrivateKeyES256K1.from_bytes(es256.sign_signature())

    assert es256_restore.sign_signature() == es256.sign_signature()


def test_private_key_es256_encode():
    es256 = PrivateKeyES256K1.from_random()
    assert jwt.encode({"alg": "ES256K"}, {}, es256.get_pkey(), [es256.algorithm()])
