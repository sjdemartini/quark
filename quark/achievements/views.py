from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils.decorators import method_decorator
from django.views.generic import ListView


class LeaderboardListView(ListView):
    # select all users with >0 scores to display on leaderboard
    # and omits all users with 0 or negative scores
    context_object_name = 'leader_list'
    template_name = 'achievements/leaderboard.html'
    paginate_by = 25  # separates leaders into pages of 25 each

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LeaderboardListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        leaders = get_user_model().objects.select_related('user').annotate(
            score=Sum('userachievement__achievement__points')).filter(
                score__gte=0).order_by('-score')

        if len(leaders) > 0:
            max_score = leaders[0].score or 0
        else:
            max_score = 0

        factors = []
        ranks = []

        # get factors and ranks for everyone in leaderboard
        if max_score > 0:

            prev_value = -1
            prev_rank = 1

            for i, leader in enumerate(leaders, start=prev_rank):
                # factor used for CSS width property (percentage). Use 70.0
                # as the maximum width (i.e. top scorer has width 70%), and
                # add 2.5 to make sure that there is enough room for text to
                # be displayed
                factor = 2.5 + leader.score * 67.5 / max_score
                if leader.score != prev_value:
                    rank = i
                else:
                    rank = prev_rank

                prev_rank = rank
                prev_value = leader.score

                ranks.append(rank)
                factors.append(factor)

        # create a list that combines the users on the leaderboard, their
        # rank, and their factor for easier iteration in the html template
        leader_list = [{'user': t[0], 'rank': t[1], 'factor': t[2]}
                       for t in zip(leaders, ranks, factors)]

        return leader_list
