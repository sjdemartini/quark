import json
import os

from django.conf import settings


NOIRO_MEDIA_LOCATION = '/var/noiro/media'


def get_json_data(filename):
    """Return a list of json data for a model, given a filename."""
    data_path = os.path.join(
        settings.WORKSPACE_ROOT, 'scripts', 'data', filename)
    with open(data_path, 'r') as json_file:
        return json.load(json_file)
