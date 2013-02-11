from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from quark.auth.models import User
from quark.pie_inventory.models import Item
from quark.pie_staff_purchase.models import PartOrder
from quark.pie_staff_purchase.models import PartOrderStatus
from quark.pie_staff_purchase.models import Vendor


class PartOrderStatusTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='pit@pioneers.berkeley.edu',
            password='testpw',
            first_name='Testy',
            last_name='User')

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


class PartOrderManagerTest(TestCase):
    fixtures = ['test_data/parts_receipt.yaml']

    def setUp(self):
        self.part2 = PartOrder.objects.get(pk=2)
        self.part3 = PartOrder.objects.get(pk=3)
        self.coord_user = User.objects.get(username='coorduser')
        self.staff_user = User.objects.get(username='staffuser')

    def make_part_order(self, item, vendor, user):
        return PartOrder(
            item=item,
            quantity=3,
            unit_price=4.55,
            vendor=vendor,
            vendor_part_num=1234,
            vendor_link='google.com/1234',
            purchase_category=PartOrder.IT,
            submitted_by=user)

    def test_approved_queryset_basic(self):
        # Tests with 1 denied status and 1 approved status
        self.assertEquals(len(PartOrder.objects.approved()), 1)

        PartOrderStatus(
            part=self.part2,
            status=PartOrderStatus.PURCHASED,
            user=self.coord_user).save()
        self.assertEquals(len(PartOrder.objects.approved()), 0)

        PartOrderStatus(
            part=self.part2,
            status=PartOrderStatus.ARRIVED,
            user=self.coord_user).save()
        self.assertEquals(len(PartOrder.objects.approved()), 0)

    def test_approved_queryset_approve_deny(self):
        # Tests with 1 approved status and a denied part being approved
        # and then purchased and arrived
        PartOrderStatus(
            part=self.part3,
            status=PartOrderStatus.REQUIRE_INFO,
            user=self.coord_user).save()
        self.assertEquals(len(PartOrder.objects.approved()), 1)

        PartOrderStatus(
            part=self.part3,
            status=PartOrderStatus.PENDING,
            user=self.staff_user).save()
        self.assertEquals(len(PartOrder.objects.approved()), 1)

        PartOrderStatus(
            part=self.part3,
            status=PartOrderStatus.APPROVED,
            user=self.coord_user).save()
        self.assertEquals(len(PartOrder.objects.approved()), 2)

        PartOrderStatus(
            part=self.part3,
            status=PartOrderStatus.PURCHASED,
            user=self.coord_user).save()
        self.assertEquals(len(PartOrder.objects.approved()), 1)

        PartOrderStatus(
            part=self.part3,
            status=PartOrderStatus.ARRIVED,
            user=self.coord_user).save()
        self.assertEquals(len(PartOrder.objects.approved()), 1)


class PartsReceiptFormTest(TestCase):
    fixtures = ['test_data/parts_receipt.yaml']

    def setUp(self):
        self.purchaser = User.objects.get(username='coorduser')
        self.vendor = Vendor.objects.get(pk=1)
        self.receipt_data = {'receipt': SimpleUploadedFile('test.pdf', 'hi')}

    def make_parts_receipt(self):
        # Lazy loading to prevent circular imports
        # Putting this with the other imports led to database errors of
        # a missing pie_staff_purchase_partorderstatus table. This is
        # apparently caused by circular imports.
        from quark.pie_staff_purchase.forms import PartsReceiptForm

        return PartsReceiptForm({
            'confirmation_number': 314159,
            'parts': [p.pk for p in PartOrder.objects.approved()],
            'status': 'pnd',
            'total_cost': 314.15,
            'tracking_number': 999999999999,
            'vendor': self.vendor.pk}, self.receipt_data)

    def test_regular_save(self):
        self.assertEquals(len(PartOrder.objects.approved()), 1)
        receipt_form = self.make_parts_receipt()
        self.assertTrue(receipt_form.is_valid())
        receipt = receipt_form.save(commit=False, purchaser=self.purchaser)
        receipt.purchaser = self.purchaser
        receipt.save()
        self.assertEquals(len(PartOrder.objects.approved()), 0)

    def test_missing_purchaser_save(self):
        self.assertEquals(len(PartOrder.objects.approved()), 1)
        receipt_form = self.make_parts_receipt()
        self.assertTrue(receipt_form.is_valid())
        with self.assertRaises(KeyError):
            receipt_form.save(commit=False)

    def test_disable_update_save(self):
        receipt_form = self.make_parts_receipt()
        self.assertTrue(receipt_form.is_valid())
        self.assertTrue(receipt_form.save(commit=False, update_parts=False))
        self.assertEquals(len(PartOrder.objects.approved()), 1)

        receipt_form.update_parts(self.purchaser)
        self.assertEquals(len(PartOrder.objects.approved()), 0)
