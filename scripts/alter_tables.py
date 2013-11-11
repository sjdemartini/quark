from django.db import connection


TABLES = [
    'user_profiles_studentorguserprofile',
    'project_reports_projectreport',
    'events_event',
    'events_eventsignup']


def alter_tables():
    """Alter certain tables so that they can handle UTF-8 fields."""
    cursor = connection.cursor()
    for table in TABLES:
        cursor.execute(
            'ALTER TABLE {} CONVERT TO CHARACTER SET utf8 COLLATE'
            ' utf8_unicode_ci;'.format(table))
