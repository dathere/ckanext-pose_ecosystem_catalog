# -*- coding: utf-8 -*-

import pytest

from ckan.tests import factories, helpers
import ckan.plugins.toolkit as toolkit


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSiteshow(object):
    def test_site_show_no_args(self):
        """
        Calling site show with no args raises a ValidationError.
        """
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action("ckanext_site_show")

    def test_site_show_with_id(self):
        """
        Calling site show with id arg returns site dict.
        """
        my_site = factories.Dataset(type="site", name="my-site")

        site_shown = helpers.call_action(
            "ckanext_site_show", id=my_site["id"]
        )

        assert my_site["name"] == site_shown["name"]

    def test_site_show_with_name(self):
        """
        Calling site show with name arg returns site dict.
        """
        my_site = factories.Dataset(type="site", name="my-site")

        site_shown = helpers.call_action(
            "ckanext_site_show", id=my_site["name"]
        )

        assert my_site["id"] == site_shown["id"]

    def test_site_show_with_nonexisting_name(self):
        """
        Calling site show with bad name arg returns ObjectNotFound.
        """
        factories.Dataset(type="site", name="my-site")

        with pytest.raises(toolkit.ObjectNotFound):
            helpers.call_action(
                "ckanext_site_show", id="my-bad-name",
            )

    def test_site_show_num_datasets_added(self):
        """
        num_datasets property returned with site dict.
        """
        my_site = factories.Dataset(type="site", name="my-site")

        site_shown = helpers.call_action(
            "ckanext_site_show", id=my_site["name"]
        )

        assert "num_datasets" in site_shown
        assert site_shown["num_datasets"] == 0

    def test_site_show_num_datasets_correct_value(self):
        """
        num_datasets property has correct value.
        """

        sysadmin = factories.User(sysadmin=True)

        my_site = factories.Dataset(type="site", name="my-site")
        org = factories.Organization()
        package_one = factories.Dataset(owner_org=org["id"])
        package_two = factories.Dataset(owner_org=org["id"])

        context = {"user": sysadmin["name"]}
        # create an association
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package_one["id"],
            site_id=my_site["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package_two["id"],
            site_id=my_site["id"],
            organization_id=org["id"]
        )

        site_shown = helpers.call_action(
            "ckanext_site_show", id=my_site["name"]
        )

        assert site_shown["num_datasets"] == 2

    def test_site_show_num_datasets_correct_only_count_active_datasets(
        self,
    ):
        """
        num_datasets property has correct value when some previously
        associated datasets have been datasets.
        """
        sysadmin = factories.User(sysadmin=True)

        my_site = factories.Dataset(type="site", name="my-site")
        org = factories.Organization()
        package_one = factories.Dataset(owner_org=org["id"])
        package_two = factories.Dataset(owner_org=org["id"])
        package_three = factories.Dataset(owner_org=org["id"])

        context = {"user": sysadmin["name"]}
        # create the associations
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package_one["id"],
            site_id=my_site["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package_two["id"],
            site_id=my_site["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package_three["id"],
            site_id=my_site["id"],
            organization_id=org["id"]
        )

        # delete the first package
        helpers.call_action(
            "package_delete", context=context, id=package_one["id"]
        )

        site_shown = helpers.call_action(
            "ckanext_site_show", id=my_site["name"]
        )

        # the num_datasets should only include active datasets
        assert site_shown["num_datasets"] == 2

    def test_site_anon_user_can_see_package_list_when_site_association_was_deleted(
        self, app
    ):
        """
        When a site is deleted, the remaining associations with formerly associated
        packages or sites can still be displayed.
        """

        sysadmin = factories.User(sysadmin=True)

        site_one = factories.Dataset(type="site", name="site-one")
        site_two = factories.Dataset(type="site", name="site-two")
        org = factories.Organization()
        package_one = factories.Dataset(owner_org=org["id"])
        package_two = factories.Dataset(owner_org=org["id"])

        admin_context = {"user": sysadmin["name"]}

        # create the associations
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=admin_context,
            package_id=package_one["id"],
            site_id=site_one["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=admin_context,
            package_id=package_one["id"],
            site_id=site_two["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=admin_context,
            package_id=package_two["id"],
            site_id=site_one["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=admin_context,
            package_id=package_two["id"],
            site_id=site_two["id"],
            organization_id=org["id"]
        )

        # delete one of the associated sites
        helpers.call_action(
            "package_delete", context=admin_context, id=site_two["id"]
        )

        # the anon user can still see the associated packages of remaining site
        associated_packages = helpers.call_action(
            "ckanext_site_package_list", site_id=site_one["id"]
        )

        assert len(associated_packages) == 2

        # overview of packages can still be seen
        app.get("/dataset", status=200)


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSiteList(object):
    def test_site_list(self):
        """Site list action returns names of sites in site."""

        site_one = factories.Dataset(type="site")
        site_two = factories.Dataset(type="site")
        site_three = factories.Dataset(type="site")

        site_list = helpers.call_action("ckanext_site_list")

        site_list_name_id = [
            (sc["name"], sc["id"]) for sc in site_list
        ]

        assert len(site_list) == 3
        assert sorted(site_list_name_id) == sorted(
            [
                (site["name"], site["id"])
                for site in [site_one, site_two, site_three,]
            ]
        )

    def test_site_list_no_datasets(self):
        """
        Site list action doesn't return normal datasets (of type
        'dataset').
        """
        site_one = factories.Dataset(type="site")
        dataset_one = factories.Dataset()
        dataset_two = factories.Dataset()

        site_list = helpers.call_action("ckanext_site_list")

        site_list_name_id = [
            (sc["name"], sc["id"]) for sc in site_list
        ]

        assert len(site_list) == 1
        assert (
            site_one["name"],
            site_one["id"],
        ) in site_list_name_id
        assert (
            dataset_one["name"],
            dataset_one["id"],
        ) not in site_list_name_id
        assert (
            dataset_two["name"],
            dataset_two["id"],
        ) not in site_list_name_id


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSitePackageList(object):

    """Tests for ckanext_site_package_list"""

    def test_site_package_list_no_packages(self):
        """
        Calling ckanext_site_package_list with a site that has no
        packages returns an empty list.
        """
        site_id = factories.Dataset(type="site")["id"]

        pkg_list = helpers.call_action(
            "ckanext_site_package_list", site_id=site_id
        )

        assert pkg_list == []

    def test_site_package_list_works_with_name(self):
        """
        Calling ckanext_site_package_list with a site name doesn't
        raise a ValidationError.
        """
        site_name = factories.Dataset(type="site")["name"]

        pkg_list = helpers.call_action(
            "ckanext_site_package_list", site_id=site_name
        )

        assert pkg_list == []

    def test_site_package_list_wrong_site_id(self):
        """
        Calling ckanext_site_package_list with a bad site id raises a
        ValidationError.
        """
        factories.Dataset(type="site")["id"]

        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_site_package_list", site_id="a-bad-id",
            )

    def test_site_package_list_site_has_package(self):
        """
        Calling ckanext_site_package_list with a site that has a
        package should return that package.
        """
        sysadmin = factories.User(sysadmin=True)

        org = factories.Organization()
        package = factories.Dataset(owner_org=org["id"])
        site_id = factories.Dataset(type="site")["id"]
        context = {"user": sysadmin["name"]}
        # create an association
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package["id"],
            site_id=site_id,
            organization_id=org["id"]
        )

        pkg_list = helpers.call_action(
            "ckanext_site_package_list", site_id=site_id
        )

        # We've got an item in the pkg_list
        assert len(pkg_list) == 1
        # The list item should have the correct name property
        assert pkg_list[0]["name"] == package["name"]

    def test_site_package_list_site_has_two_packages(self):
        """
        Calling ckanext_site_package_list with a site that has two
        packages should return the packages.
        """
        sysadmin = factories.User(sysadmin=True)

        org = factories.Organization()
        package_one = factories.Dataset(owner_org=org["id"])
        package_two = factories.Dataset(owner_org=org["id"])
        site_id = factories.Dataset(type="site")["id"]
        context = {"user": sysadmin["name"]}
        # create first association
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package_one["id"],
            site_id=site_id,
            organization_id=org["id"]
        )
        # create second association
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package_two["id"],
            site_id=site_id,
            organization_id=org["id"]
        )

        pkg_list = helpers.call_action(
            "ckanext_site_package_list", site_id=site_id
        )

        # We've got two items in the pkg_list
        assert len(pkg_list) == 2

    def test_site_package_list_site_only_contains_active_datasets(
        self,
    ):
        """
        Calling ckanext_site_package_list will only return active datasets
        (not deleted ones).
        """
        sysadmin = factories.User(sysadmin=True)

        org = factories.Organization()
        package_one = factories.Dataset(owner_org=org["id"])
        package_two = factories.Dataset(owner_org=org["id"])
        package_three = factories.Dataset(owner_org=org["id"])
        site_id = factories.Dataset(type="site")["id"]
        context = {"user": sysadmin["name"]}
        # create first association
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package_one["id"],
            site_id=site_id,
            organization_id=org["id"]
        )
        # create second association
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package_two["id"],
            site_id=site_id,
            organization_id=org["id"]
        )
        # create third association
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package_three["id"],
            site_id=site_id,
            organization_id=org["id"]
        )

        # delete the first package
        helpers.call_action(
            "package_delete", context=context, id=package_one["id"]
        )

        pkg_list = helpers.call_action(
            "ckanext_site_package_list", site_id=site_id
        )

        # We've got two items in the pkg_list
        assert len(pkg_list) == 2

        pkg_list_ids = [pkg["id"] for pkg in pkg_list]
        assert package_two["id"] in pkg_list_ids
        assert package_three["id"] in pkg_list_ids
        assert package_one["id"] not in pkg_list_ids

    def test_site_package_list_package_isnot_a_site(self):
        """
        Calling ckanext_site_package_list with a package id should raise a
        ValidationError.

        Since Sites are Packages under the hood, make sure we treat them
        differently.
        """
        sysadmin = factories.User(sysadmin=True)

        org = factories.Organization()
        package = factories.Dataset(owner_org=org["id"])
        site_id = factories.Dataset(type="site")["id"]
        context = {"user": sysadmin["name"]}
        # create an association
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package["id"],
            site_id=site_id,
            organization_id=org["id"]
        )

        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_site_package_list", site_id=package["id"],
            )


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestPackageSiteList(object):

    """Tests for ckanext_package_site_list"""

    def test_package_site_list_no_sites(self):
        """
        Calling ckanext_package_site_list with a package that has no
        sites returns an empty list.
        """
        package_id = factories.Dataset()["id"]

        site_list = helpers.call_action(
            "ckanext_package_site_list", package_id=package_id
        )

        assert site_list == []

    def test_package_site_list_works_with_name(self):
        """
        Calling ckanext_package_site_list with a package name doesn't
        raise a ValidationError.
        """
        package_name = factories.Dataset()["name"]

        site_list = helpers.call_action(
            "ckanext_package_site_list", package_id=package_name
        )

        assert site_list == []

    def test_package_site_list_wrong_site_id(self):
        """
        Calling ckanext_package_site_list with a bad package id raises a
        ValidationError.
        """
        factories.Dataset()["id"]

        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_package_site_list", site_id="a-bad-id",
            )

    def test_package_site_list_site_has_package(self):
        """
        Calling ckanext_package_site_list with a package that has a
        site should return that site.
        """
        sysadmin = factories.User(sysadmin=True)

        org = factories.Organization()
        package = factories.Dataset(owner_org=org["id"])
        site = factories.Dataset(type="site")
        context = {"user": sysadmin["name"]}
        # create an association
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package["id"],
            site_id=site["id"],
            organization_id=org["id"]
        )

        site_list = helpers.call_action(
            "ckanext_package_site_list", package_id=package["id"]
        )

        # We've got an item in the site_list
        assert len(site_list) == 1
        # The list item should have the correct name property
        assert site_list[0]["name"] == site["name"]

    def test_package_site_list_site_has_two_packages(self):
        """
        Calling ckanext_package_site_list with a package that has two
        sites should return the sites.
        """
        sysadmin = factories.User(sysadmin=True)

        org = factories.Organization()
        package = factories.Dataset(owner_org=org["id"])
        site_one = factories.Dataset(type="site")
        site_two = factories.Dataset(type="site")
        context = {"user": sysadmin["name"]}
        # create first association
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package["id"],
            site_id=site_one["id"],
            organization_id=org["id"]
        )
        # create second association
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package["id"],
            site_id=site_two["id"],
            organization_id=org["id"]
        )

        site_list = helpers.call_action(
            "ckanext_package_site_list", package_id=package["id"]
        )

        # We've got two items in the site_list
        assert len(site_list) == 2

    def test_package_site_list_package_isnot_a_site(self):
        """
        Calling ckanext_package_site_list with a site id should raise a
        ValidationError.

        Since Sites are Packages under the hood, make sure we treat them
        differently.
        """
        sysadmin = factories.User(sysadmin=True)

        org = factories.Organization()
        package = factories.Dataset(owner_org=org["id"])
        site = factories.Dataset(type="site")
        context = {"user": sysadmin["name"]}
        # create an association
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package["id"],
            site_id=site["id"],
            organization_id=org["id"]
        )

        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_package_site_list", package_id=site["id"],
            )


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSiteAdminList(object):

    """Tests for ckanext_site_admin_list"""

    def test_site_admin_list_no_site_admins(self):
        """
        Calling ckanext_site_admin_list on a site that has no sites
        admins returns an empty list.
        """

        site_admin_list = helpers.call_action(
            "ckanext_site_admin_list"
        )

        assert site_admin_list == []

    def test_site_admin_list_users(self):
        """
        Calling ckanext_site_admin_list will return users who are site
        admins.
        """
        user_one = factories.User()
        user_two = factories.User()
        user_three = factories.User()

        helpers.call_action(
            "ckanext_site_admin_add", context={}, username=user_one["name"]
        )
        helpers.call_action(
            "ckanext_site_admin_add", context={}, username=user_two["name"]
        )
        helpers.call_action(
            "ckanext_site_admin_add",
            context={},
            username=user_three["name"],
        )

        site_admin_list = helpers.call_action(
            "ckanext_site_admin_list", context={}
        )

        assert len(site_admin_list) == 3
        for user in [user_one, user_two, user_three]:
            assert {
                "name": user["name"],
                "id": user["id"],
            } in site_admin_list

    def test_site_admin_only_lists_admin_users(self):
        """
        Calling ckanext_site_admin_list will only return users who are
        site admins.
        """
        user_one = factories.User()
        user_two = factories.User()
        user_three = factories.User()

        helpers.call_action(
            "ckanext_site_admin_add", context={}, username=user_one["name"]
        )
        helpers.call_action(
            "ckanext_site_admin_add", context={}, username=user_two["name"]
        )

        site_admin_list = helpers.call_action(
            "ckanext_site_admin_list", context={}
        )

        assert len(site_admin_list) == 2
        # user three isn't in list
        assert {
            "name": user_three["name"],
            "id": user_three["id"],
        } not in site_admin_list


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestPackageSearchBeforeSearch(object):

    """
    Site uses the `before_search` method to alter search parameters.
    """

    def test_package_search_no_additional_filters(self):
        """
        Perform package_search with no additional filters should not include
        sites.
        """
        factories.Dataset()
        factories.Dataset()
        factories.Dataset(type="site")
        factories.Dataset(type="custom")

        search_results = helpers.call_action("package_search", context={})[
            "results"
        ]

        types = [result["type"] for result in search_results]

        assert len(search_results) == 3
        assert "site" not in types
        assert "custom" in types

    def test_package_search_filter_include_site(self):
        """
        package_search filtered to include datasets of type site should
        only include sites.
        """
        factories.Dataset()
        factories.Dataset()
        factories.Dataset(type="site")
        factories.Dataset(type="custom")

        search_results = helpers.call_action(
            "package_search", context={}, fq="dataset_type:site"
        )["results"]

        types = [result["type"] for result in search_results]

        assert len(search_results) == 1
        assert "site" in types
        assert "custom" not in types
        assert "dataset" not in types


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestUserShowBeforeSearch(object):

    """
    Site uses the `before_search` method to alter results of user_show
    (via package_search).
    """

    def test_user_show_no_additional_filters(self):
        """
        Perform package_search with no additional filters should not include
        sites.
        """

        user = factories.User()
        factories.Dataset(user=user)
        factories.Dataset(user=user)
        factories.Dataset(user=user, type="site")
        factories.Dataset(user=user, type="custom")

        search_results = helpers.call_action(
            "user_show", context={}, include_datasets=True, id=user["name"]
        )["datasets"]

        types = [result["type"] for result in search_results]

        assert len(search_results) == 3
        assert "site" not in types
        assert "custom" in types
