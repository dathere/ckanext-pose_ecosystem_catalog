# -*- coding: utf-8 -*-

import pytest

from ckan.lib import helpers
from ckan.tests import factories, helpers as test_helpers

from ckanext.site.utils import markdown_to_html


@pytest.mark.usefixtures("clean_db")
class TestUtils(object):

    def test_markdown_to_html(self):
        sites1 = factories.Dataset(
                type='site',
                name='my-site',
                notes='# Title')

        sites2 = factories.Dataset(
            type='site',
            name='my-site-2',
            notes='# Title 2')

        markdown_to_html()

        migrated_site1 = test_helpers.call_action(
                'package_show',
                context={'ignore_auth': True},
                id=sites1['id']
            )

        assert migrated_site1['notes'] == helpers.render_markdown(sites1['notes'])

        migrated_site2 = test_helpers.call_action(
                'package_show',
                context={'ignore_auth': True},
                id=sites2['id']
            )

        assert migrated_site2['notes'] == helpers.render_markdown(sites2['notes'])
