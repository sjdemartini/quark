import mox

from django.core.management.base import CommandError
from django.test import TestCase
from django.test.utils import override_settings

from quark.utils import create_dev_db
from quark.utils.management.commands import dev


class DevTest(TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.command = dev.Command()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_offsets_correct_values(self):
        for _, offset in dev.OFFSETS.items():
            self.assertLessEqual(offset, 998)
            self.assertGreaterEqual(offset, 80)
            self.assertNotEqual(offset, 999)

    def test_port(self):
        self.assertEqual(self.command.get_port('wli', 'tbp'), 8080)
        self.assertEqual(self.command.get_port('wli', 'pie'), 9080)
        self.assertEqual(self.command.get_port('flieee', 'tbp'), 8085)
        self.assertEqual(self.command.get_port('flieee', 'pie'), 9085)

    def test_default_ports(self):
        self.assertEqual(self.command.get_port('', 'tbp'), 8999)
        self.assertEqual(self.command.get_port('', 'pie'), 9999)

    def test_no_port(self):
        self.assertRaises(
            CommandError, self.command.get_port, '', 'asdf')

    @override_settings(PROJECT_APPS=['quark.foo', 'thirdparty.bar'],
                       WORKSPACE_ROOT='root')
    def test_load_initial_data(self):
        self.mox.StubOutWithMock(dev, 'execute_from_command_line')
        self.mox.StubOutWithMock(dev, 'glob')

        # Disable for the AndReturn calls.
        # pylint: disable=E1101
        dev.glob.glob(
            'root/quark/foo/fixtures/*.yaml').AndReturn(['file1'])
        dev.glob.glob(
            'root/thirdparty/bar/fixtures/*.yaml').AndReturn(
                ['file2', 'file3'])
        # pylint: enable=E1101

        dev.execute_from_command_line(
            ['manage.py', 'loaddata', 'file1', 'file2', 'file3'])

        self.mox.ReplayAll()
        self.command.load_initial_data()
        self.mox.VerifyAll()

    @override_settings(PROJECT_APPS=[], WORKSPACE_ROOT='root')
    def test_no_initial_data(self):
        self.mox.ReplayAll()
        self.command.load_initial_data()
        self.mox.VerifyAll()

    @override_settings(PROJECT_APPS=[])
    def test_handle(self):
        # We don't want to run the resulting run_command calls, so we stub it
        # out. We just want to know that it doesn't raise an exception.
        self.mox.StubOutWithMock(dev, 'execute_from_command_line')
        self.mox.StubOutWithMock(dev.getpass, 'getuser')

        # Force shared port.
        dev.getpass.getuser().AndReturn('foo')

        dev.execute_from_command_line(['manage.py', 'syncdb'])
        dev.execute_from_command_line(['manage.py', 'migrate'])
        dev.execute_from_command_line(
            ['manage.py', 'collectstatic', '--noinput'])
        dev.execute_from_command_line(
            ['manage.py', 'runserver', '0.0.0.0:8999'])
        self.mox.ReplayAll()
        self.command.handle('tbp')
        self.mox.VerifyAll()

    def test_handle_fail_few_arguments(self):
        self.mox.StubOutWithMock(dev, 'execute_from_command_line')
        self.assertRaises(
            CommandError, self.command.handle)

    def test_handle_fail_too_many_args(self):
        self.mox.StubOutWithMock(dev, 'execute_from_command_line')
        self.assertRaises(
            CommandError, self.command.handle, 'foo', 'bar')


class CreateDevDbTest(TestCase):
    def setUp(self):
        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_is_valid_db_name(self):
        self.assertTrue(create_dev_db.is_valid_db_name('quark_dev_panda'))

    def test_is_valid_db_name_false(self):
        self.assertFalse(create_dev_db.is_valid_db_name('quark_dev_panda!'))

    def test_create_dev_db(self):
        self.mox.StubOutWithMock(create_dev_db.MySQLdb, 'connect')
        create_dev_db.DB_PASSWORD = 'bar'

        db = self.mox.CreateMockAnything()
        create_dev_db.MySQLdb.connect(
            user='quark_dev', passwd='bar').AndReturn(db)

        cursor = self.mox.CreateMockAnything()
        db.cursor().AndReturn(cursor)
        cursor.execute('CREATE DATABASE IF NOT EXISTS quark_dev_foo')
        cursor.close()
        db.commit()

        ex_cursor = self.mox.CreateMockAnything()
        db.cursor().AndReturn(ex_cursor)
        ex_cursor.execute(
            ('SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA'
             ' WHERE SCHEMA_NAME = %s'), ['quark_dev_foo'])
        ex_cursor.fetchone().AndReturn('result')
        ex_cursor.close()

        db.close()

        self.mox.ReplayAll()
        self.assertTrue(create_dev_db.create_dev_db('foo'))
        self.mox.VerifyAll()

    def test_fail_to_create_db(self):
        self.mox.StubOutWithMock(create_dev_db.MySQLdb, 'connect')
        create_dev_db.DB_PASSWORD = 'bar'

        db = self.mox.CreateMockAnything()
        create_dev_db.MySQLdb.connect(
            user='quark_dev', passwd='bar').AndReturn(db)

        cursor = self.mox.CreateMockAnything()
        db.cursor().AndReturn(cursor)
        cursor.execute('CREATE DATABASE IF NOT EXISTS quark_dev_foo')
        cursor.close()
        db.commit()

        ex_cursor = self.mox.CreateMockAnything()
        db.cursor().AndReturn(ex_cursor)
        ex_cursor.execute(
            ('SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA'
             ' WHERE SCHEMA_NAME = %s'), ['quark_dev_foo'])
        ex_cursor.fetchone().AndReturn(None)
        ex_cursor.close()

        db.close()

        self.mox.ReplayAll()
        self.assertFalse(create_dev_db.create_dev_db('foo'))
        self.mox.VerifyAll()

    def test_fail_connect_with_db(self):
        self.mox.StubOutWithMock(create_dev_db.MySQLdb, 'connect')
        create_dev_db.DB_PASSWORD = 'bar'

        db = self.mox.CreateMockAnything()
        create_dev_db.MySQLdb.connect(
            user='quark_dev', passwd='bar').AndReturn(db)

        cursor = self.mox.CreateMockAnything()
        db.cursor().AndReturn(cursor)
        cursor.execute(mox.IgnoreArg()).AndRaise(Exception)

        db.close()

        self.mox.ReplayAll()
        self.assertRaises(Exception, create_dev_db.create_dev_db, 'foo')
        self.mox.VerifyAll()

    def test_fail_connect_without(self):
        self.mox.StubOutWithMock(create_dev_db.MySQLdb, 'connect')
        create_dev_db.DB_PASSWORD = 'bar'

        create_dev_db.MySQLdb.connect(
            user='quark_dev', passwd='bar').AndReturn(None)

        self.mox.ReplayAll()
        self.assertRaises(Exception, create_dev_db.create_dev_db, 'foo')
        self.mox.VerifyAll()

    def test_fail_bad_db_name(self):
        self.assertFalse(create_dev_db.create_dev_db('foo!??!'))

    def test_main(self):
        self.mox.StubOutWithMock(create_dev_db.getpass, 'getuser')
        self.mox.StubOutWithMock(create_dev_db, 'create_dev_db')
        create_dev_db.getpass.getuser().AndReturn('foo')

        create_dev_db.create_dev_db('foo')

        self.mox.ReplayAll()
        create_dev_db.main()
        self.mox.VerifyAll()
