from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.utils import timesince
from django.utils import timezone

from quark.project_reports.models import ProjectReport
from quark.notifications.models import Notification


def notifications(request):
    """Get all notifications for a user that have not been cleared."""
    if request.user.is_authenticated():
        # Create notifications for project reports that are late from all terms
        project_reports = ProjectReport.objects.filter(
            author=request.user,
            complete=False,
            date__lt=timezone.localtime(timezone.now()).date())
        content_type = ContentType.objects.get_for_model(ProjectReport)
        for project_report in project_reports:
            notification, _ = Notification.objects.get_or_create(
                user=request.user,
                status=Notification.NEGATIVE,
                content_type=content_type,
                object_pk=project_report.pk,
                title='Missing Project Report',
                subtitle=project_report.title,
                url=reverse('project-reports:edit', args=(project_report.pk,)))
            # Description must be unicode because timesince generates a unicode
            # string
            notification.description = u'{} overdue'.format(
                timesince.timesince(project_report.date))
            notification.cleared = False
            notification.save()

        user_notifications = Notification.objects.filter(
            user=request.user, cleared=False)
        if user_notifications.exists():
            return {'notifications': user_notifications}
    return {}
