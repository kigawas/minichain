import unittest
from collections.abc import Hashable


class TestCase(unittest.TestCase):
    def check_serialization(self, cls, obj, env={}):
        self.assertIsInstance(obj, cls)
        self.assertNotEqual(obj, 1)
        self.assertNotEqual(obj, "")
        self.assertEqual(obj, eval(repr(obj), env))
        self.assertEqual(obj, cls.deserialize(obj.serialize()))
        if isinstance(obj, Hashable):
            self.assertEqual(hash(obj), hash(cls.deserialize(obj.serialize())))
