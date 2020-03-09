import codecs
from typing import Tuple

from coincurve.utils import get_valid_secret
from eth_keys import keys

__all__ = ["generate_keypair", "sign", "verify"]


def remove_0x(s: str) -> str:
    if s.startswith("0x") or s.startswith("0X"):
        return s[2:]
    return s


def decode_hex(s: str) -> bytes:
    return codecs.decode(remove_0x(s), "hex")  # type: ignore


def generate_keypair() -> Tuple[str, str]:
    k = keys.PrivateKey(get_valid_secret())
    return k.to_hex(), k.public_key.to_hex()


def sign(priv_key: str, msg: str) -> str:
    prv = keys.PrivateKey(decode_hex(priv_key))
    return prv.sign_msg(msg.encode()).to_hex()


def verify(pub_key: str, sig: str, msg: str) -> bool:
    """
    >>> pri, pub = generate_keypair()
    >>> msg = 'This is a test string.'
    >>> verify(pub, sign(pri, msg), msg)
    True
    """
    pub = keys.PublicKey(decode_hex(pub_key))
    signature = keys.Signature(decode_hex(sig))
    return pub.verify_msg(msg.encode(), signature)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
