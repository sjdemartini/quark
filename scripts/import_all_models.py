from django.core.management import call_command

from scripts.alter_tables import alter_tables
from scripts.import_base_models import import_terms
from scripts.import_courses_models import import_courses
from scripts.import_courses_models import import_course_instances
from scripts.import_courses_models import import_departments
from scripts.import_courses_models import import_instructors
from scripts.import_events_models import import_events
from scripts.import_events_models import import_event_attendances
from scripts.import_events_models import import_event_sign_ups
from scripts.import_events_models import import_event_types
from scripts.import_exams_models import import_exams
from scripts.import_exams_models import import_exam_flags
from scripts.import_project_reports_models import import_project_reports
from scripts.import_resumes_models import import_resumes
from scripts.import_user_models import delete_user_profiles
from scripts.import_user_models import delete_users
from scripts.import_user_models import import_user_profiles
from scripts.import_user_models import import_users


# All functions will look for files with names like:
# scripts/data/<noiro_app>.<noiro_model>.json
#
# First, create the data folder in the scripts folder:
# mkdir <path_to_repo>/scripts/data
# Then to get the json files, go to /var/noiro/<commit_hash>/noiro and run:
# ./manage.py dumpdata <app>.<model> > \
#     <path_to_repo>/scripts/data/<app>.<model>.json
#
# Then to run this script to import all models, do:
# ./manage.py shell
# and then:
# execfile('scripts/import_all_models.py')
#
# A backup of all current data before importing will also be saved to
# scripts/data/backup.json in case something goes wrong with importing.
#
# Certain tables will also be altered before any importing so that no errors
# will occur while importing fields encoded in UTF-8.
#
# The json files needed in the scripts/data/ directory are:
# noiro_main.semester.json
# courses.department.json
# courses.course.json
# courses.instructor.json
# courses.section.json
# auth.user.json
# user_profiles.userprofile.json
# projects.projectreport.json
# events.eventtype.json
# events.event.json
# events.eventsignup.json
# events.eventattendance.json
# noiro_main.officer.json
# user_profiles.resume.json
# examfiles.exam.json
# examfiles.examflag.json

print('Backing up all current data to scripts/data/backup.json')
backup = open('scripts/data/backup.json', 'w')
call_command('dumpdata', stdout=backup)
backup.close()

print('Altering certain tables so that they can handle UTF-8 fields.')
alter_tables()

print('Importing all models from noiro.')

print('Importing terms.')
import_terms()

print('Importing departments.')
import_departments()
print('Importing courses.')
import_courses()
print('Importing instructors.')
import_instructors()
print('Importing course instances.')
import_course_instances()

print('Deleting current users.')
delete_users()
print('Importing users.')
import_users()
print('Deleting current user profiles.')
delete_user_profiles()
print('Importing user profiles.')
import_user_profiles()

print('Importing project reports.')
import_project_reports()

print('Importing event types.')
import_event_types()
print('Importing events.')
import_events()
print('Importing event sign ups.')
import_event_sign_ups()
print('Importing event attendances.')
import_event_attendances()

print('Importing officers.')
import_officers()

print('Importing resumes.')
import_resumes()

print('Importing exams.')
import_exams()
print('Importing exam flags.')
import_exam_flags()

print('All models successfully imported.')
