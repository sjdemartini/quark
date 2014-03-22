import os

from django.core.management.base import CommandError
from django.test import TestCase
from django.test.utils import override_settings
from mock import patch
import mox

from quark.utils import create_dev_db
from quark.utils.dev import DevServer
from quark.utils.management.commands import dev as dev_cmd
import quark.utils as dev_utils


class DevServerTest(TestCase):
    def setUp(self):
        self.server = DevServer()

    def test_offsets_correct_values(self):
        for _, offset in self.server.OFFSETS.items():
            self.assertLessEqual(offset, 998)
            self.assertGreaterEqual(offset, 80)
            self.assertNotEqual(offset, 999)

    def test_port(self):
        self.assertEqual(self.server.get_port('wli'), 8080)
        self.assertEqual(self.server.get_port('flieee'), 8085)

    def test_default_port(self):
        self.assertEqual(self.server.get_port(''), 8999)

    def test_ip_all(self):
        self.assertEqual(self.server.ip, '0.0.0.0')

    def test_ip_localhost(self):
        local_server = DevServer(username='foo', localhost=True)
        self.assertEqual(local_server.ip, 'localhost')

    @patch('django.core.management.ManagementUtility')
    def test_run_exit(self, mock_mgmt):
        """Test that runner exits on KeyboardInterrupt"""
        mock_mgmt.execute(side_effect=KeyboardInterrupt)
        self.server.run_server()
        self.assertTrue(mock_mgmt.execute.called)


class DevUtilsTest(TestCase):
    @override_settings(PROJECT_APPS=[], WORKSPACE_ROOT='root')
    @patch('django.core.management.ManagementUtility')
    def test_no_initial_data(self, mock_mgmt):
        """Don't run loaddata with no available fixtures"""
        dev_utils.load_initial_data()
        self.assertFalse(mock_mgmt.called)

    @override_settings(PROJECT_APPS=['quark.foo', 'thirdparty.bar'],
                       WORKSPACE_ROOT='root')
    @patch('django.core.management.ManagementUtility')
    @patch('glob.glob')
    def test_load_initial_data(self, mock_glob, mock_mgmt):
        fake_glob = {
            'root/quark/foo/fixtures/*.yaml': ['file1'],
            'root/thirdparty/bar/fixtures/*.yaml': ['file2', 'file3'],
        }
        mock_glob.side_effect = lambda x: fake_glob[x]
        mock_mgmt.execute.side_effect = lambda arg: self.assertEqual(
            arg, ['manage.py', 'loaddata', 'file1', 'file2', 'file3'])
        dev_utils.load_initial_data()
        self.assertEqual(mock_glob.call_count, 2)

    @override_settings(PROJECT_APPS=[], WORKSPACE_ROOT='root')
    @patch('django.core.management.ManagementUtility')
    @patch('quark.utils.load_initial_data')
    def test_update_db(self, mock_data, mock_mgmt):
        """
        Ensure update_db goes through the 2 management steps, which assumes
        there are no PROJECT_APPS, or load_initial_data is stubbed out.
        """
        dev_utils.update_db()
        self.assertEqual(mock_mgmt.call_count, 2)
        self.assertEqual(mock_data.call_count, 1)


class DevCommandTest(TestCase):
    def setUp(self):
        self.command = dev_cmd.Command()

    @override_settings(PROJECT_APPS=[])
    @patch.dict(os.environ, {'RUN_MAIN': 'true'})
    @patch('getpass.getuser')
    @patch('quark.utils.update_db')
    @patch.object(dev_cmd.DevServer, 'run_server')
    def test_handle(self, mock_server, mock_update, mock_user):
        """Running dev does not raise a KeyError or CommandError"""
        # Note that we mock out the RUN_MAIN environment variable, which would
        # be set by Django when running the management command the first time
        mock_user.return_value = 'foo'
        self.command.handle()
        self.assertTrue(mock_update.called)
        self.assertTrue(mock_server.called)

    def test_handle_fail_too_many_args(self):
        self.assertRaises(CommandError, self.command.handle, 'foo')


class CreateDevDBTest(TestCase):
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
        cursor.execute('CREATE DATABASE IF NOT EXISTS quark_dev_foo'
                       ' CHARACTER SET utf8'
                       ' COLLATE utf8_unicode_ci')
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
        cursor.execute('CREATE DATABASE IF NOT EXISTS quark_dev_foo'
                       ' CHARACTER SET utf8'
                       ' COLLATE utf8_unicode_ci')
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
