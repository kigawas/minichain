from hashlib import blake2b
from functools import partial

__all__ = ["Hash", "Block", "BlockChain"]

Hash = partial(blake2b, digest_size=32)

from chain.block import Block  # noqa: E402
from chain.blockchain import BlockChain  # noqa: E402
