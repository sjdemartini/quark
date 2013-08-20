from django.db import models


class PastPresident(models.Model):
    name = models.CharField(max_length=100)
    term = models.CharField(
        max_length=100,
        help_text='Spring 1950 or 1930-1931 or Fall 1967 - Spring 1968')
    email = models.EmailField(blank=True)
    bio = models.TextField(
        blank=True,
        help_text='Shows up on the index page')
    picture = models.ImageField(
        upload_to='images/past_pres/',
        blank=True)
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text='Ex: Building On Foundations - Jo Kay Chan - Spring 1999')
    summary = models.TextField(
        blank=True,
        help_text='Quick summary of status of the chapter and future vision')
    body = models.TextField(
        blank=True,
        help_text='Main multi-paragraph text')
    contributions = models.TextField(
        blank=True,
        help_text='Use markdown syntax with asterisks for bullets in list')
    ordering_number = models.IntegerField(
        blank=True, db_index=True,
        help_text=('Number used to order presidents. '
                   'Higher numbers for more recent presidents'))

    def __unicode__(self):
        return '%s (%s)' % (self.name, self.term)

    class Meta(object):
        ordering = ('-ordering_number',)
