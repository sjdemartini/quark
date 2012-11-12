import mox

from django.test import TestCase

from quark.utils import create_dev_db
from quark.utils import dev


class DevTest(TestCase):
    def setUp(self):
        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_offsets_correct_values(self):
        for _, offset in dev.OFFSETS.items():
            self.assertLessEqual(offset, 998)
            self.assertGreaterEqual(offset, 80)
            self.assertNotEqual(offset, 999)

    def test_port(self):
        self.assertEqual(dev.get_port('wli', 'tbp'), 8080)
        self.assertEqual(dev.get_port('wli', 'pie'), 9080)
        self.assertEqual(dev.get_port('flieee', 'tbp'), 8085)
        self.assertEqual(dev.get_port('flieee', 'pie'), 9085)

    def test_default_ports(self):
        self.assertEqual(dev.get_port('', 'tbp'), 8999)
        self.assertEqual(dev.get_port('', 'pie'), 9999)

    def test_no_port(self):
        self.assertIsNone(dev.get_port('', 'asdf'))

    def test_error_out(self):
        self.assertRaises(SystemExit, dev.error_out)

    def test_run_server(self):
        # We don't want to run the resulting run_command calls, so we stub it
        # out. We just want to know that it doesn't raise an exception.
        self.mox.StubOutWithMock(dev, 'run_command')
        self.mox.StubOutWithMock(dev.getpass, 'getuser')

        # Force shared port.
        dev.getpass.getuser().AndReturn('foo')

        dev.run_command('python manage.py syncdb')
        dev.run_command('python manage.py migrate')
        dev.run_command('python manage.py collectstatic')
        dev.run_command('python manage.py runserver 0.0.0.0:8999')
        self.mox.ReplayAll()
        dev.run_server('tbp')
        self.mox.VerifyAll()

    def test_run_server_fail(self):
        # In case this test doesn't do as we expect, we don't want to run the
        # resulting run_command calls, so we stub it out.
        self.mox.StubOutWithMock(dev, 'run_command')
        self.assertRaises(SystemExit, dev.run_server, 'asdf')

    def test_run_command(self):
        self.mox.StubOutWithMock(dev.subprocess, 'call')
        dev.subprocess.call('foo', shell=True).AndReturn(0)
        self.mox.ReplayAll()
        self.assertTrue(dev.run_command('foo'))
        self.mox.VerifyAll()

    def test_run_command_fail(self):
        self.mox.StubOutWithMock(dev.subprocess, 'call')
        dev.subprocess.call('foo', shell=True).AndReturn(1)
        self.mox.ReplayAll()
        self.assertRaises(SystemExit, dev.run_command, 'foo')
        self.mox.VerifyAll()

    def test_main(self):
        self.mox.StubOutWithMock(dev, 'run_server')
        dev.sys.argv = ['dev', 'tbp']
        dev.run_server('tbp')
        self.mox.ReplayAll()
        dev.main()
        self.mox.VerifyAll()

    def test_main_fail_few_arguments(self):
        self.mox.StubOutWithMock(dev, 'run_server')
        dev.sys.argv = ['foo']
        self.assertRaises(SystemExit, dev.main)

    def test_main_fail_too_many_args(self):
        self.mox.StubOutWithMock(dev, 'run_server')
        dev.sys.argv = ['foo', 'bar', 'baz']
        self.assertRaises(SystemExit, dev.main)


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
