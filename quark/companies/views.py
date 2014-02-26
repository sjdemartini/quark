from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import ListView

from quark.accounts.forms import PasswordResetForm
from quark.companies.forms import CompanyRepCreationForm
from quark.companies.models import Company


# TODO(sjdemartini): Use proper permissions for each of the different views and
# actions


class CompanyListView(ListView):
    """List all the companies that have accounts."""
    context_object_name = 'companies'
    model = Company
    template_name = 'companies/list.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('companies.change_company', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(CompanyListView, self).dispatch(*args, **kwargs)


class CompanyDetailView(DetailView):
    """Show details for a company and its representatives."""
    model = Company
    pk_url_kwarg = 'company_pk'
    template_name = 'companies/detail.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('companies.change_company', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(CompanyDetailView, self).dispatch(*args, **kwargs)

    # TODO(sjdemartini): Add more interesting context here, like a list of the
    # representatives for the company


class CompanyRepCreateView(CreateView):
    """View for creating a new account for a company representative.

    Upon successful completion of the creation form, an email is sent to the
    company representative to allow them to set the password for their account.
    """
    form_class = CompanyRepCreationForm
    success_url = reverse_lazy('companies:list')
    template_name = 'companies/create_rep.html'
    object = None  # The User account created for the rep

    @method_decorator(login_required)
    @method_decorator(
        permission_required('companies.add_companyrep', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(CompanyRepCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        self.object = form.save()
        username = self.object.get_username()
        company = form.cleaned_data['company']
        msg = ('Successfully created a new company rep account with the '
               'username {} for the company {}.'.format(username, company))
        messages.success(self.request, msg)

        # Use a password reset form to send the new company rep a password
        # reset email, so that they can choose their own password and log in
        pw_reset_form = PasswordResetForm({'username_or_email': username})
        if pw_reset_form.is_valid():
            email_template = 'accounts/password_set_initial_email.html'
            subject_template = 'accounts/password_set_initial_subject.txt'
            pw_reset_form.save(
                email_template_name=email_template,
                subject_template_name=subject_template)
        else:
            # Throw an error and log the form data and errors, since something
            # is wrong.
            error_msg = (
                u'Failed to send new company rep their password reset email. \n'
                'Form data: {data} \nForm Errors: {errors}'.format(
                    data=pw_reset_form.data,
                    errors=pw_reset_form.errors.items())
            )
            raise ValidationError(error_msg)
        return HttpResponseRedirect(self.get_success_url())
