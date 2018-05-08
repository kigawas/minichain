import unittest


class TestCase(unittest.TestCase):
    def check_serialization(self, cls, obj, env={}):
        self.assertIsInstance(obj, cls)
        self.assertEqual(obj, eval(repr(obj), env))
        self.assertEqual(obj, cls.deserialze(obj.serialize()))
        self.assertEqual(hash(obj), hash(cls.deserialze(obj.serialize())))
