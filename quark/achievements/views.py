from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse_lazy
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import ListView

from quark.achievements.forms import UserAchievementForm
from quark.achievements.models import Achievement
from quark.achievements.models import UserAchievement


class AchievementDetailView(DetailView):
    context_object_name = 'achievement'
    model = Achievement
    template_name = 'achievements/achievement_detail.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AchievementDetailView, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(
            short_name=self.kwargs['achievement_short_name'])

    def get_context_data(self, **kwargs):
        context = super(AchievementDetailView, self).get_context_data(**kwargs)

        # Select the viewer's secret and private achievements so that they
        # can only see the ones they've unlocked.
        viewer_achievements = self.request.user.userachievement_set
        context['viewable_hidden_achievements'] = Achievement.objects.filter(
            userachievement__in=viewer_achievements.values_list('id')).exclude(
            privacy='public')

        # Find all users that have unlocked the achievement
        user_achievements = UserAchievement.objects.filter(
            achievement__short_name=context['achievement'].short_name).exclude(
            acquired=False)
        users_with_achievement = get_user_model().objects.filter(
            userachievement__in=user_achievements.values_list('id'))
        context['users_with_achievement'] = users_with_achievement.order_by(
            'last_name')

        # Find other achievements in same sequence to display related.
        context['related_achievements'] = Achievement.objects.filter(
            sequence=context['achievement'].sequence).exclude(
            short_name=context['achievement'].short_name)

        return context


class LeaderboardListView(ListView):
    # select all users with >0 scores to display on leaderboard
    # and omits all users with 0 or negative scores
    context_object_name = 'leader_list'
    template_name = 'achievements/leaderboard.html'
    paginate_by = 35  # separates leaders into pages of 35 each

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LeaderboardListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        leaders = get_user_model().objects.filter(
            userachievement__acquired=True).select_related(
            'userprofile').annotate(score=Sum(
            'userachievement__achievement__points')).filter(
            score__gte=0).order_by('-score')

        if len(leaders) > 0:
            max_score = leaders[0].score or 0
        else:
            max_score = 0

        # Create a list of "leader" entries, where each entry is a dictionary
        # that includes the user, their rank on the leaderboard (1st, 2nd,
        # etc.), and their leaderboard width "factor" (see below for details).
        leader_list = []
        if max_score > 0:

            prev_value = -1
            prev_rank = 1

            for i, leader in enumerate(leaders, start=prev_rank):
                # factor used for CSS width property (percentage). Use 70.0 as
                # the maximum width (i.e. top scorer has width 70%), including
                # adding 2.5 to every factor to make sure that there is enough
                # room for text to be displayed.
                factor = 2.5 + leader.score * 67.5 / max_score
                if leader.score == prev_value:
                    rank = prev_rank
                else:
                    rank = i

                prev_rank = rank
                prev_value = leader.score

                # Add the leader entry to the list
                leader_list.append({'user': leader,
                                    'factor': factor,
                                    'rank': rank})
        return leader_list


class UserAchievementAssignView(FormView):
    """Provide an interface for the viewer to assign achievements to users."""
    form_class = UserAchievementForm
    model = UserAchievement
    success_url = reverse_lazy('achievements:assign')
    template_name = 'achievements/assign.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('achievements.add_userachievement',
                            raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(UserAchievementAssignView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.save(assigner=self.request.user)
        achievement = form.cleaned_data.get('achievement')
        users = form.cleaned_data.get('users')

        users_namestring = ', '.join(
            [user.userprofile.get_common_name() for user in users])

        messages.success(
            self.request,
            'Achievement {achievement} assigned to {names}'.format(
                achievement=achievement.name, names=users_namestring))
        return super(UserAchievementAssignView, self).form_valid(form)


class UserAchievementListView(ListView):
    context_object_name = 'unlocked_list'
    template_name = 'achievements/user.html'
    display_user = None
    user_achievements = None
    user_points = 0

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.display_user = get_object_or_404(get_user_model(),
                                              id=self.kwargs['user_id'])
        self.user_achievements = self.display_user.userachievement_set.exclude(
            acquired=False).order_by('achievement__rank')
        return super(UserAchievementListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        queryset = self.user_achievements

        for userachievement in queryset:
            self.user_points += userachievement.achievement.points

        if self.request.user != self.display_user:
            queryset = queryset.exclude(achievement__privacy='private')

        return queryset

    def get_context_data(self, **kwargs):
        context = super(UserAchievementListView, self).get_context_data(
            **kwargs)
        context['display_user'] = self.display_user
        context['user_points'] = self.user_points
        context['user_num_achievements'] = self.user_achievements.count()

        # Select achievements that have ids not found in the list of obtained
        # user achievements (i.e. they have not been acquired yet or don't
        # exist), and obtain goals and progresses.
        locked_achievements = Achievement.objects.exclude(
            userachievement__in=self.user_achievements).exclude(
            privacy='private').order_by('rank')
        progresses = []
        for achievement in locked_achievements:
            try:
                user_achievement = UserAchievement.objects.get(
                    user=self.display_user, achievement=achievement)
                progresses.append(user_achievement.progress)
            except UserAchievement.DoesNotExist:
                progresses.append(0)
        locked_list = [{'achievement': t[0], 'progress': t[1]}
                       for t in zip(locked_achievements, progresses)]
        context['locked_list'] = locked_list

        # Select hidden achievements the viewer has unlocked so that they are
        # visible in other users' pages.
        viewer_achievements = self.request.user.userachievement_set
        context['viewer_secret_achievements'] = Achievement.objects.filter(
            userachievement__in=viewer_achievements.values_list('id')).filter(
            privacy='secret')

        return context
