from flask import Blueprint, render_template, request

from ckan.plugins import toolkit
from ckanext.pose_theme.routes import _helpers

contact_blueprint = Blueprint('pose_contact', __name__)


@contact_blueprint.route('/contact', methods=['GET', 'POST'])
def form():
    """Custom contact form handler - restricted to logged-in users."""
    
    # Check if user is logged in
    if not toolkit.current_user.is_authenticated:
        toolkit.h.flash_error(toolkit._('You must be logged in to access the contact form.'))
        # Redirect to login page with return URL
        return toolkit.redirect_to('user.login', came_from=toolkit.request.url)
    
    # User is authenticated, proceed with form handling
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