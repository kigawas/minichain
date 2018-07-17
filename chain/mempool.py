from typing import Set

from chain.transaction import Transaction

__all__ = ["get_mempool", "Mempool"]


class Mempool:
    def __init__(self, transactions: Set[Transaction] = set()) -> None:
        self.transactions = transactions

    def __repr__(self) -> str:
        return f"Mempool({repr(self.transactions)})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Mempool):
            return False
        return self.transactions == other.transactions

    def trim_txs(self, block_txs: Set[Transaction]) -> None:
        self.transactions.difference_update(block_txs)

    def is_double_spent(self, transaction) -> bool:
        for tx in self.transactions:
            if tx.has_same_inputs(transaction):
                return True
        return False

    def add(self, transaction: Transaction) -> bool:
        if self.is_double_spent(transaction):
            return False

        self.transactions.add(transaction)

        return True

    def remove(self, transaction: Transaction) -> None:
        self.transactions.discard(transaction)

    def serialize(self) -> dict:
        return dict(transactions=list(self.transactions))

    @staticmethod
    def deserialize(other: dict) -> "Mempool":
        return Mempool(transactions=set(other["transactions"]))


_mempool = Mempool()


def get_mempool() -> Mempool:
    return _mempool
