import pytest

import ckan.model as model
import ckan.plugins.toolkit as toolkit

from ckan.tests import factories, helpers

from ckanext.extension.model import ExtensionPackageAssociation, ExtensionAdmin
from ckan.model.package import Package


@pytest.mark.usefixtures("clean_db")
class TestDeleteExtension(object):
    def test_extension_delete_no_args(self):
        """
        Calling extension delete with no args raises a ValidationError.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_extension_delete", context=context,
            )

    def test_extension_delete_incorrect_args(self):
        """
        Calling extension delete with incorrect args raises ObjectNotFound.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}
        factories.Dataset(type="extension")
        with pytest.raises(toolkit.ObjectNotFound):
            helpers.call_action(
                "ckanext_extension_delete", context=context, id="blah-blah",
            )

    def test_extension_delete_by_id(self):
        """
        Calling extension delete with extension id.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}
        extension = factories.Dataset(type="extension")

        # One extension object created
        assert (
            model.Session.query(Package)
            .filter(Package.type == "extension")
            .count()
            == 1
        )

        helpers.call_action(
            "ckanext_extension_delete", context=context, id=extension["id"]
        )

        assert (
            model.Session.query(Package)
            .filter(Package.type == "extension")
            .count()
            == 0
        )

    def test_extension_delete_by_name(self):
        """
        Calling extension delete with extension name.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}
        extension = factories.Dataset(type="extension")

        # One extension object created
        assert (
            model.Session.query(Package)
            .filter(Package.type == "extension")
            .count()
            == 1
        )

        helpers.call_action(
            "ckanext_extension_delete", context=context, id=extension["name"]
        )

        assert (
            model.Session.query(Package)
            .filter(Package.type == "extension")
            .count()
            == 0
        )

    def test_extension_delete_removes_associations(self):
        """
        Deleting a extension also deletes associated ExtensionPackageAssociation
        objects.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}
        org = factories.Organization()
        extension = factories.Dataset(type="extension", name="my-extension")
        dataset_one = factories.Dataset(name="dataset-one", owner_org=org["id"])
        dataset_two = factories.Dataset(name="dataset-two", owner_org=org["id"])

        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=dataset_one["id"],
            extension_id=extension["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=dataset_two["id"],
            extension_id=extension["id"],
            organization_id=org["id"]
        )

        assert model.Session.query(ExtensionPackageAssociation).count() == 2

        helpers.call_action(
            "ckanext_extension_delete", context=context, id=extension["id"]
        )

        assert model.Session.query(ExtensionPackageAssociation).count() == 0


@pytest.mark.usefixtures("clean_db")
class TestDeletePackage(object):
    def test_package_delete_retains_associations(self):
        """
        Deleting a package (setting its status to 'delete') retains associated
        ExtensionPackageAssociation objects.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}
        org = factories.Organization()
        extension = factories.Dataset(type="extension", name="my-extension")
        dataset_one = factories.Dataset(name="dataset-one", owner_org=org["id"])
        dataset_two = factories.Dataset(name="dataset-two", owner_org=org["id"])

        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=dataset_one["id"],
            extension_id=extension["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=dataset_two["id"],
            extension_id=extension["id"],
            organization_id=org["id"]
        )

        assert model.Session.query(ExtensionPackageAssociation).count() == 2

        # delete the first package, should also delete the
        # ExtensionPackageAssociation associated with it.
        helpers.call_action(
            "package_delete", context=context, id=dataset_one["id"]
        )

        assert model.Session.query(ExtensionPackageAssociation).count() == 2

    def test_package_purge_deletes_associations(self):
        """
        Purging a package (actually deleting it from the database) deletes
        associated ExtensionPackageAssociation objects.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}
        org = factories.Organization()
        extension = factories.Dataset(type="extension", name="my-extension")
        dataset_one = factories.Dataset(name="dataset-one", owner_org=org["id"])
        dataset_two = factories.Dataset(name="dataset-two", owner_org=org["id"])

        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=dataset_one["id"],
            extension_id=extension["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=dataset_two["id"],
            extension_id=extension["id"],
            organization_id=org["id"]
        )

        assert model.Session.query(ExtensionPackageAssociation).count() == 2

        # purge the first package, should also delete the
        # ExtensionPackageAssociation associated with it.
        pkg = model.Session.query(model.Package).get(dataset_one["id"])
        pkg.purge()
        model.repo.commit_and_remove()

        assert model.Session.query(ExtensionPackageAssociation).count() == 1


@pytest.mark.usefixtures("clean_db")
class TestDeleteExtensionPackageAssociation(object):
    def test_association_delete_no_args(self):
        """
        Calling sc/pkg association delete with no args raises ValidationError.
        """
        sysadmin = factories.User(sysadmin=True)
        context = {"user": sysadmin["name"]}
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_extension_package_association_delete", context=context,
            )

    def test_association_delete_missing_arg(self):
        """
        Calling sc/pkg association delete with a missing arg raises
        ValidationError.
        """
        sysadmin = factories.User(sysadmin=True)
        package_id = factories.Dataset()["id"]

        context = {"user": sysadmin["name"]}
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_extension_package_association_delete",
                context=context,
                package_id=package_id,
            )

    def test_association_delete_by_id(self):
        """
        Calling sc/pkg association delete with correct args (package ids)
        correctly deletes an association.
        """
        sysadmin = factories.User(sysadmin=True)
        organization_id = factories.Organization()["id"]
        package_id = factories.Dataset(owner_org=organization_id)["id"]
        extension_id = factories.Dataset(type="extension")["id"]

        context = {"user": sysadmin["name"]}
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package_id,
            extension_id=extension_id,
            organization_id=organization_id
        )

        # One association object created
        assert model.Session.query(ExtensionPackageAssociation).count() == 1

        helpers.call_action(
            "ckanext_extension_package_association_delete",
            context=context,
            package_id=package_id,
            extension_id=extension_id,
            organization_id=organization_id
        )

    def test_association_delete_attempt_with_non_existent_association(self):
        """
        Attempting to delete a non-existent association (package ids exist,
        but aren't associated with each other), will cause a NotFound error.
        """
        sysadmin = factories.User(sysadmin=True)
        organization_id = factories.Organization()["id"]
        package_id = factories.Dataset(owner_org=organization_id)["id"]
        extension_id = factories.Dataset(type="extension")["id"]

        # No existing associations
        assert model.Session.query(ExtensionPackageAssociation).count() == 0

        context = {"user": sysadmin["name"]}
        with pytest.raises(toolkit.ObjectNotFound):
            helpers.call_action(
                "ckanext_extension_package_association_delete",
                context=context,
                package_id=package_id,
                extension_id=extension_id,
                organization_id=organization_id
            )

    def test_association_delete_attempt_with_bad_package_ids(self):
        """
        Attempting to delete an association by passing non-existent package
        ids will cause a ValidationError.
        """
        sysadmin = factories.User(sysadmin=True)

        # No existing associations
        assert model.Session.query(ExtensionPackageAssociation).count() == 0

        context = {"user": sysadmin["name"]}
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_extension_package_association_delete",
                context=context,
                package_id="my-bad-package-id",
                extension_id="my-bad-extension-id",
                organization_id="my-bad-organization-id"
            )

    def test_association_delete_retains_packages(self):
        """
        Deleting a sc/pkg association doesn't delete the associated packages.
        """
        sysadmin = factories.User(sysadmin=True)
        organization_id = factories.Organization()["id"]
        package_id = factories.Dataset(owner_org=organization_id)["id"]
        extension_id = factories.Dataset(type="extension")["id"]

        context = {"user": sysadmin["name"]}
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package_id,
            extension_id=extension_id,
            organization_id=organization_id
        )

        helpers.call_action(
            "ckanext_extension_package_association_delete",
            context=context,
            package_id=package_id,
            extension_id=extension_id,
        )

        # package still exist
        assert (
            model.Session.query(Package)
            .filter(Package.type == "dataset")
            .count()
            == 1
        )

        # extension still exist
        assert (
            model.Session.query(Package)
            .filter(Package.type == "extension")
            .count()
            == 1
        )


@pytest.mark.usefixtures("clean_db")
class TestRemoveExtensionAdmin(object):
    def test_extension_admin_remove_deletes_extension_admin_user(self):
        """
        Calling ckanext_extension_admin_remove deletes ExtensionAdmin object.
        """
        user = factories.User()

        helpers.call_action(
            "ckanext_extension_admin_add", context={}, username=user["name"]
        )

        # There's a ExtensionAdmin obj
        assert model.Session.query(ExtensionAdmin).count() == 1

        helpers.call_action(
            "ckanext_extension_admin_remove", context={}, username=user["name"]
        )

        # There's no ExtensionAdmin obj
        assert model.Session.query(ExtensionAdmin).count() == 0
        assert ExtensionAdmin.get_extension_admin_ids() == []

    def test_extension_admin_delete_user_removes_extension_admin_object(self):
        """
        Deleting a user also deletes the corresponding ExtensionAdmin object.
        """
        user = factories.User()

        helpers.call_action(
            "ckanext_extension_admin_add", context={}, username=user["name"]
        )

        # There's a ExtensionAdmin object
        assert model.Session.query(ExtensionAdmin).count() == 1
        assert user["id"] in ExtensionAdmin.get_extension_admin_ids()

        # purge the user, should also delete the ExtensionAdmin object
        # associated with it.
        user_obj = model.Session.query(model.User).get(user["id"])
        user_obj.purge()
        model.repo.commit_and_remove()

        # The ExtensionAdmin has also been removed
        assert model.Session.query(ExtensionAdmin).count() == 0
        assert ExtensionAdmin.get_extension_admin_ids() == []

    def test_extension_admin_remove_retains_user(self):
        """
        Deleting a ExtensionAdmin object doesn't delete the corresponding user.
        """

        user = factories.User()

        helpers.call_action(
            "ckanext_extension_admin_add", context={}, username=user["name"]
        )

        # We have a user
        user_obj = model.Session.query(model.User).get(user["id"])
        assert user_obj is not None

        helpers.call_action(
            "ckanext_extension_admin_remove", context={}, username=user["name"]
        )

        # We still have a user
        user_obj = model.Session.query(model.User).get(user["id"])
        assert user_obj is not None

    def test_extension_admin_remove_with_bad_username(self):
        """
        Calling extension admin remove with a non-existent user raises
        ValidationError.
        """

        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_extension_admin_remove",
                context={},
                username="no-one-here",
            )

    def test_extension_admin_remove_with_no_args(self):
        """
        Calling extension admin remove with no arg raises ValidationError.
        """

        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_extension_admin_remove", context={},
            )
