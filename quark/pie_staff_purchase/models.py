from django.db import models

from quark.auth.models import User
from quark.pie_inventory.models import Item


class Vendor(models.Model):
    """
    Stores simple information about a Vendor. Handling of duplicates
    is done in the user interface, where creating a new vendor is an
    explicit action and existing vendors are accessible through a
    drop-down.
    """
    name = models.CharField(max_length=80)
    url = models.URLField()

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return 'Vendor %s' % self.name


class PartsReceipt(models.Model):
    """
    Stores information on who made the purchase, as well as
    what was purchased, a copy of the receipt, and tracking
    information.
    """
    ARRIVED = 'arv'
    PENDING = 'pnd'
    SHIPPING = 'shp'
    STATUS_OPTIONS = (
        (ARRIVED, 'Arrived'),
        (PENDING, 'Pending'),
        (SHIPPING, 'Shipped'))

    confirmation_number = models.CharField(max_length=20)
    receipt = models.FileField(upload_to='pie/receipts')
    status = models.CharField(
        max_length=3,
        choices=STATUS_OPTIONS)
    total_cost = models.DecimalField(max_digits=8, decimal_places=2)
    tracking_number = models.CharField(max_length=20)
    vendor = models.ForeignKey(Vendor)

    purchaser = models.ForeignKey(User)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        # pylint: disable=E1101
        return 'Parts Receipt for %s at %s' % (
            self.purchaser.get_full_name(), str(self.vendor))


class PartOrder(models.Model):
    """
    Stores information about the individual part that is to be ordered.
    Users will create instances of this each time they want it to be
    ordered. When coordinators make a purchase, they will create a
    PartsReceipt which collects these PartOrders together.

    Vendor information is included to help make it clear to the coord
    what is to be ordered.
    """
    ELECTRICAL = 'ele'
    EXTERNAL = 'ext'
    INTERNAL = 'int'
    IT = 'pit'
    KITDEV = 'kit'
    MECHANICAL = 'mec'
    MENTORSHIP = 'mnt'
    SOFTWARE = 'sft'
    CATEGORIES = (
        (ELECTRICAL, 'Kitdev - Electrical'),
        (EXTERNAL, 'External'),
        (INTERNAL, 'Internal'),
        (IT, 'IT'),
        (KITDEV, 'Kitdev'),
        (MECHANICAL, 'Kitdev - Mechanical'),
        (SOFTWARE, 'Kitdev - Software'))

    item = models.ForeignKey(Item)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)

    vendor = models.ForeignKey(Vendor)
    vendor_part_num = models.CharField(max_length=20)
    vendor_link = models.URLField()

    order = models.ForeignKey(PartsReceipt, null=True)

    notes = models.TextField(blank=True)
    purchase_category = models.CharField(
        max_length=3,
        choices=CATEGORIES)
    submitted_by = models.ForeignKey(User)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        # pylint: disable=E1101
        return 'Part Order for %s, requested by %s' % (
            self.item.name, self.submitted_by.get_full_name())


class PartOrderStatus(models.Model):
    """
    A new status is created every time it changes, allowing for
    a log to be built up on the purchases.
    """
    APPROVED = 'apv'
    ARRIVED = 'arv'
    DENIED = 'dnd'
    PENDING = 'pnd'
    PURCHASED = 'prd'
    REQUIRE_INFO = 'rmi'
    STATUS_OPTIONS = (
        (APPROVED, 'Approved'),
        (ARRIVED, 'Arrived'),
        (DENIED, 'Denied'),
        (PENDING, 'Pending'),
        (PURCHASED, 'Purchased'),
        (REQUIRE_INFO, 'Require more info'))

    comments = models.TextField(blank=True)
    part = models.ForeignKey(PartOrder)
    status = models.CharField(
        max_length=3,
        choices=STATUS_OPTIONS)
    user = models.ForeignKey(User)

    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        # pylint: disable=E1101
        return '(%s) %s' % (
            self.get_status_display(), str(self.part))

    def save(self, *args, **kwargs):
        # Unless explicitly told not to force an insert, always create
        # a new entry in the database when this is saved.
        if kwargs.get('force_insert', True):
            self.pk = None
            kwargs['force_insert'] = True
        models.Model.save(self, *args, **kwargs)
