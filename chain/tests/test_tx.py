import unittest
from decimal import Decimal
import binascii

from chain.transaction import TxIn, TxOut, Transaction, TX_REGULAR
from chain.utils.elliptic import generate_keypair

from chain.tests import TestCase


class TestTx(TestCase):
    def test_txin(self):
        priv, pub = generate_keypair()
        ti = TxIn(1, 'aaa', Decimal(100), pub)
        self.assertFalse(ti.valid)

        # sign with wrong key
        ti.sign(priv.replace('a','1').replace('1', 'b'))
        self.assertFalse(ti.valid)

        # sign with invalid key
        with self.assertRaises(binascii.Error):
            ti.sign('aaa')

        # stil screaming with error
        with self.assertRaises(ValueError):
            ti.verify()

        # sign with right key
        ti.sign(priv)
        self.assertTrue(ti.valid)

        self.check_serialization(TxIn, ti, globals())

    def test_txout(self):
        priv, pub = generate_keypair()
        to = TxOut(Decimal(100), 'aaa')
        self.check_serialization(TxOut, to, globals())

        to = TxOut(Decimal(100000000000000000000), 'aaa')
        self.check_serialization(TxOut, to, globals())

    def test_transaction(self):
        priv, pub = generate_keypair()
        tx = Transaction(
            TX_REGULAR,
            [TxIn(1, 'aaa', Decimal(200), pub)],
            [TxOut(Decimal(100), 'aaa'), TxOut(Decimal(99), 'bbb')]
        )

        self.check_serialization(Transaction, tx, globals())

        self.assertTrue(tx.has_enough_balance)
        self.assertEqual(tx.fee, Decimal(1))

if __name__ == '__main__':
    unittest.main()
