from chain import Hash
from dataclasses import dataclass


@dataclass(frozen=True)
class Block:
    index: int
    prev_hash: str
    timestamp: int
    data: str
    nonce: int
    target: str
    hash: str

    def __hash__(self) -> int:
        return int(self.hash, 16)

    @staticmethod
    def calculate_hash(
        index: int, prev_hash: str, timestamp: int, data: str, nonce: int, target: str
    ) -> str:
        s: bytes = f"{index}{prev_hash}{timestamp}{data}{nonce}{target}".encode()
        return Hash(s).hexdigest()

    @staticmethod
    def validate_difficulty(hash: str, target: str) -> bool:
        return int(hash, 16) <= int(target, 16)

    @classmethod
    def deserialize(cls, other: dict):
        return cls(**other)

    def serialize(self) -> dict:
        return dict(
            index=self.index,
            prev_hash=self.prev_hash,
            timestamp=self.timestamp,
            data=self.data,
            nonce=self.nonce,
            target=self.target,
            hash=self.hash,
        )

    def is_valid(self) -> bool:
        return self.is_valid_hash() and self.is_valid_difficulty()

    def is_valid_hash(self) -> bool:
        return self.recalculate_hash() == self.hash

    def is_valid_difficulty(self) -> bool:
        return self.validate_difficulty(self.hash, self.target)

    def recalculate_hash(self) -> str:
        return self.calculate_hash(
            self.index,
            self.prev_hash,
            self.timestamp,
            self.data,
            self.nonce,
            self.target,
        )
