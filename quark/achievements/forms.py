from chosen import forms as chosen_forms
from django import forms

from quark.achievements.models import Achievement
from quark.achievements.models import UserAchievement
from quark.base.forms import ChosenTermMixin
from quark.user_profiles.fields import UserCommonNameMultipleChoiceField


class UserAchievementForm(ChosenTermMixin, forms.Form):
    achievement = chosen_forms.ChosenModelChoiceField(
        queryset=Achievement.objects.filter(manual=True))
    users = UserCommonNameMultipleChoiceField()
    explanation = forms.CharField(
        required=False,
        help_text=('Any extra metadata or notes about what the user did to '
                   'earn this achievement.'))

    class Meta(object):
        model = UserAchievement
        fields = ('achievement', 'users', 'term', 'explanation')
        widgets = {
            'achievement': chosen_forms.ChosenSelect(),
        }

    def save(self, assigner):
        """For each user specified in the form, this calls the achievement's
        assign method to give it to that user with any specified data.

        The assigner argument is the user who is giving the achievement,
        usually self.request.user.
        """
        term = self.cleaned_data.get('term')
        users = self.cleaned_data.get('users')
        achievement = self.cleaned_data.get('achievement')
        explanation = self.cleaned_data.get('explanation')

        for user in users:
            achievement.assign(user, term=term, explanation=explanation,
                               assigner=assigner)
