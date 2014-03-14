# pylint: disable=F0401
from Mailman import MailList
from Mailman import Utils

from quark.base.models import OfficerPosition


def get_lists():
    names = Utils.list_names()
    names.sort()
    committees = OfficerPosition.objects.all()
    committee_lists = {}
    for committee in committees:
        if committee.mailing_list:
            committee_lists[committee.mailing_list] = committee
    mlists = []
    for name in names:
        try:
            mlist = MailList.MailList(name, lock=False)
        except IOError:
            continue
        mlist_item = {
            'name': mlist.internal_name(),
            'url': mlist.GetScriptURL('listinfo', absolute=1),
            'adminurl': mlist.GetScriptURL('admin', absolute=1),
            'description': mlist.description,
            'public': True if mlist.advertised else False,
        }
        if mlist.internal_name() in committee_lists:
            mlist_item['position'] = committee_lists[mlist.internal_name()]
        mlists.append(mlist_item)

    return mlists
