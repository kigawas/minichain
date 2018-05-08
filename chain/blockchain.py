from typing import List
import time

from chain.utils.log import logger
from chain.block import Block


class BlockChain:
    _interval = 5  # 5s per block

    def __init__(self, blocks: List[Block] = []) -> None:
        self.blocks = [BlockChain.genesis()] if not blocks else blocks

    def __len__(self) -> int:
        return self.length

    def __repr__(self) -> str:
        return f'BlockChain({repr(self.blocks)})'

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.blocks[key]
        else:
            return self.blocks[key.start:key.stop:key.step]

    def __eq__(self, other) -> bool:
        if self.length != other.length:
            return False
        return all([b1.hash == b2.hash for b1, b2 in zip(self.blocks, other.blocks)])

    def __hash__(self) -> int:
        return hash(sum([hash(b) for b in self.blocks]))

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

    def replace(self, other: 'BlockChain') -> None:
        if not other.is_valid_chain() or self == other:
            return

        if self.length < other.length:
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
            adjusted_timespan = min(
                max(actual_timespan, target_timespan / ratio_limit),
                target_timespan * ratio_limit
            )
            assert 1 / ratio_limit <= adjusted_timespan / target_timespan <= ratio_limit
            logger.info(f'Retargeting at {self.length}, difficulty change: {target_timespan/adjusted_timespan:.2%}')
            new_target = int(lb.target, 16) * adjusted_timespan / target_timespan
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

    def add_block(self, block: Block) -> bool:
        if block.valid and self.is_next_block(block):
            self.blocks.append(block)
            return True
        else:
            return False

    def mine(self, data: str) -> bool:
        next_block = self.generate_next(data)
        return self.add_block(next_block)

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
        target = '00000ffff0000000000000000000000000000000000000000000000000000000'
        while True:
            hash = Block.calculate_hash(*args, nonce=nonce, target=target)
            if Block.validate_difficulty(hash, target):
                break
            else:
                nonce += 1
        return Block(*args, nonce=nonce, target=target, hash=hash)

    @staticmethod
    def deserialze(other: dict) -> 'BlockChain':
        blocks = [Block(**b) for b in other['blocks']]
        return BlockChain(blocks=blocks)
