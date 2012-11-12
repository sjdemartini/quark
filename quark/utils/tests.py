from django.test import TestCase

from quark.utils.create_dev_db import is_valid_db_name
from quark.utils.dev import OFFSETS
from quark.utils.dev import get_port


class DevTest(TestCase):
    def test_offsets_correct_values(self):
        for _, offset in OFFSETS.items():
            self.assertLessEqual(offset, 998)
            self.assertGreaterEqual(offset, 80)
            self.assertNotEqual(offset, 999)

    def test_port(self):
        self.assertEqual(get_port('wli', 'tbp'), 8080)
        self.assertEqual(get_port('wli', 'pie'), 9080)
        self.assertEqual(get_port('flieee', 'tbp'), 8085)
        self.assertEqual(get_port('flieee', 'pie'), 9085)

    def test_default_ports(self):
        self.assertEqual(get_port('', 'tbp'), 8999)
        self.assertEqual(get_port('', 'pie'), 9999)


class CreateDevDbTest(TestCase):
    def test_is_valid_db_name(self):
        self.assertTrue(is_valid_db_name('quark_dev_panda'))

    def test_is_valid_db_name_false(self):
        self.assertFalse(is_valid_db_name('quark_dev_panda!'))
