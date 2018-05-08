import unittest
from decimal import Decimal

from chain.transaction import TxIn, TxOut, Transaction, TX_REGULAR
from chain.utils.elliptic import generate_keypair

from chain.tests import TestCase


class TestTx(TestCase):
    def test_txin(self):
        priv, pub = generate_keypair()
        ti = TxIn(1, 'aaa', Decimal(100), pub)
        self.assertFalse(ti.valid)
        ti.sign(priv)
        self.assertTrue(ti.valid)
        self.check_serialization(TxIn, ti, globals())

    def test_txout(self):
        priv, pub = generate_keypair()
        to = TxOut(Decimal(100), 'aaa')
        self.check_serialization(TxOut, to, globals())

    def test_transaction(self):
        priv, pub = generate_keypair()
        tx = Transaction(
            TX_REGULAR,
            [TxIn(1, 'aaa', Decimal(200), pub)],
            [TxOut(Decimal(100), 'aaa'), TxOut(Decimal(100), 'bbb')]
        )
        self.check_serialization(Transaction, tx, globals())


if __name__ == '__main__':
    unittest.main()
