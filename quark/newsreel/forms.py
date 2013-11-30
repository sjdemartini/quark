from django import forms

from quark.newsreel.models import News


class NewsForm(forms.ModelForm):
    class Meta(object):
        model = News
        fields = ('title', 'blurb', 'image')
