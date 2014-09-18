import os

from django.conf import settings
from django.db import models


class Resume(models.Model):
    RESUMES_LOCATION = 'resumes'

    # Custom displays for the verified NullBooleanField
    VERIFIED_CHOICES = (
        (None, 'Pending'),
        (True, 'Approved'),
        (False, 'Denied'),
    )

    def rename_file(instance, filename):
        """Rename the file to the user's username, and update the resume
        file if it already exists."""
        # pylint: disable=E0213
        file_ext = os.path.splitext(filename)[1]
        filename = os.path.join(Resume.RESUMES_LOCATION,
                                str(instance.user.get_username()) + file_ext)
        full_path = os.path.join(settings.MEDIA_ROOT, filename)
        # if resume file already exists, delete it so the new resume file can
        # use the same name
        if os.path.exists(full_path):
            os.remove(full_path)
        return filename

    user = models.ForeignKey(settings.AUTH_USER_MODEL, unique=True)
    gpa = models.DecimalField(
        verbose_name='GPA', max_digits=4, decimal_places=3,
        help_text='GPA must have three decimal places (ex. 3.750)')
    full_text = models.TextField(help_text='Full text of the resume')
    resume_file = models.FileField(
        upload_to=rename_file,
        verbose_name='File', help_text='PDF only please')
    # Each resume must be manually verified by an officer to determine
    # whether it is suitable to show to companies. For candidates, resumes
    # must also be verified to fulfill the resume candidate requirement.
    # This field is set to null if no one has examined this resume yet, false
    # if it has been deemed inappropriate, and true if it has been verified.
    verified = models.NullBooleanField(choices=VERIFIED_CHOICES)
    critique = models.BooleanField(
        default=True, verbose_name='Critique requested',
        help_text='Request an officer to critique your resume')
    # If true, then this resume is to be released to companies when verified.
    # The user specifies this when uploading or editing their resume, and it
    # should not be changed by anyone else.
    release = models.BooleanField(
        default=True, verbose_name='Release to companies')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField()

    class Meta(object):
        permissions = (
            ('view_resumes', 'Can view all resumes'),
        )

    def get_download_file_name(self):
        """Return the file name of the resume file when it is downloaded."""
        return '{first}{last}'.format(
            first=self.user.first_name, last=self.user.last_name)

    def __unicode__(self):
        return '{user} (Updated {time})'.format(
            user=self.user.get_full_name(),
            time=self.updated.strftime('%Y-%m-%d %H:%M:%S %Z'))
