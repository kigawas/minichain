import unittest
import time

from chain import Block, BlockChain

from . import TestCase


class TestBlockChain(TestCase):
    def test_block(self):
        args = (0, "0", int(time.time()), "test")
        nonce = 0
        target = "f" * 64
        hash = Block.calculate_hash(*args, nonce, target)
        b = Block(*args, nonce=nonce, target=target, hash=hash)
        self.assertSerializable(Block, b, globals())
        self.assertTrue(b.valid)
        b.hash = "aaa"
        self.assertFalse(b.valid)

    def test_blockchain(self):
        bc = BlockChain()
        blocks_to_mine = 5
        for i in range(blocks_to_mine):
            bc.mine("data")

        self.assertSerializable(BlockChain, bc, globals())

        self.assertTrue(bc.validate_blocks(0, 1))
        self.assertTrue(bc.validate_blocks(1, 3))
        self.assertTrue(bc.is_valid_chain())
        self.assertEqual(bc.blocks, bc.blocks)
        self.assertIs(bc[0], bc.blocks[0])
        self.assertEqual(len(bc), blocks_to_mine + 1)
        self.assertEqual(bc[0:-1:2], bc.blocks[0:-1:2])
        self.assertEqual(bc[::-1], bc.blocks[::-1])

        last_block = bc[-1]
        bc1 = BlockChain()
        bc1.mine("any")
        self.assertFalse(bc1.add_block(last_block))
        self.assertNotEqual(bc, bc1)
        self.assertFalse(bc.replace(bc1))
        self.assertEqual(bc[-1], last_block)
        self.assertTrue(bc1.replace(bc))
        self.assertEqual(bc1, bc)
        print()
        for i in range(blocks_to_mine):
            bc1.mine("another data")

        self.assertIs(bc1.blocks, bc.blocks)
        self.assertEqual(bc, bc1)


if __name__ == "__main__":
    unittest.main()
