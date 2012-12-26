from django.test import TestCase

from quark.auth.models import User
from quark.pie_inventory.models import Item
from quark.pie_staff_purchase.models import PartOrder
from quark.pie_staff_purchase.models import PartOrderStatus
from quark.pie_staff_purchase.models import Vendor


class PartOrderStatusTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'test_user', 'pit@pioneers.berkeley.edu', 'testpw')
        self.user.save()

        self.vendor = Vendor(
            name='McMaster',
            url='mcmaster.com')
        self.vendor.save()

        # Note: Not specifying an image on purpose.
        self.item = Item(
            name='thingamajig',
            wiki='pioneers.berkeley.edu/staff/wiki/thingamajig')
        self.item.save()

        self.part_order = PartOrder(
            item=self.item,
            quantity=1,
            unit_price=9000,
            vendor=self.vendor,
            vendor_part_num='1337',
            vendor_link='mcmaster.com/1337',
            purchase_category='Mentorship',
            submitted_by=self.user)
        self.part_order.save()

    def test_save(self):
        part_status = PartOrderStatus(
            part=self.part_order,
            status=PartOrderStatus.ARRIVED,
            user=self.user)
        part_status.save()

        part_statuses = PartOrderStatus.objects.all()
        self.assertEquals(len(part_statuses), 1)

        part_statuses[0].save()
        part_statuses = PartOrderStatus.objects.all()
        self.assertEquals(len(part_statuses), 2)

    def test_save_override(self):
        part_status = PartOrderStatus(
            part=self.part_order,
            status=PartOrderStatus.ARRIVED,
            user=self.user)
        part_status.save()

        part_statuses = PartOrderStatus.objects.all()
        self.assertEquals(len(part_statuses), 1)

        part_status.status = PartOrderStatus.PENDING
        part_status.save(force_insert=False)
        part_statuses = PartOrderStatus.objects.all()
        self.assertEquals(len(part_statuses), 1)
        self.assertEquals(part_statuses[0].status, PartOrderStatus.PENDING)
