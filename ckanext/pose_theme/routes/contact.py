from flask import Blueprint, render_template, request

from ckan.plugins import toolkit
from ckanext.pose_theme.routes import _helpers

contact_blueprint = Blueprint('pose_contact', __name__)


@contact_blueprint.route('/contact', methods=['GET', 'POST'])
def form():
    """Custom contact form handler."""
    if request.method == 'POST':
        result = _helpers.submit()
        if result['success']:
            return render_template('contact/success.html')
        else:
            return render_template(
                'contact/form.html',
                data=result['data'],
                errors=result['errors'],
                error_summary=result['error_summary'],
                recaptcha_error=result.get('recaptcha_error'),
            )
    
    return render_template('contact/form.html', data={}, errors={})


def get_blueprints():
    return [contact_blueprint]