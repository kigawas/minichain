from functools import total_ordering
from hashlib import blake2s
import time

__all__ = ['Block']


class Block:
    def __init__(self, index: int, prev_hash: str, timestamp: int, data: str, nonce: int, target: str, hash: str):
        self.index = index
        self.prev_hash = prev_hash
        self.timestamp = timestamp
        self.data = data
        self.nonce = nonce
        self.target = target
        self.hash = hash

        assert self.valid

    def __repr__(self):
        return 'Block({}, {}, {}, {}, {}, {}, {})'.format(
            repr(self.index), repr(self.prev_hash), repr(self.timestamp),
            repr(self.data), repr(self.nonce), repr(self.target), repr(self.hash)
        )

    def serialize(self) -> dict:
        return dict(index=self.index,
                    prev_hash=self.prev_hash,
                    timestamp=self.timestamp,
                    data=self.data,
                    nonce=self.nonce,
                    target=self.target,
                    hash=self.hash)

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
        s = f'{index}{prev_hash}{timestamp}{data}{nonce}{target}'.encode()
        return blake2s(s).hexdigest()

    @staticmethod
    def validate_difficulty(hash: str, target: str) -> bool:
        return int(hash, 16) <= int(target, 16)


@total_ordering
class BlockChain:

    def __init__(self, blocks=[]):
        self.blocks = [BlockChain.genesis()] if not blocks else blocks
        self._interval = 5  # 5s per block

    def __len__(self):
        return self.length

    def __eq__(self, other):
        if self.length != other.length:
            return False
        return all([b1.hash == b2.hash for b1, b2 in zip(self.blocks, other.blocks)])

    def __lt__(self, other):
        return self.length < other.length

    @property
    def interval(self) -> int:
        return self._interval

    @property
    def latest_block(self) -> Block:
        return self.blocks[-1]

    @property
    def length(self) -> int:
        return len(self.blocks)

    def serialize(self) -> dict:
        return dict(
            blocks=[b.serialize() for b in self.blocks]
        )

    def replace(self, other) -> None:
        if self < other and other.is_valid_chain():
            self.blocks = other.blocks

    def retarget(self) -> str:
        lb = self.latest_block
        block_count = 10
        target_timespan = block_count * self.interval
        if len(self.blocks) % block_count != 0:
            return lb.target
        else:
            ratio_limit = 4
            actual_timespan = lb.timestamp - self.blocks[-block_count].timestamp
            actual_timespan = max(actual_timespan, target_timespan / ratio_limit)
            actual_timespan = min(actual_timespan, target_timespan * ratio_limit)
            assert 1 / ratio_limit <= actual_timespan / target_timespan <= ratio_limit
            print(f'Retargeting at {len(self.blocks)}, difficulty change: {target_timespan/actual_timespan:.2%}')
            new_target = int(lb.target, 16) * actual_timespan / target_timespan
            return f'{int(new_target):x}'.rjust(64, '0')

    def validate_blocks(self, left: int, right: int):
        assert 0 <= left < right < self.length
        mini_blocks = self.blocks[left:right + 1]
        are_all_valid = all([b.valid for b in mini_blocks])
        are_all_adjacent = all([
            BlockChain.are_blocks_adjacent(cur_block, prev_block)
            for prev_block, cur_block in zip(mini_blocks[:-1], mini_blocks[1:])
        ])
        return are_all_valid and are_all_adjacent

    def is_valid_chain(self):
        return self.validate_blocks(0, self.length - 1)

    def generate_next(self, data: str) -> Block:
        lb = self.latest_block
        args = (lb.index + 1, lb.hash, int(time.time()), data)
        nonce = 0
        target = self.retarget()
        while True:
            hash = Block.calculate_hash(*args, nonce=nonce, target=target)
            if Block.validate_difficulty(hash, target):
                break
            else:
                nonce += 1
        return Block(*args, nonce=nonce, target=target, hash=hash)

    def is_next_block(self, block: Block) -> bool:
        return BlockChain.are_blocks_adjacent(block, self.latest_block)

    def mine(self, data: str) -> None:
        b = self.generate_next(data)
        if self.is_next_block(b):
            self.blocks.append(b)
        else:
            raise ValueError('Invalid next block')

    @staticmethod
    def are_blocks_adjacent(block: Block, prev_block: Block) -> bool:
        is_valid_block = block.valid
        is_valid_next = block.index == prev_block.index + 1 and block.prev_hash == prev_block.hash
        return is_valid_block and is_valid_next

    @staticmethod
    def genesis() -> Block:
        args = (0, '0', int(time.time()), 'Genesis Block')
        nonce = 0
        # suppose this target's difficulty = 1
        target = '0000ffff00000000000000000000000000000000000000000000000000000000'
        while True:
            hash = Block.calculate_hash(*args, nonce=nonce, target=target)
            if Block.validate_difficulty(hash, target):
                break
            else:
                nonce += 1
        return Block(*args, nonce=nonce, target=target, hash=hash)

    @staticmethod
    def deserialze(other: dict):
        blocks = [Block(**d) for d in other['blocks']]
        return BlockChain(blocks=blocks)


if __name__ == '__main__':
    last = time.time()
    b = BlockChain()
    print(b.latest_block)
    for i in range(100):
        b.mine('a')
        interval = time.time() - last
        last = time.time()
        print(interval)

    print(b.validate_blocks(0, 1))
    print(b.validate_blocks(1, 3))
    print(b.is_valid_chain())
    print(BlockChain.deserialze(b.serialize()) == b)

    print(b.blocks)
