from django.contrib.auth import get_user_model
from django.test import TestCase

from quark.newsreel.models import News


class NewsTesting(TestCase):
    """Tests for the News model."""
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='officer',
            email='it@tbp.berkeley.edu',
            password='testofficerpw',
            first_name='Bentley',
            last_name='Bent')

    def test_rank_setting(self):
        self.assertEqual(0, News.objects.all().count())

        # Ensure that the first News object is assigned a rank of 1 after
        # save() is done.
        news_obj = News(
            title='Look at some news!',
            blurb='If you can see it, the test worked!',
            creator=self.user)
        self.assertIsNone(news_obj.rank)
        news_obj.save()
        self.assertEqual(1, news_obj.rank)

        # Subsequent news objects should be given rank one higher than the
        # current max rank
        news_obj = News(title='Second news', blurb='Double the news!',
                        creator=self.user)
        news_obj.save()
        self.assertEqual(2, news_obj.rank)

        # Change an existing item's rank to a higher value
        news_obj.rank = 20
        news_obj.save()
        news_obj = News(title='Third news', blurb='Triple the news?!',
                        creator=self.user)
        news_obj.save()
        self.assertEqual(21, news_obj.rank)

    def test_news_ordering(self):
        # Create 3 News objects, which will be given sequential rank (so that
        # the last one created should be first in ordering)
        news_1 = News(title='First', blurb='A news story', creator=self.user)
        news_1.save()
        news_2 = News(title='Second', blurb='More news', creator=self.user)
        news_2.save()
        news_3 = News(title='Third', blurb='Final news', creator=self.user)
        news_3.save()

        # Check that the queryset is returned in the correct order
        self.assertEqual(list(News.objects.all()), [news_3, news_2, news_1])

        # Make the news_2 rank a higher number, so it should now come first
        # in the ordering
        news_2.rank = 5
        news_2.save()
        self.assertEqual(list(News.objects.all()), [news_2, news_3, news_1])
