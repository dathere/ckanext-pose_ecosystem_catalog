import pytest

from ckan.plugins import toolkit as tk

from ckan.tests import factories

import ckanext.extension.logic.helpers as extension_helpers


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestGetSiteStatistics(object):
    def test_dataset_count_no_datasets(self):
        """
        Dataset and extension count is 0 when no datasets, and no extensions.
        """
        if not tk.check_ckan_version(min_version="2.5"):
            pytest.skip(
                reason="get_site_statistics without user broken in CKAN 2.4"
            )
        stats = extension_helpers.get_site_statistics()
        assert stats["dataset_count"] == 0
        assert stats["extension_count"] == 0

    def test_dataset_count_no_datasets_some_extensions(self):
        """
        Dataset and extension count is 0 when no datasets, but some extensions.
        """
        if not tk.check_ckan_version(min_version="2.5"):
            pytest.skip(
                reason="get_site_statistics without user broken in CKAN 2.4"
            )
        for i in range(0, 10):
            factories.Dataset(type="extension")

        stats = extension_helpers.get_site_statistics()
        assert stats["dataset_count"] == 0
        assert stats["extension_count"] == 10

    def test_dataset_count_some_datasets_no_extensions(self):
        """
        Dataset and extension count is correct when there are datasets, but no
        extensions.
        """
        if not tk.check_ckan_version(min_version="2.5"):
            pytest.skip(
                reason="get_site_statistics without user broken in CKAN 2.4"
            )
        for i in range(0, 10):
            factories.Dataset()

        stats = extension_helpers.get_site_statistics()
        assert stats["dataset_count"] == 10
        assert stats["extension_count"] == 0

    def test_dataset_count_some_datasets_some_extensions(self):
        """
        Dataset and extension count is correct when there are datasets and some
        extensions.
        """
        if not tk.check_ckan_version(min_version="2.5"):
            pytest.skip(
                reason="get_site_statistics without user broken in CKAN 2.4"
            )
        for i in range(0, 10):
            factories.Dataset()

        for i in range(0, 5):
            factories.Dataset(type="extension")

        stats = extension_helpers.get_site_statistics()
        assert stats["dataset_count"] == 10
        assert stats["extension_count"] == 5
