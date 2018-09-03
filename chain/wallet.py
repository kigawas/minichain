from chain.utils import elliptic


class Wallet:
    def __init__(self, password=None):
        self._key_pair = elliptic.generate_keypair()
        self._password = password

    def get_public_key(self):
        return self._key_pair[1]

    def get_private_key(self, password=None):
        if self._password != password:
            raise ValueError("Incorrect password")

        return self._key_pair[0]
