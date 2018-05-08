from chain import Hash


class Block:
    def __init__(self, index: int, prev_hash: str, timestamp: int, data: str, nonce: int, target: str, hash: str) -> None:
        self.index = index
        self.prev_hash = prev_hash
        self.timestamp = timestamp
        self.data = data
        self.nonce = nonce
        self.target = target
        self.hash = hash

        assert self.valid

    def __eq__(self, other) -> bool:
        if self.index != other.index:
            return False

        if self.hash != other.hash:
            return False

        return True

    def __repr__(self) -> str:
        return 'Block({}, {}, {}, {}, {}, {}, {})'.format(
            repr(self.index), repr(self.prev_hash), repr(self.timestamp),
            repr(self.data), repr(self.nonce), repr(self.target), repr(self.hash)
        )

    def __hash__(self) -> int:
        return int(self.hash, 16)

    def serialize(self) -> dict:
        return dict(
            index=self.index,
            prev_hash=self.prev_hash,
            timestamp=self.timestamp,
            data=self.data,
            nonce=self.nonce,
            target=self.target,
            hash=self.hash
        )

    @property
    def valid(self) -> bool:
        return self.is_valid_hash() and self.is_valid_difficulty()

    def is_valid_hash(self) -> bool:
        return self.recalculate_hash() == self.hash

    def is_valid_difficulty(self) -> bool:
        return Block.validate_difficulty(self.hash, self.target)

    def recalculate_hash(self) -> str:
        return Block.calculate_hash(
            self.index, self.prev_hash, self. timestamp, self.data, self.nonce, self.target
        )

    @staticmethod
    def calculate_hash(index: int, prev_hash: str, timestamp: int, data: str, nonce: int, target: str) -> str:
        s: bytes = f'{index}{prev_hash}{timestamp}{data}{nonce}{target}'.encode()
        return Hash(s).hexdigest()

    @staticmethod
    def validate_difficulty(hash: str, target: str) -> bool:
        return int(hash, 16) <= int(target, 16)

    @staticmethod
    def deserialze(other: dict) -> 'Block':
        return Block(**other)
