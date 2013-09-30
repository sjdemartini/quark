from django.core.management import call_command

from scripts.import_base_models import import_terms
from scripts.import_courses_models import import_courses
from scripts.import_courses_models import import_course_instances
from scripts.import_courses_models import import_departments
from scripts.import_courses_models import import_instructors


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
# The json files needed in the scripts/data/ directory are:
# noiro_main.semester.json
# courses.department.json
# courses.course.json
# courses.instructor.json
# courses.section.json

print('Backing up all current data to scripts/data/backup.json')
backup = open('scripts/data/backup.json', 'w')
call_command('dumpdata', stdout=backup)
backup.close()

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

print('All models successfully imported.')
