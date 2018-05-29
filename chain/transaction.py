from decimal import Decimal
from typing import List

from chain import Hash
from chain.utils import elliptic

__all__ = [
    'TxIn', 'TxOut', 'Transaction',
    'TX_REGULAR', 'TX_FEE', 'TX_REWARD'
]


class TxIn:
    def __init__(self, tx_index: int, tx_hash: str, amount: Decimal, pubkey: str, signature: str='') -> None:
        self.tx_index = tx_index
        self.tx_hash = tx_hash
        self.amount = amount
        self.pubkey = pubkey
        self._signature = signature
        self._hash = self.calculate_hash()

    def __eq__(self, other) -> bool:
        return self.hash == other.hash

    def __repr__(self) -> str:
        return 'TxIn({}, {}, {}, {}, {})'.format(
            repr(self.tx_index), repr(self.tx_hash),
            repr(self.amount), repr(self.pubkey), repr(self.signature)
        )

    def __hash__(self) -> int:
        return int(self.hash, 16)

    @property
    def signature(self) -> str:
        return self._signature

    @property
    def hash(self) -> str:
        return self._hash

    @property
    def valid(self) -> bool:
        return self.verify(quiet=True)

    def serialize(self):
        return dict(
            tx_index=self.tx_index,
            tx_hash=self.tx_hash,
            amount=str(self.amount),
            pubkey=self.pubkey,
            signature=self.signature
        )

    def calculate_hash(self) -> str:
        s: bytes = f'{self.tx_index}{self.tx_hash}{self.amount}{self.pubkey}'.encode()
        return Hash(s).hexdigest()

    def sign(self, key: str) -> str:
        self._signature = elliptic.sign(key, self.hash)
        return self.signature

    def verify(self, quiet=False) -> bool:
        computed_hash = self.calculate_hash()
        try:
            verified = elliptic.verify(self.pubkey, self.signature, computed_hash)
            if not verified:
                raise ValueError('Tx input cannot be verified')
        except Exception as e:
            verified = False
            if not quiet:
                raise e

        return verified

    @staticmethod
    def deserialze(other: dict) -> 'TxIn':
        other['amount'] = Decimal(other['amount'])
        return TxIn(**other)


class TxOut:
    def __init__(self, amount: Decimal, address: str) -> None:
        self._amount = amount
        self._address = address

    def __eq__(self, other) -> bool:
        return (self.amount, self.address) == (other.amount, other.address)

    def __repr__(self) -> str:
        return f'TxOut({repr(self.amount)}, {repr(self.address)})'

    def __hash__(self) -> int:
        return hash((self.amount, self.address))

    @property
    def amount(self) -> Decimal:
        return self._amount

    @property
    def address(self) -> str:
        return self._address

    def serialize(self) -> dict:
        return dict(amount=self.amount, address=self.address)

    @staticmethod
    def deserialze(other: dict) -> 'TxOut':
        other['amount'] = Decimal(other['amount'])
        return TxOut(**other)


TX_REGULAR = 'regular'
TX_FEE = 'fee'
TX_REWARD = 'reward'

ALL_TX_TYPES = [
    TX_REGULAR, TX_FEE, TX_REWARD
]


class Transaction:

    _reward = 100

    def __init__(self, type: str, inputs: List[TxIn]=[], outputs: List[TxOut]=[]) -> None:
        self._type = type
        assert self._type in ALL_TX_TYPES
        self._inputs = inputs
        self._outputs = outputs
        self._hash = self.calculate_hash()

    def __eq__(self, other) -> bool:
        return self.hash == other.hash

    def __repr__(self) -> str:
        return f'Transaction({repr(self.type)}, {repr(self.inputs)}, {repr(self.outputs)})'

    def __hash__(self) -> int:
        return int(self.hash, 16)

    @property
    def reward(self):
        return self._reward

    @property
    def type(self):
        return self._type

    @property
    def inputs(self):
        return self._inputs

    @property
    def outputs(self):
        return self._outputs

    @property
    def hash(self):
        return self._hash

    @property
    def total_input(self) -> Decimal:
        return sum([i.amount for i in self.inputs], Decimal(0))

    @property
    def total_output(self) -> Decimal:
        return sum([o.amount for o in self.outputs], Decimal(0))

    @property
    def has_enough_balance(self):
        self.total_input >= self.total_output

    @property
    def fee(self):
        assert self.type == TX_REGULAR
        return self.total_input - self.total_output

    @property
    def valid(self) -> bool:
        if not self.has_enough_balance:
            return False

        return all([txin.valid for txin in self.inputs])

    def serialize(self) -> dict:
        return dict(
            type=self.type,
            inputs=[txin.serialize() for txin in self.inputs],
            outputs=[txin.serialize() for txin in self.outputs],
        )

    def calculate_hash(self) -> str:
        s: bytes = f'{self.type}{self.inputs}{self.outputs}'.encode()
        return Hash(s).hexdigest()

    @staticmethod
    def deserialze(other: dict) -> 'Transaction':
        inputs = [TxIn.deserialze(txin) for txin in other['inputs']]
        outputs = [TxOut.deserialze(txout) for txout in other['outputs']]
        return Transaction(other['type'], inputs, outputs)
