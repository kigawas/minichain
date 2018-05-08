from typing import Tuple

from secp256k1 import PrivateKey, PublicKey

__all__ = [
    'generate_keypair',
    'sign',
    'verify'
]


def generate_keypair() -> Tuple[str, str]:
    k = PrivateKey()
    return k.private_key.hex(), k.pubkey.serialize().hex()


def sign(priv_key: str, msg: str) -> str:
    k = PrivateKey(bytes.fromhex(priv_key))
    sig = k.ecdsa_sign(msg.encode())
    return k.ecdsa_serialize(sig).hex()


def verify(pub_key: str, sig: str, msg: str) -> bool:
    k = PublicKey(bytes.fromhex(pub_key), raw=True)
    s = k.ecdsa_deserialize(bytes.fromhex(sig))
    return k.ecdsa_verify(msg.encode(), s)


# pri, pub = generate_keypair()
# msg = 'aaaa'
# sig = sign(pri, msg)
# print(pri, pub, sig)
# print(verify(pub, sig, msg))
