#!/usr/bin/env python
import getpass
import MySQLdb
import re
import sys

KEY_PATH = '/home/tbp/private'
if KEY_PATH not in sys.path:
    sys.path.append(KEY_PATH)
# pylint: disable=F0401
from quark_keys import DEV_DB_PASSWORD as DB_PASSWORD

DB_USER = 'quark_dev'


def is_valid_db_name(name):
    """
    Name validation using regex.
    Should only contain letters, digits, underscores
    """
    result = re.search('[^A-Za-z0-9_]', name)
    return result is None


def create_dev_db(username, quiet=False):
    """
    Connects to the database using production credentials.
    Creates a new dev database if it doesn't exist.
    Passes through any errors/exceptions as a result of a bad SQL statement.

    Returns the created (or existing) database name or None if it failed.
    """
    db_name = '%s_%s' % (DB_USER, username)
    if not is_valid_db_name(db_name):
        return False

    result = False
    db = None
    try:
        db = MySQLdb.connect(user=DB_USER, passwd=DB_PASSWORD)
        cr_cursor = db.cursor()
        cr_cursor.execute('CREATE DATABASE IF NOT EXISTS %s'
                          ' CHARACTER SET utf8'
                          ' COLLATE utf8_unicode_ci' % db_name)
        cr_cursor.close()
        db.commit()

        # Be paranoid. Ensure new db is created and change has been commited.
        ex_cursor = db.cursor()
        ex_cursor.execute('SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA'
                          ' WHERE SCHEMA_NAME = %s', [db_name])
        result = ex_cursor.fetchone() is not None
        ex_cursor.close()
    finally:
        if db:
            db.close()

    if not quiet:
        if result:
            print 'Success! Dev database "%s" was created' % db_name
        else:
            print 'Error: Dev database "%s" was not created' % db_name

    return result


def main():
    username = getpass.getuser()
    print 'Creating database for %s' % username
    create_dev_db(username)


if __name__ == '__main__':
    main()
