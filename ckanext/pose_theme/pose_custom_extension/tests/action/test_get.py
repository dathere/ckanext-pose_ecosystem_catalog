# -*- coding: utf-8 -*-

import pytest

from ckan.tests import factories, helpers
import ckan.plugins.toolkit as toolkit


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestExtensionshow(object):
    def test_extension_show_no_args(self):
        """
        Calling extension show with no args raises a ValidationError.
        """
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action("ckanext_extension_show")

    def test_extension_show_with_id(self):
        """
        Calling extension show with id arg returns extension dict.
        """
        my_extension = factories.Dataset(type="extension", name="my-extension")

        extension_shown = helpers.call_action(
            "ckanext_extension_show", id=my_extension["id"]
        )

        assert my_extension["name"] == extension_shown["name"]

    def test_extension_show_with_name(self):
        """
        Calling extension show with name arg returns extension dict.
        """
        my_extension = factories.Dataset(type="extension", name="my-extension")

        extension_shown = helpers.call_action(
            "ckanext_extension_show", id=my_extension["name"]
        )

        assert my_extension["id"] == extension_shown["id"]

    def test_extension_show_with_nonexisting_name(self):
        """
        Calling extension show with bad name arg returns ObjectNotFound.
        """
        factories.Dataset(type="extension", name="my-extension")

        with pytest.raises(toolkit.ObjectNotFound):
            helpers.call_action(
                "ckanext_extension_show", id="my-bad-name",
            )

    def test_extension_show_num_datasets_added(self):
        """
        num_datasets property returned with extension dict.
        """
        my_extension = factories.Dataset(type="extension", name="my-extension")

        extension_shown = helpers.call_action(
            "ckanext_extension_show", id=my_extension["name"]
        )

        assert "num_datasets" in extension_shown
        assert extension_shown["num_datasets"] == 0

    def test_extension_show_num_datasets_correct_value(self):
        """
        num_datasets property has correct value.
        """

        sysadmin = factories.User(sysadmin=True)

        my_extension = factories.Dataset(type="extension", name="my-extension")
        org = factories.Organization()
        package_one = factories.Dataset(owner_org=org["id"])
        package_two = factories.Dataset(owner_org=org["id"])

        context = {"user": sysadmin["name"]}
        # create an association
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package_one["id"],
            extension_id=my_extension["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package_two["id"],
            extension_id=my_extension["id"],
            organization_id=org["id"]
        )

        extension_shown = helpers.call_action(
            "ckanext_extension_show", id=my_extension["name"]
        )

        assert extension_shown["num_datasets"] == 2

    def test_extension_show_num_datasets_correct_only_count_active_datasets(
        self,
    ):
        """
        num_datasets property has correct value when some previously
        associated datasets have been datasets.
        """
        sysadmin = factories.User(sysadmin=True)

        my_extension = factories.Dataset(type="extension", name="my-extension")
        org = factories.Organization()
        package_one = factories.Dataset(owner_org=org["id"])
        package_two = factories.Dataset(owner_org=org["id"])
        package_three = factories.Dataset(owner_org=org["id"])

        context = {"user": sysadmin["name"]}
        # create the associations
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package_one["id"],
            extension_id=my_extension["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package_two["id"],
            extension_id=my_extension["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package_three["id"],
            extension_id=my_extension["id"],
            organization_id=org["id"]
        )

        # delete the first package
        helpers.call_action(
            "package_delete", context=context, id=package_one["id"]
        )

        extension_shown = helpers.call_action(
            "ckanext_extension_show", id=my_extension["name"]
        )

        # the num_datasets should only include active datasets
        assert extension_shown["num_datasets"] == 2

    def test_extension_anon_user_can_see_package_list_when_extension_association_was_deleted(
        self, app
    ):
        """
        When a extension is deleted, the remaining associations with formerly associated
        packages or extensions can still be displayed.
        """

        sysadmin = factories.User(sysadmin=True)

        extension_one = factories.Dataset(type="extension", name="extension-one")
        extension_two = factories.Dataset(type="extension", name="extension-two")
        org = factories.Organization()
        package_one = factories.Dataset(owner_org=org["id"])
        package_two = factories.Dataset(owner_org=org["id"])

        admin_context = {"user": sysadmin["name"]}

        # create the associations
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=admin_context,
            package_id=package_one["id"],
            extension_id=extension_one["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=admin_context,
            package_id=package_one["id"],
            extension_id=extension_two["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=admin_context,
            package_id=package_two["id"],
            extension_id=extension_one["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=admin_context,
            package_id=package_two["id"],
            extension_id=extension_two["id"],
            organization_id=org["id"]
        )

        # delete one of the associated extensions
        helpers.call_action(
            "package_delete", context=admin_context, id=extension_two["id"]
        )

        # the anon user can still see the associated packages of remaining extension
        associated_packages = helpers.call_action(
            "ckanext_extension_package_list", extension_id=extension_one["id"]
        )

        assert len(associated_packages) == 2

        # overview of packages can still be seen
        app.get("/dataset", status=200)


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestExtensionList(object):
    def test_extension_list(self):
        """Extension list action returns names of extensions in site."""

        extension_one = factories.Dataset(type="extension")
        extension_two = factories.Dataset(type="extension")
        extension_three = factories.Dataset(type="extension")

        extension_list = helpers.call_action("ckanext_extension_list")

        extension_list_name_id = [
            (sc["name"], sc["id"]) for sc in extension_list
        ]

        assert len(extension_list) == 3
        assert sorted(extension_list_name_id) == sorted(
            [
                (extension["name"], extension["id"])
                for extension in [extension_one, extension_two, extension_three,]
            ]
        )

    def test_extension_list_no_datasets(self):
        """
        Extension list action doesn't return normal datasets (of type
        'dataset').
        """
        extension_one = factories.Dataset(type="extension")
        dataset_one = factories.Dataset()
        dataset_two = factories.Dataset()

        extension_list = helpers.call_action("ckanext_extension_list")

        extension_list_name_id = [
            (sc["name"], sc["id"]) for sc in extension_list
        ]

        assert len(extension_list) == 1
        assert (
            extension_one["name"],
            extension_one["id"],
        ) in extension_list_name_id
        assert (
            dataset_one["name"],
            dataset_one["id"],
        ) not in extension_list_name_id
        assert (
            dataset_two["name"],
            dataset_two["id"],
        ) not in extension_list_name_id


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestExtensionPackageList(object):

    """Tests for ckanext_extension_package_list"""

    def test_extension_package_list_no_packages(self):
        """
        Calling ckanext_extension_package_list with a extension that has no
        packages returns an empty list.
        """
        extension_id = factories.Dataset(type="extension")["id"]

        pkg_list = helpers.call_action(
            "ckanext_extension_package_list", extension_id=extension_id
        )

        assert pkg_list == []

    def test_extension_package_list_works_with_name(self):
        """
        Calling ckanext_extension_package_list with a extension name doesn't
        raise a ValidationError.
        """
        extension_name = factories.Dataset(type="extension")["name"]

        pkg_list = helpers.call_action(
            "ckanext_extension_package_list", extension_id=extension_name
        )

        assert pkg_list == []

    def test_extension_package_list_wrong_extension_id(self):
        """
        Calling ckanext_extension_package_list with a bad extension id raises a
        ValidationError.
        """
        factories.Dataset(type="extension")["id"]

        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_extension_package_list", extension_id="a-bad-id",
            )

    def test_extension_package_list_extension_has_package(self):
        """
        Calling ckanext_extension_package_list with a extension that has a
        package should return that package.
        """
        sysadmin = factories.User(sysadmin=True)

        org = factories.Organization()
        package = factories.Dataset(owner_org=org["id"])
        extension_id = factories.Dataset(type="extension")["id"]
        context = {"user": sysadmin["name"]}
        # create an association
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package["id"],
            extension_id=extension_id,
            organization_id=org["id"]
        )

        pkg_list = helpers.call_action(
            "ckanext_extension_package_list", extension_id=extension_id
        )

        # We've got an item in the pkg_list
        assert len(pkg_list) == 1
        # The list item should have the correct name property
        assert pkg_list[0]["name"] == package["name"]

    def test_extension_package_list_extension_has_two_packages(self):
        """
        Calling ckanext_extension_package_list with a extension that has two
        packages should return the packages.
        """
        sysadmin = factories.User(sysadmin=True)

        org = factories.Organization()
        package_one = factories.Dataset(owner_org=org["id"])
        package_two = factories.Dataset(owner_org=org["id"])
        extension_id = factories.Dataset(type="extension")["id"]
        context = {"user": sysadmin["name"]}
        # create first association
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package_one["id"],
            extension_id=extension_id,
            organization_id=org["id"]
        )
        # create second association
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package_two["id"],
            extension_id=extension_id,
            organization_id=org["id"]
        )

        pkg_list = helpers.call_action(
            "ckanext_extension_package_list", extension_id=extension_id
        )

        # We've got two items in the pkg_list
        assert len(pkg_list) == 2

    def test_extension_package_list_extension_only_contains_active_datasets(
        self,
    ):
        """
        Calling ckanext_extension_package_list will only return active datasets
        (not deleted ones).
        """
        sysadmin = factories.User(sysadmin=True)

        org = factories.Organization()
        package_one = factories.Dataset(owner_org=org["id"])
        package_two = factories.Dataset(owner_org=org["id"])
        package_three = factories.Dataset(owner_org=org["id"])
        extension_id = factories.Dataset(type="extension")["id"]
        context = {"user": sysadmin["name"]}
        # create first association
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package_one["id"],
            extension_id=extension_id,
            organization_id=org["id"]
        )
        # create second association
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package_two["id"],
            extension_id=extension_id,
            organization_id=org["id"]
        )
        # create third association
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package_three["id"],
            extension_id=extension_id,
            organization_id=org["id"]
        )

        # delete the first package
        helpers.call_action(
            "package_delete", context=context, id=package_one["id"]
        )

        pkg_list = helpers.call_action(
            "ckanext_extension_package_list", extension_id=extension_id
        )

        # We've got two items in the pkg_list
        assert len(pkg_list) == 2

        pkg_list_ids = [pkg["id"] for pkg in pkg_list]
        assert package_two["id"] in pkg_list_ids
        assert package_three["id"] in pkg_list_ids
        assert package_one["id"] not in pkg_list_ids

    def test_extension_package_list_package_isnot_a_extension(self):
        """
        Calling ckanext_extension_package_list with a package id should raise a
        ValidationError.

        Since Extensions are Packages under the hood, make sure we treat them
        differently.
        """
        sysadmin = factories.User(sysadmin=True)

        org = factories.Organization()
        package = factories.Dataset(owner_org=org["id"])
        extension_id = factories.Dataset(type="extension")["id"]
        context = {"user": sysadmin["name"]}
        # create an association
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package["id"],
            extension_id=extension_id,
            organization_id=org["id"]
        )

        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_extension_package_list", extension_id=package["id"],
            )


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestPackageExtensionList(object):

    """Tests for ckanext_package_extension_list"""

    def test_package_extension_list_no_extensions(self):
        """
        Calling ckanext_package_extension_list with a package that has no
        extensions returns an empty list.
        """
        package_id = factories.Dataset()["id"]

        extension_list = helpers.call_action(
            "ckanext_package_extension_list", package_id=package_id
        )

        assert extension_list == []

    def test_package_extension_list_works_with_name(self):
        """
        Calling ckanext_package_extension_list with a package name doesn't
        raise a ValidationError.
        """
        package_name = factories.Dataset()["name"]

        extension_list = helpers.call_action(
            "ckanext_package_extension_list", package_id=package_name
        )

        assert extension_list == []

    def test_package_extension_list_wrong_extension_id(self):
        """
        Calling ckanext_package_extension_list with a bad package id raises a
        ValidationError.
        """
        factories.Dataset()["id"]

        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_package_extension_list", extension_id="a-bad-id",
            )

    def test_package_extension_list_extension_has_package(self):
        """
        Calling ckanext_package_extension_list with a package that has a
        extension should return that extension.
        """
        sysadmin = factories.User(sysadmin=True)

        org = factories.Organization()
        package = factories.Dataset(owner_org=org["id"])
        extension = factories.Dataset(type="extension")
        context = {"user": sysadmin["name"]}
        # create an association
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package["id"],
            extension_id=extension["id"],
            organization_id=org["id"]
        )

        extension_list = helpers.call_action(
            "ckanext_package_extension_list", package_id=package["id"]
        )

        # We've got an item in the extension_list
        assert len(extension_list) == 1
        # The list item should have the correct name property
        assert extension_list[0]["name"] == extension["name"]

    def test_package_extension_list_extension_has_two_packages(self):
        """
        Calling ckanext_package_extension_list with a package that has two
        extensions should return the extensions.
        """
        sysadmin = factories.User(sysadmin=True)

        org = factories.Organization()
        package = factories.Dataset(owner_org=org["id"])
        extension_one = factories.Dataset(type="extension")
        extension_two = factories.Dataset(type="extension")
        context = {"user": sysadmin["name"]}
        # create first association
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package["id"],
            extension_id=extension_one["id"],
            organization_id=org["id"]
        )
        # create second association
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package["id"],
            extension_id=extension_two["id"],
            organization_id=org["id"]
        )

        extension_list = helpers.call_action(
            "ckanext_package_extension_list", package_id=package["id"]
        )

        # We've got two items in the extension_list
        assert len(extension_list) == 2

    def test_package_extension_list_package_isnot_a_extension(self):
        """
        Calling ckanext_package_extension_list with a extension id should raise a
        ValidationError.

        Since Extensions are Packages under the hood, make sure we treat them
        differently.
        """
        sysadmin = factories.User(sysadmin=True)

        org = factories.Organization()
        package = factories.Dataset(owner_org=org["id"])
        extension = factories.Dataset(type="extension")
        context = {"user": sysadmin["name"]}
        # create an association
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package["id"],
            extension_id=extension["id"],
            organization_id=org["id"]
        )

        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_package_extension_list", package_id=extension["id"],
            )


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestExtensionAdminList(object):

    """Tests for ckanext_extension_admin_list"""

    def test_extension_admin_list_no_extension_admins(self):
        """
        Calling ckanext_extension_admin_list on a site that has no extensions
        admins returns an empty list.
        """

        extension_admin_list = helpers.call_action(
            "ckanext_extension_admin_list"
        )

        assert extension_admin_list == []

    def test_extension_admin_list_users(self):
        """
        Calling ckanext_extension_admin_list will return users who are extension
        admins.
        """
        user_one = factories.User()
        user_two = factories.User()
        user_three = factories.User()

        helpers.call_action(
            "ckanext_extension_admin_add", context={}, username=user_one["name"]
        )
        helpers.call_action(
            "ckanext_extension_admin_add", context={}, username=user_two["name"]
        )
        helpers.call_action(
            "ckanext_extension_admin_add",
            context={},
            username=user_three["name"],
        )

        extension_admin_list = helpers.call_action(
            "ckanext_extension_admin_list", context={}
        )

        assert len(extension_admin_list) == 3
        for user in [user_one, user_two, user_three]:
            assert {
                "name": user["name"],
                "id": user["id"],
            } in extension_admin_list

    def test_extension_admin_only_lists_admin_users(self):
        """
        Calling ckanext_extension_admin_list will only return users who are
        extension admins.
        """
        user_one = factories.User()
        user_two = factories.User()
        user_three = factories.User()

        helpers.call_action(
            "ckanext_extension_admin_add", context={}, username=user_one["name"]
        )
        helpers.call_action(
            "ckanext_extension_admin_add", context={}, username=user_two["name"]
        )

        extension_admin_list = helpers.call_action(
            "ckanext_extension_admin_list", context={}
        )

        assert len(extension_admin_list) == 2
        # user three isn't in list
        assert {
            "name": user_three["name"],
            "id": user_three["id"],
        } not in extension_admin_list


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestPackageSearchBeforeSearch(object):

    """
    Extension uses the `before_search` method to alter search parameters.
    """

    def test_package_search_no_additional_filters(self):
        """
        Perform package_search with no additional filters should not include
        extensions.
        """
        factories.Dataset()
        factories.Dataset()
        factories.Dataset(type="extension")
        factories.Dataset(type="custom")

        search_results = helpers.call_action("package_search", context={})[
            "results"
        ]

        types = [result["type"] for result in search_results]

        assert len(search_results) == 3
        assert "extension" not in types
        assert "custom" in types

    def test_package_search_filter_include_extension(self):
        """
        package_search filtered to include datasets of type extension should
        only include extensions.
        """
        factories.Dataset()
        factories.Dataset()
        factories.Dataset(type="extension")
        factories.Dataset(type="custom")

        search_results = helpers.call_action(
            "package_search", context={}, fq="dataset_type:extension"
        )["results"]

        types = [result["type"] for result in search_results]

        assert len(search_results) == 1
        assert "extension" in types
        assert "custom" not in types
        assert "dataset" not in types


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestUserShowBeforeSearch(object):

    """
    Extension uses the `before_search` method to alter results of user_show
    (via package_search).
    """

    def test_user_show_no_additional_filters(self):
        """
        Perform package_search with no additional filters should not include
        extensions.
        """

        user = factories.User()
        factories.Dataset(user=user)
        factories.Dataset(user=user)
        factories.Dataset(user=user, type="extension")
        factories.Dataset(user=user, type="custom")

        search_results = helpers.call_action(
            "user_show", context={}, include_datasets=True, id=user["name"]
        )["datasets"]

        types = [result["type"] for result in search_results]

        assert len(search_results) == 3
        assert "extension" not in types
        assert "custom" in types
