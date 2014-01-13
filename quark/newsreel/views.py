from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from quark.newsreel.models import News
from quark.utils.ajax import json_response


class NewsListView(ListView):
    """View to look at all existing News items and re-order them, editing their
    ranks.
    """
    context_object_name = 'news_items'
    model = News
    template_name = 'newsreel/list.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('newsreel.change_news', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(NewsListView, self).dispatch(*args, **kwargs)


@require_POST
@login_required
@permission_required('newsreel.change_news', raise_exception=True)
def news_reorder(request):
    """Endpoint for saving the ordering (ranks) of newsreel News items."""
    # The "news" post parameter is a list of PKs of News items in the order that
    # they should appear (i.e., ordered from highest to lowest ranking items):
    news_order = request.POST.getlist('news')

    # We will reset the "rank" fields of each of the News items based on the
    # news_order given above. If we walk in reverse order of the news_order
    # list, we can set the rank of the current News item equal to the current
    # loop iteration number (since lower rank value means later in the
    # ordering):
    for rank, news_pk in enumerate(reversed(news_order)):
        news = News.objects.get(pk=news_pk)
        if news.rank != rank:
            news.rank = rank
            news.save(update_fields=['rank'])

    return json_response()
