from typing import List
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

        assert self.is_valid_hash() and self.is_valid_difficulty()

    def __repr__(self):
        return 'Block({}, {}, {}, {}, {}, {}, {})'.format(
            repr(self.index), repr(self.prev_hash), repr(self.timestamp),
            repr(self.data), repr(self.nonce), repr(self.target), repr(self.hash)
        )

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


class BlockChain:

    def __init__(self):
        self.blocks = [BlockChain.genesis()]
        self.interval = 5  # 5s per block

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

    @property
    def latest_block(self) -> Block:
        return self.blocks[-1]

    @staticmethod
    def are_blocks_adjacent(block: Block, prev_block: Block) -> bool:
        is_valid_block = block.is_valid_hash() and block.is_valid_difficulty()
        is_valid_next = block.index == prev_block.index + 1 and block.prev_hash == prev_block.hash
        return is_valid_block and is_valid_next

    def is_block_next(self, block: Block) -> bool:
        return BlockChain.are_blocks_adjacent(block, self.latest_block)

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

    def mine(self, data: str) -> None:
        b = self.generate_next(data)
        if self.is_block_next(b):
            self.blocks.append(b)
        else:
            raise ValueError('Invalid next block')


if __name__ == '__main__':
    last = time.time()
    b = BlockChain()
    print(b.latest_block)
    for i in range(200):
        b.mine('a')
        interval = time.time() - last
        last = time.time()
        print(interval)

    print(b.blocks)
