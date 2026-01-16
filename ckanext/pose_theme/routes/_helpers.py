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
    Modified version for general contact form.
    """
    errors = {}
    error_summary = {}
    # Optional fields for contact form
    optional_fields = {'organization', 'url'}
    recaptcha_error = None

    # Required fields: name, email, subject, content
    required_fields = ['name', 'email', 'subject', 'content']

    # Check each required field
    for field in required_fields:
        value = data_dict.get(field)
        if value is None or value == '':
            errors[field] = ['Missing Value']
            error_summary[field] = 'Missing value'

    # Check the email address, if there is one and the config option isn't off
    if (
        toolkit.asbool(toolkit.config.get('ckanext.contact.check_email', True))
        and data_dict.get('email')
    ):
        if not is_email(data_dict['email'], check_dns=True):
            errors['email'] = ['Email address appears to be invalid']
            error_summary['email'] = 'Email address appears to be invalid'

    # Validate URL if provided
    if data_dict.get('url'):
        url = data_dict['url'].strip()
        if url and not (url.startswith('http://') or url.startswith('https://')):
            errors['url'] = ['URL must start with http:// or https://']
            error_summary['url'] = 'Invalid URL format'

    # Only check the recaptcha if there are no errors
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
    subject=None, default='Contact Form Submission', timestamp_default=False
):
    """Creates the subject line for the contact email."""
    # Subject mapping for better readability
    subject_map = {
        'general': 'General Inquiry',
        'submission': 'Question About Submissions',
        'technical': 'Technical Support',
        'feedback': 'Feedback or Suggestions',
        'report': 'Report an Issue',
        'partnership': 'Partnership Opportunity',
        'other': 'Other Inquiry'
    }
    
    # Use mapped subject if it's a key, otherwise use the value directly
    subject_text = subject_map.get(subject, subject) if subject else default
    
    # Get the default subject from config if not provided
    if not subject:
        subject_text = toolkit.config.get('ckanext.contact.subject', toolkit._(default))
    
    # Add timestamp if configured
    if asbool(
        toolkit.config.get(
            'ckanext.contact.add_timestamp_to_subject', timestamp_default
        )
    ):
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')
        subject_text = f'{subject_text} [{timestamp}]'

    # Add prefix if configured
    prefix = toolkit.config.get('ckanext.contact.subject_prefix', '')
    return f'{prefix}{" " if prefix else ""}{subject_text}'


def submit():
    """Custom submit handler for general contact form."""
    email_success = True

    data_dict = logic.clean_dict(
        unflatten(logic.tuplize_dict(logic.parse_params(toolkit.request.values)))
    )

    # Use our custom validation
    errors, error_summary, recaptcha_error = validate(data_dict)

    if len(errors) == 0 and recaptcha_error is None:
        # Subject mapping for email display
        subject_map = {
            'general': 'General Inquiry',
            'submission': 'Question About Submissions',
            'technical': 'Technical Support',
            'feedback': 'Feedback or Suggestions',
            'report': 'Report an Issue',
            'partnership': 'Partnership Opportunity',
            'other': 'Other Inquiry'
        }
        
        subject_label = subject_map.get(
            data_dict.get('subject', ''), 
            data_dict.get('subject', 'Contact Form')
        )
        
        # Build email body
        body_parts = [
            '═══════════════════════════════════════════════════',
            'NEW CONTACT FORM SUBMISSION',
            '═══════════════════════════════════════════════════',
            '',
            'CONTACT INFORMATION:',
            '───────────────────────────────────────────────────',
            f'Name:         {data_dict.get("name", "Not provided")}',
            f'Email:        {data_dict["email"]}',
            f'Organization: {data_dict.get("organization", "Not provided")}',
            '',
            '───────────────────────────────────────────────────',
            f'SUBJECT:      {subject_label}',
            '───────────────────────────────────────────────────',
            '',
            'MESSAGE:',
            '───────────────────────────────────────────────────',
            data_dict.get("content", "No message provided"),
            '',
        ]
        
        # Add related URL if provided
        if data_dict.get('url'):
            body_parts.extend([
                '───────────────────────────────────────────────────',
                'ADDITIONAL INFORMATION:',
                '───────────────────────────────────────────────────',
                f'Related URL:  {data_dict.get("url")}',
                '',
            ])
        
        body_parts.extend([
            '═══════════════════════════════════════════════════',
            f'Submitted:    {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")}',
            '═══════════════════════════════════════════════════',
            '',
            'Reply directly to this email to respond to the sender.',
        ])
        
        mail_dict = {
            'recipient_email': toolkit.config.get(
                'ckanext.contact.mail_to', toolkit.config.get('email_to')
            ),
            'recipient_name': toolkit.config.get(
                'ckanext.contact.recipient_name', 
                toolkit.config.get('ckan.site_title', 'CKAN Catalog')
            ),
            'subject': build_subject(subject=data_dict.get('subject')),
            'body': '\n'.join(body_parts),
            'headers': {'reply-to': data_dict['email']},
        }

        # Allow plugins to alter the email
        for plugin in PluginImplementations(IContact):
            plugin.mail_alter(mail_dict, data_dict)

        emails = mail_dict.pop('recipient_email')
        names = mail_dict.pop('recipient_name')
        if isinstance(emails, str):
            emails = [emails]
            names = [names]

        # Send email to all recipients
        for name, email in zip(names, emails):
            try:
                mailer.mail_recipient(name, email, **mail_dict)
                log.info(f'Contact form email sent successfully to {email}')
            except (mailer.MailerException, socket.error) as e:
                log.error(f'Failed to send contact form email to {email}: {str(e)}')
                email_success = False

    return {
        'success': recaptcha_error is None and len(errors) == 0 and email_success,
        'data': data_dict,
        'errors': errors,
        'error_summary': error_summary,
        'recaptcha_error': recaptcha_error,
    }