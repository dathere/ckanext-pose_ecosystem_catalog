import pytest

from ckanext.pose_theme.tests.helpers import do_get, do_post

CUSTOM_CSS_URL = "/ckan-admin/custom_css"
RESET_CUSTOM_CSS_URL = "/ckan-admin/reset_custom_css"

DEFAULT_DATA = {
    'account-header-background-color': '#165cab',
    'account-header-hover-background-color': '#1f76d8',
    'account-header-text-color': '#ffffff',
    'nav-header-background-color': '#ffffff',
    'nav-header-hover-background-color': '#1f76d8',
    'nav-header-text-color': '#07305c',
    'module-header-background-color': '#165cab',
    'module-header-text-color': '#ffffff',
    'footer-background-color': '#07305c',
    'footer-link-text-color': '#ffffff',
    'footer-text-color': '#ffffff'
}

DEFAULT_CUSTOM_CSS = (
    '.account-masthead {background: #165cab}',
    '.account-masthead .account ul li a:hover {background: #1f76d8}',
    '.account-masthead .account ul li a {color: #ffffff}',
    '.masthead {background: #ffffff}',
    '.masthead .navigation .nav-pills li a:hover,.masthead .navigation .nav-pills li.active a,'
    '.navbar-toggle {background-color: #1f76d8}',
    '.navbar .nav>li>a,.masthead .nav>li>a,.navbar hgroup>h1>a,.navbar hgroup>h2 {color: #07305c}',
    '.module-heading {background: #165cab}',
    '.module-heading,.module-heading .action {color: #ffffff}',
    'body, .site-footer, .footer-column-form .cke_reset {background: #07305c}',
    '.site-footer a,.site-footer a:hover,.footer-column-form .cke_reset a {color: #ffffff}',
    '.site-footer,.site-footer label,.site-footer small,.footer-column-form .cke_reset {color: #ffffff}'
)


def check_custom_css_page_html(response, expected_form_data, expected_css_data, errors=()):
    assert response, 'Response is empty.'
    assert len(expected_form_data.keys()) == response.body.count('pose-theme-color-picker')
    for key, value in expected_form_data.items():
        assert 'name="{0}" id="{0}" value="{1}"'.format(
            key, value) in response.body, 'Missed form field for "{}".'.format(key)
    for line in expected_css_data:
        assert line in response.body, 'CSS line "{}" missed in result html.'.format(line)
    if errors:
        for error_message in errors:
            assert error_message in response.body, 'Error message "{}" not in HTML.'.format(error_message)
    else:
        assert 'alert' not in response, 'Result HTML contains alerts when they are not expected.'


@pytest.mark.usefixtures("clean_db", "with_request_context")
def test_get_custom_css_page_with_not_sysadmin_user(app):
    response = do_get(app, CUSTOM_CSS_URL, is_sysadmin=False)
    assert 403 == response.status_code


@pytest.mark.usefixtures("clean_db", "with_request_context")
def test_get_custom_css_page_with_default_data(app):
    response = do_get(app, CUSTOM_CSS_URL, is_sysadmin=True)
    check_custom_css_page_html(response, expected_form_data=DEFAULT_DATA.copy(), expected_css_data=DEFAULT_CUSTOM_CSS)


@pytest.mark.usefixtures("clean_db", "with_request_context")
def test_post_custom_css_page_with_changed_color(app):
    data = DEFAULT_DATA.copy()
    data['account-header-background-color'] = '#07305c'
    unexpected_custom_css = '.account-masthead {background: #165cab}'
    expected_custom_css = list(DEFAULT_CUSTOM_CSS)
    expected_custom_css.remove(unexpected_custom_css)
    expected_custom_css.append('.account-masthead {background: #07305c}')
    response = do_post(app, CUSTOM_CSS_URL, is_sysadmin=True, data=data)

    check_custom_css_page_html(response, expected_form_data=data, expected_css_data=expected_custom_css)
    assert unexpected_custom_css not in response


@pytest.mark.usefixtures("clean_db", "with_request_context")
def test_post_custom_css_page_with_changed_color_respond_with_contrast_connected_message(app):
    data = DEFAULT_DATA.copy()
    data['account-header-background-color'] = '#ffffff'

    unexpected_custom_css = '.account-masthead {background: #ffffff}'

    expected_custom_css = list(DEFAULT_CUSTOM_CSS)

    response = do_post(app, CUSTOM_CSS_URL, is_sysadmin=True, data=data)
    messages = [
        'Account Header Background Color and Account Header Text Color: Contrast ratio is not high enough.'
    ]
    check_custom_css_page_html(response, expected_form_data=data, expected_css_data=expected_custom_css,
                               errors=messages)
    assert unexpected_custom_css not in response


@pytest.mark.usefixtures("clean_db", "with_request_context")
def test_reset_changed_custom_css(app):
    data = DEFAULT_DATA.copy()
    data['account-header-background-color'] = '#07305c'
    unexpected_custom_css = '.account-masthead {background: #165cab}'
    expected_custom_css = list(DEFAULT_CUSTOM_CSS)
    expected_custom_css.remove(unexpected_custom_css)
    expected_custom_css.append('.account-masthead {background: #07305c}')
    response = do_post(app, CUSTOM_CSS_URL, is_sysadmin=True, data=data)
    assert unexpected_custom_css not in response

    reset_response = do_post(app, RESET_CUSTOM_CSS_URL, data={})
    check_custom_css_page_html(reset_response,
                               expected_form_data=DEFAULT_DATA.copy(),
                               expected_css_data=DEFAULT_CUSTOM_CSS)
