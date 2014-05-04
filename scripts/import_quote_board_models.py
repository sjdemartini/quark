from dateutil import parser
from django.contrib.auth import get_user_model

from quark.quote_board.models import Quote
from scripts import get_json_data


user_model = get_user_model()


def import_quotes():
    # pylint: disable=E1103
    models = get_json_data('quoteboard.quote.json')
    for model in models:
        fields = model['fields']
        pk = model['pk']

        quote, _ = Quote.objects.get_or_create(
            pk=pk,
            quote=fields['quote_line'],
            submitter=user_model.objects.get(pk=fields['poster']))
        quote.speakers.add(user_model.objects.get(pk=fields['speaker']))
        # Get a queryset of the single object so that update can be called,
        # which doesn't call save and allows fields with auto_now_add=True to be
        # overridden
        quote = Quote.objects.filter(pk=pk)
        quote.update(time=parser.parse(fields['quote_time']).date())
