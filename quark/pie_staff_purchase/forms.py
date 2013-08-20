from chosen.forms import ChosenModelMultipleChoiceField
from chosen import widgets as ChosenWidgets
from django import forms

from quark.pie_staff_purchase.models import PartOrder
from quark.pie_staff_purchase.models import PartOrderStatus
from quark.pie_staff_purchase.models import PartsReceipt
from quark.pie_staff_purchase.models import Vendor


class PartOrderForm(forms.ModelForm):
    class Meta(object):
        model = PartOrder
        exclude = ('order', 'submitted_by',)
        widgets = {
            'item': ChosenWidgets.ChosenSelectMultiple,
            'vendor': ChosenWidgets.ChosenSelect}


class PartOrderStatusForm(forms.ModelForm):
    """
    This for is intended to be used with the part and user fields pre-populated
    upon instantiation.
    """
    class Meta(object):
        model = PartOrderStatus
        exclude = ('part', 'user',)


class PartsReceiptForm(forms.ModelForm):
    """
    Form has an additional field, parts, to account for all of
    the parts being ordered. In save, we use this to create
    purchased statuses for those parts. Note that these statuses
    will be created only when commit is not False.
    """
    # Only show PartOrders that have been approved.
    parts = ChosenModelMultipleChoiceField(
        queryset=PartOrder.objects.approved())

    def update_parts(self, purchaser):
        # purchaser field is a User that is for the new part statuses
        for part in self.cleaned_data['parts']:
            PartOrderStatus(
                part=part,
                status=PartOrderStatus.PURCHASED,
                user=purchaser).save()

    def save(self, *args, **kwargs):
        # One of the kwargs must be an assignment for purchaser, so it may be
        # used for update_parts. Optionally, the call to update_parts can
        # be skipped with update_parts = False
        if kwargs.get('update_parts', True):
            self.update_parts(kwargs['purchaser'])

        # Remove the special key words since save doesn't like extra ones it
        # doesn't know about
        if 'update_parts' in kwargs.keys():
            del(kwargs['update_parts'])
        if 'purchaser' in kwargs.keys():
            del(kwargs['purchaser'])
        return super(PartsReceiptForm, self).save(*args, **kwargs)

    class Meta(object):
        model = PartsReceipt
        exclude = ('purchaser',)
        widgets = {
            'vendor': ChosenWidgets.ChosenSelect}


class VendorForm(forms.ModelForm):
    class Meta(object):
        model = Vendor
