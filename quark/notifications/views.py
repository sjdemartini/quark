from django.views.decorators.http import require_POST

from quark.notifications.models import Notification
from quark.utils.ajax import json_response


@require_POST
def clear_notification(request, notification_pk):
    try:
        notification = Notification.objects.get(
            user=request.user, pk=notification_pk)
        notification.cleared = True
        notification.save()
        return json_response()
    except Notification.DoesNotExist:
        return json_response(status=400)
