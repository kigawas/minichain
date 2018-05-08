import unittest
import time

from chain import Block, BlockChain

from . import TestCase


class TestBlockChain(TestCase):
    def test_block(self):
        args = (0, '0', int(time.time()), 'test')
        nonce = 0
        target = 'f' * 64
        hash = Block.calculate_hash(*args, nonce, target)
        b = Block(*args, nonce=nonce, target=target, hash=hash)
        self.check_serialization(Block, b, globals())
        self.assertTrue(b.valid)
        b.hash = 'aaa'
        self.assertFalse(b.valid)

    def test_blockchain(self):
        bc = BlockChain()
        for i in range(5):
            bc.mine('a')

        self.assertTrue(bc.validate_blocks(0, 1))
        self.assertTrue(bc.validate_blocks(1, 3))
        self.assertTrue(bc.is_valid_chain())
        self.assertEqual(bc.blocks, bc.blocks)
        self.check_serialization(BlockChain, bc, globals())


if __name__ == '__main__':
    unittest.main()
