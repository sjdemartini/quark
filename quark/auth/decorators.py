from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from quark.base.models import Term


def officer_types_required(officer_types=None, exclude=False, current=False):
    """Generator for specific officer type access decorators

    This decorator generator creates a decorator that allows only officers of
    specified positions to view the page.

    To use this decorator generator, give it a list of the short names of the
    allowed positions. The name 'execs' can be used to reference to all the
    executive positions. To allow any officer to view the page, no parameters
    are needed.

    To RESTRICT certain officer positions from viewing, set the optional
    exclude parameter to True.

    If the optional parameter current is set to True, then only current
    officer positions will be used in determining permissions (i.e. current
    officer with the given officer_types for exclude False, and current officer
    that isn't officer_types right now for exclude True).

    Ex. To allow only the president and IT to view a page:
    @officer_types_required(['president', 'it'])
    Ex. To restrict execs from viewing:
    @officer_types_required(['execs'], True)
    Ex. To restrict current IT from viewing:
    @officer_types_required(['it'], True, True)
    Ex. To allow only current execs to view:
    @officer_types_required(['execs'], current=True)
    """

    if officer_types is None:
        officer_types = []

    officer_types = set(officer_types)
    if 'execs' in officer_types:
        officer_types.remove('execs')
        officer_types = officer_types.union(
            ['president', 'vp', 'rsec', 'csec', 'treasurer'])

    def new_officer_decorator(orig_view):
        def new_view(request, *args, **kwargs):
            if request.user.is_authenticated():
                if request.user.is_tbp_officer(current=current):
                    if not officer_types:
                        return orig_view(request, *args, **kwargs)

                    term = (Term.objects.get_current_term() if current
                            else None)
                    positions = request.user.get_tbp_officer_positions(
                        term=term)
                    positions = [pos.short_name.lower() for pos in positions]

                    # check if any desired officer type is in user's positions
                    pos_matches = officer_types.intersection(positions)
                    if bool(pos_matches) ^ exclude:  # xor
                        return orig_view(request, *args, **kwargs)

                # insufficient permissions at some level
                raise PermissionDenied
            else:  # if not logged in
                return (login_required(orig_view))(request, *args, **kwargs)

        # return view with decorator applied
        return new_view

    return new_officer_decorator


def candidate_required(orig_view):
    def new_view(request, *args, **kwargs):
        if request.user.is_authenticated():
            if request.user.is_tbp_candidate():
                return orig_view(request, *args, **kwargs)
            else:
                raise PermissionDenied
        else:
            return (login_required(orig_view))(request, *args, **kwargs)

    return new_view


officer_required = officer_types_required()
current_officer_required = officer_types_required(current=True)
current_officer_no_advisor_required = officer_types_required(
    ['advisor', 'faculty'], exclude=True, current=True)
president_required = officer_types_required(['president'])
execs_required = officer_types_required(['execs'])
it_required = officer_types_required(['it'])
execs_it_required = officer_types_required(['execs', 'it'])
president_it_required = officer_types_required(['president', 'it'])
vp_it_required = officer_types_required(['vp', 'it'])
