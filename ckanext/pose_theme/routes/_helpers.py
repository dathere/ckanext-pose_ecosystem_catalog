# !/usr/bin/env python
# encoding: utf-8
import logging
import socket
from datetime import datetime, timezone

from ckan import logic
from ckan.common import asbool
from ckan.lib import mailer
from ckan.lib.navl.dictization_functions import unflatten
from ckan.plugins import PluginImplementations, toolkit
from pyisemail import is_email

from ckanext.contact import recaptcha
from ckanext.contact.interfaces import IContact

log = logging.getLogger(__name__)


def validate(data_dict):
    """
    Validates the given data and recaptcha if necessary.
    Modified version for pose_theme with custom optional fields.
    """
    errors = {}
    error_summary = {}
    # Add your optional fields here
    optional_fields = {'subject', 'name', 'organization', 'category', 'content'}
    recaptcha_error = None

    # check each field to see if it has a value and if not, show and error
    for field, value in data_dict.items():
        # we know the save field is not necessary and may be empty so ignore it
        if field == 'save':
            continue
        # ignore optionals
        if field in optional_fields:
            continue
        if value is None or value == '':
            errors[field] = ['Missing Value']
            error_summary[field] = 'Missing value'

    # check the email address, if there is one and the config option isn't off
    if (
        toolkit.asbool(toolkit.config.get('ckanext.contact.check_email', True))
        and data_dict.get('email')
    ):
        if not is_email(data_dict['email'], check_dns=True):
            errors['email'] = ['Email address appears to be invalid']
            error_summary['email'] = 'Email address appears to be invalid'

    # only check the recaptcha if there are no errors
    if not errors:
        try:
            expected_action = toolkit.config.get('ckanext.contact.recaptcha_v3_action')
            recaptcha.check_recaptcha(
                data_dict.get('g-recaptcha-response', None), expected_action
            )
        except recaptcha.RecaptchaError as e:
            log.info(f'Recaptcha failed due to "{e}"')
            recaptcha_error = toolkit._('Recaptcha check failed, please try again.')

    return errors, error_summary, recaptcha_error


def build_subject(
    subject=None, default='Contact/Question from visitor', timestamp_default=False
):
    """Creates the subject line for the contact email."""
    if not subject:
        subject = toolkit.config.get('ckanext.contact.subject', toolkit._(default))
    if asbool(
        toolkit.config.get(
            'ckanext.contact.add_timestamp_to_subject', timestamp_default
        )
    ):
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')
        subject = f'{subject} [{timestamp}]'

    prefix = toolkit.config.get('ckanext.contact.subject_prefix', '')
    return f'{prefix}{" " if prefix else ""}{subject}'


def submit():
    """Custom submit handler with modified validation."""
    email_success = True

    data_dict = logic.clean_dict(
        unflatten(logic.tuplize_dict(logic.parse_params(toolkit.request.values)))
    )

    # Use our custom validation
    errors, error_summary, recaptcha_error = validate(data_dict)

    if len(errors) == 0 and recaptcha_error is None:
        body_parts = [
            f'{data_dict.get("content", "No description provided")}\n',
            'Sent by:',
            f'  Name: {data_dict.get("name", "Not provided")}',
            f'  Email: {data_dict["email"]}',
            f'  Organization: {data_dict.get("organization", "Not provided")}',
            f'  Site/Extension Name: {data_dict.get("project_name", "")}',
            f'  URL: {data_dict.get("url", "")}',
            f'  Submission Type: {data_dict.get("submission_type", "")}',
            f'  Category: {data_dict.get("category", "Not provided")}',
        ]
        mail_dict = {
            'recipient_email': toolkit.config.get(
                'ckanext.contact.mail_to', toolkit.config.get('email_to')
            ),
            'recipient_name': toolkit.config.get(
                'ckanext.contact.recipient_name', toolkit.config.get('ckan.site_title')
            ),
            'subject': build_subject(subject=data_dict.get('subject')),
            'body': '\n'.join(body_parts),
            'headers': {'reply-to': data_dict['email']},
        }

        for plugin in PluginImplementations(IContact):
            plugin.mail_alter(mail_dict, data_dict)

        emails = mail_dict.pop('recipient_email')
        names = mail_dict.pop('recipient_name')
        if isinstance(emails, str):
            emails = [emails]
            names = [names]

        for name, email in zip(names, emails):
            try:
                mailer.mail_recipient(name, email, **mail_dict)
            except (mailer.MailerException, socket.error):
                email_success = False

    return {
        'success': recaptcha_error is None and len(errors) == 0 and email_success,
        'data': data_dict,
        'errors': errors,
        'error_summary': error_summary,
        'recaptcha_error': recaptcha_error,
    }