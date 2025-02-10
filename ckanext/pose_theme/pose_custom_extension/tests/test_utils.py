# -*- coding: utf-8 -*-

import pytest

from ckan.lib import helpers
from ckan.tests import factories, helpers as test_helpers

from ckanext.extension.utils import markdown_to_html


@pytest.mark.usefixtures("clean_db")
class TestUtils(object):

    def test_markdown_to_html(self):
        extensions1 = factories.Dataset(
                type='extension',
                name='my-extension',
                notes='# Title')

        extensions2 = factories.Dataset(
            type='extension',
            name='my-extension-2',
            notes='# Title 2')

        markdown_to_html()

        migrated_extension1 = test_helpers.call_action(
                'package_show',
                context={'ignore_auth': True},
                id=extensions1['id']
            )

        assert migrated_extension1['notes'] == helpers.render_markdown(extensions1['notes'])

        migrated_extension2 = test_helpers.call_action(
                'package_show',
                context={'ignore_auth': True},
                id=extensions2['id']
            )

        assert migrated_extension2['notes'] == helpers.render_markdown(extensions2['notes'])
