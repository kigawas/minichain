import unittest
from decimal import Decimal
import binascii

from chain.transaction import TxIn, TxOut, Transaction, TX_REGULAR
from chain.mempool import get_mempool, Mempool
from chain.utils.elliptic import generate_keypair

from chain.tests import TestCase


class TestTx(TestCase):
    def test_txin(self):
        priv, pub = generate_keypair()
        ti = TxIn(1, "aaa", Decimal(100), pub)
        self.assertFalse(ti.valid)

        # sign with wrong key
        ti.sign(priv.replace("a", "1").replace("1", "b"))
        self.assertFalse(ti.valid)

        # sign with invalid key
        with self.assertRaises(binascii.Error):
            ti.sign("aaa")

        # stil screaming with error
        with self.assertRaises(ValueError):
            ti.verify()

        # sign with right key
        ti.sign(priv)
        self.assertTrue(ti.valid)

        self.check_serialization(TxIn, ti, globals())

    def test_txout(self):
        priv, pub = generate_keypair()
        to = TxOut(Decimal(100), "aaa")
        self.check_serialization(TxOut, to, globals())

        to = TxOut(Decimal(100000000000000000000), "aaa")
        self.check_serialization(TxOut, to, globals())

    def test_transaction(self):
        priv, pub = generate_keypair()
        inputs = [TxIn(1, "aaa", Decimal(200), pub)]
        outputs = [TxOut(Decimal(100), "aaa"), TxOut(Decimal(99), "bbb")]

        for ti in inputs:
            ti.sign(priv)

        tx = Transaction(TX_REGULAR, inputs, outputs)

        self.check_serialization(Transaction, tx, globals())

        self.assertTrue(tx.has_enough_balance)
        self.assertEqual(tx.fee, Decimal(1))
        self.assertTrue(tx.valid)

        tx1 = Transaction(
            TX_REGULAR, [inputs[0], TxIn(1, "bbb", Decimal(200), pub)], outputs
        )
        tx2 = Transaction(TX_REGULAR, [TxIn(1, "bbb", Decimal(200), pub)], outputs)
        self.assertTrue(tx.has_same_inputs(tx1))
        self.assertFalse(tx.has_same_inputs(tx2))

        mempool = get_mempool()
        self.assertIs(mempool, get_mempool())
        mempool == 1
        mempool.add(tx)
        mempool.add(tx)
        self.check_serialization(Mempool, mempool, globals())

        self.assertTrue(mempool.is_double_spent(tx))
        self.assertTrue(mempool.is_double_spent(tx1))
        self.assertFalse(mempool.is_double_spent(tx2))


if __name__ == "__main__":
    unittest.main()
