from django.db import models

from quark.auth.models import User
from quark.pie_inventory.models import Item


class ToolStatus(models.Model):
    CABINET = 'cab'
    CHECKED_OUT = 'c-o'
    BROKEN = 'brk'
    REPAIRING = 'rep'
    MISSING = 'mis'
    RETIRED = 'ret'

    STATUS_CHOICES = (
        (CABINET, 'cabinet'),
        (CHECKED_OUT, 'checked out'),
        (BROKEN, 'broken'),
        (REPAIRING, 'repairing'),
        (MISSING, 'missing'),
        (RETIRED, 'retired')
    )

    authorizing_user = models.ForeignKey(User, related_name='+')
    user = models.ForeignKey(User, related_name='+')
    instance = models.ForeignKey('ToolInstance')
    status = models.CharField(max_length=3,
                              choices=STATUS_CHOICES,
                              default=CABINET)
    created = models.DateTimeField(auto_now_add=True)


class ToolInstance(models.Model):
    id_code = models.CharField(max_length=40,
                               db_index=True,
                               unique=True)
    type = models.ForeignKey(Item)
    cost = models.IntegerField(default=0)
    purchase_date = models.DateTimeField(auto_now_add=True)
