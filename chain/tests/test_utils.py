from chain.utils.elliptic import generate_keypair, sign, verify
from chain.utils.log import logger

from chain.tests import TestCase


class TestTx(TestCase):
    def test_elliptic(self):
        prv, pub = generate_keypair()
        msg = "0" * 1024 * 1024 * 100  # assuming 100 MB block data
        self.assertTrue(verify(pub, sign(prv, msg), msg))

    def test_log(self):
        print()
        logger.info("INFO LOG")
        logger.warning("WARNING LOG")
        logger.error("ERROR LOG")
        logger.debug("DEBUG LOG")
