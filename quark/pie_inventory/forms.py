from django import forms

from quark.pie_inventory.models import Item


# pylint: disable=R0924
class ItemForm(forms.ModelForm):
    """
    Basic form for an Item.
    """
    class Meta:
        model = Item
        fields = ('name', 'picture', 'wiki', 'description')
