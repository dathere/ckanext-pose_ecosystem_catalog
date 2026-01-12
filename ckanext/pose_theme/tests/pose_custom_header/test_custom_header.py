import pytest

from ckanext.pose_theme.tests.helpers import do_get, do_post

CUSTOM_HEADER_URL = "/ckan-admin/custom_header"
RESET_CUSTOM_HEADER_URL = "/ckan-admin/reset_custom_header"
DEFAULT_LINKS = (
    {'position': 0, 'title': 'Datasets', 'url': '/dataset'},
    {'position': 1, 'title': 'Organizations', 'url': '/organization'},
    {'position': 2, 'title': 'Groups', 'url': '/group'},
    {'position': 3, 'title': 'About', 'url': '/about'},
)
DEFAULT_HEADERS = (
    {'title': 'Datasets', 'url': '/dataset'},
    {'title': 'Organizations', 'url': '/organization'},
    {'title': 'Groups', 'url': '/group'},
    {'title': 'About', 'url': '/about'},
)


def check_custom_header_page_html(response, links, headers, default_layout=True):
    assert response, 'Response is empty.'
    if default_layout:
        assert '<option value="default" selected="selected">' in response
    else:
        assert '<option value="compressed" selected="selected">' in response
    for index, link in enumerate(links):
        assert '<div class="row" id="link-{}">'.format(index) in response
        assert 'name="position" value="{}"'.format(link.get('position')) in response
        assert 'id="title-{}" name="title" value="{}"'.format(index, link.get('title')) in response
        assert 'id="url-{}" name="url" value="{}"'.format(index, link.get('url')) in response
    for header in headers:
        assert '<li><a href="{}">{}</a></li>'.format(header.get('url'), header.get('title')) in response


@pytest.mark.usefixtures("clean_db", "with_request_context")
def test_get_custom_header_page_with_not_sysadmin_user(app):
    response = do_get(app, CUSTOM_HEADER_URL, is_sysadmin=False)
    assert '<h1>403 Forbidden</h1>' in response


@pytest.mark.usefixtures("clean_db", "with_request_context")
def test_get_custom_header_page(app):
    response = do_get(app, CUSTOM_HEADER_URL, is_sysadmin=True)
    check_custom_header_page_html(response, links=[], headers=DEFAULT_HEADERS, default_layout=True)


@pytest.mark.usefixtures("clean_db", "with_request_context")
def test_add_link_to_custom_header(app):
    data = {
        'add_link': '',
        'new_title': 'Example',
        'new_url': 'https://example.com',
    }
    expected_links = DEFAULT_LINKS + ({'position': 4, 'title': 'Example', 'url': 'https://example.com'},)
    expected_headers = DEFAULT_HEADERS + ({'title': 'Example', 'url': 'https://example.com'},)

    custom_header_response = do_get(app, CUSTOM_HEADER_URL, is_sysadmin=True)
    check_custom_header_page_html(custom_header_response, links=[], headers=DEFAULT_HEADERS, default_layout=True)

    response = do_post(app, CUSTOM_HEADER_URL, data, is_sysadmin=True)
    check_custom_header_page_html(response, links=expected_links, headers=expected_headers)


@pytest.mark.usefixtures("clean_db", "with_request_context")
def test_add_unsupported_link_to_custom_header(app):
    data = {
        'add_link': '',
        'new_title': 'Bad Example',
        'new_link': 'http://example.com'
    }
    response = do_post(app, CUSTOM_HEADER_URL, data, is_sysadmin=True)
    check_custom_header_page_html(response, links=[], headers=DEFAULT_HEADERS)


@pytest.mark.usefixtures("clean_db", "with_request_context")
def test_remove_link_from_custom_header(app):
    data = {
        'remove_link': '',
        'remove_title': 'About',
    }
    expected_links = list(DEFAULT_LINKS)
    expected_links.pop(3)

    expected_headers = list(DEFAULT_HEADERS)
    expected_headers.pop(3)

    response = do_post(app, CUSTOM_HEADER_URL, data, is_sysadmin=True)
    check_custom_header_page_html(response, links=expected_links, headers=expected_headers)
    assert '<li><a href="/about">About</a></li>' not in response


@pytest.mark.usefixtures("clean_db", "with_request_context")
def test_update_multiple_custom_header_links(app):
    data = {
        'save': '',
        'layout_type': 'default',
        'position': ['1', '0'],
        'title': ['Dataset Catalog', 'Departments'],
        'url': ['/dataset', '/organization']
    }
    expected_links = (
        {'position': 1, 'title': 'Dataset Catalog', 'url': '/dataset'},
        {'position': 0, 'title': 'Departments', 'url': '/organization'},
    )
    expected_headers = (
        {'title': 'Dataset Catalog', 'url': '/dataset'},
        {'title': 'Departments', 'url': '/organization'},
    )

    response = do_post(app, CUSTOM_HEADER_URL, data, is_sysadmin=True)
    check_custom_header_page_html(response, links=expected_links, headers=expected_headers)


@pytest.mark.usefixtures("clean_db", "with_request_context")
def test_update_single_custom_header_links(app):
    data = {
        'save': '',
        'layout_type': 'compressed',
        'position': '0',
        'title': 'New Datasets',
        'url': '/dataset'
    }
    expected_headers = [
        {'title': 'New Datasets', 'url': '/dataset'}
    ]

    response = do_post(app, CUSTOM_HEADER_URL, data, is_sysadmin=True)
    check_custom_header_page_html(response, links=[], headers=expected_headers, default_layout=False)
