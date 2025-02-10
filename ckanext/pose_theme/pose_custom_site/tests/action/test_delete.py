import pytest

import ckan.model as model
import ckan.plugins.toolkit as toolkit

from ckan.tests import factories, helpers

from ckanext.site.model import SitePackageAssociation, SiteAdmin
from ckan.model.package import Package


@pytest.mark.usefixtures("clean_db")
class TestDeleteSite(object):
    def test_site_delete_no_args(self):
        """
        Calling site delete with no args raises a ValidationError.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_site_delete", context=context,
            )

    def test_site_delete_incorrect_args(self):
        """
        Calling site delete with incorrect args raises ObjectNotFound.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}
        factories.Dataset(type="site")
        with pytest.raises(toolkit.ObjectNotFound):
            helpers.call_action(
                "ckanext_site_delete", context=context, id="blah-blah",
            )

    def test_site_delete_by_id(self):
        """
        Calling site delete with site id.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}
        site = factories.Dataset(type="site")

        # One site object created
        assert (
            model.Session.query(Package)
            .filter(Package.type == "site")
            .count()
            == 1
        )

        helpers.call_action(
            "ckanext_site_delete", context=context, id=site["id"]
        )

        assert (
            model.Session.query(Package)
            .filter(Package.type == "site")
            .count()
            == 0
        )

    def test_site_delete_by_name(self):
        """
        Calling site delete with site name.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}
        site = factories.Dataset(type="site")

        # One site object created
        assert (
            model.Session.query(Package)
            .filter(Package.type == "site")
            .count()
            == 1
        )

        helpers.call_action(
            "ckanext_site_delete", context=context, id=site["name"]
        )

        assert (
            model.Session.query(Package)
            .filter(Package.type == "site")
            .count()
            == 0
        )

    def test_site_delete_removes_associations(self):
        """
        Deleting a site also deletes associated SitePackageAssociation
        objects.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}
        org = factories.Organization()
        site = factories.Dataset(type="site", name="my-site")
        dataset_one = factories.Dataset(name="dataset-one", owner_org=org["id"])
        dataset_two = factories.Dataset(name="dataset-two", owner_org=org["id"])

        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=dataset_one["id"],
            site_id=site["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=dataset_two["id"],
            site_id=site["id"],
            organization_id=org["id"]
        )

        assert model.Session.query(SitePackageAssociation).count() == 2

        helpers.call_action(
            "ckanext_site_delete", context=context, id=site["id"]
        )

        assert model.Session.query(SitePackageAssociation).count() == 0


@pytest.mark.usefixtures("clean_db")
class TestDeletePackage(object):
    def test_package_delete_retains_associations(self):
        """
        Deleting a package (setting its status to 'delete') retains associated
        SitePackageAssociation objects.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}
        org = factories.Organization()
        site = factories.Dataset(type="site", name="my-site")
        dataset_one = factories.Dataset(name="dataset-one", owner_org=org["id"])
        dataset_two = factories.Dataset(name="dataset-two", owner_org=org["id"])

        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=dataset_one["id"],
            site_id=site["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=dataset_two["id"],
            site_id=site["id"],
            organization_id=org["id"]
        )

        assert model.Session.query(SitePackageAssociation).count() == 2

        # delete the first package, should also delete the
        # SitePackageAssociation associated with it.
        helpers.call_action(
            "package_delete", context=context, id=dataset_one["id"]
        )

        assert model.Session.query(SitePackageAssociation).count() == 2

    def test_package_purge_deletes_associations(self):
        """
        Purging a package (actually deleting it from the database) deletes
        associated SitePackageAssociation objects.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}
        org = factories.Organization()
        site = factories.Dataset(type="site", name="my-site")
        dataset_one = factories.Dataset(name="dataset-one", owner_org=org["id"])
        dataset_two = factories.Dataset(name="dataset-two", owner_org=org["id"])

        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=dataset_one["id"],
            site_id=site["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=dataset_two["id"],
            site_id=site["id"],
            organization_id=org["id"]
        )

        assert model.Session.query(SitePackageAssociation).count() == 2

        # purge the first package, should also delete the
        # SitePackageAssociation associated with it.
        pkg = model.Session.query(model.Package).get(dataset_one["id"])
        pkg.purge()
        model.repo.commit_and_remove()

        assert model.Session.query(SitePackageAssociation).count() == 1


@pytest.mark.usefixtures("clean_db")
class TestDeleteSitePackageAssociation(object):
    def test_association_delete_no_args(self):
        """
        Calling sc/pkg association delete with no args raises ValidationError.
        """
        sysadmin = factories.User(sysadmin=True)
        context = {"user": sysadmin["name"]}
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_site_package_association_delete", context=context,
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
                "ckanext_site_package_association_delete",
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
        site_id = factories.Dataset(type="site")["id"]

        context = {"user": sysadmin["name"]}
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package_id,
            site_id=site_id,
            organization_id=organization_id
        )

        # One association object created
        assert model.Session.query(SitePackageAssociation).count() == 1

        helpers.call_action(
            "ckanext_site_package_association_delete",
            context=context,
            package_id=package_id,
            site_id=site_id,
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
        site_id = factories.Dataset(type="site")["id"]

        # No existing associations
        assert model.Session.query(SitePackageAssociation).count() == 0

        context = {"user": sysadmin["name"]}
        with pytest.raises(toolkit.ObjectNotFound):
            helpers.call_action(
                "ckanext_site_package_association_delete",
                context=context,
                package_id=package_id,
                site_id=site_id,
                organization_id=organization_id
            )

    def test_association_delete_attempt_with_bad_package_ids(self):
        """
        Attempting to delete an association by passing non-existent package
        ids will cause a ValidationError.
        """
        sysadmin = factories.User(sysadmin=True)

        # No existing associations
        assert model.Session.query(SitePackageAssociation).count() == 0

        context = {"user": sysadmin["name"]}
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_site_package_association_delete",
                context=context,
                package_id="my-bad-package-id",
                site_id="my-bad-site-id",
                organization_id="my-bad-organization-id"
            )

    def test_association_delete_retains_packages(self):
        """
        Deleting a sc/pkg association doesn't delete the associated packages.
        """
        sysadmin = factories.User(sysadmin=True)
        organization_id = factories.Organization()["id"]
        package_id = factories.Dataset(owner_org=organization_id)["id"]
        site_id = factories.Dataset(type="site")["id"]

        context = {"user": sysadmin["name"]}
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package_id,
            site_id=site_id,
            organization_id=organization_id
        )

        helpers.call_action(
            "ckanext_site_package_association_delete",
            context=context,
            package_id=package_id,
            site_id=site_id,
        )

        # package still exist
        assert (
            model.Session.query(Package)
            .filter(Package.type == "dataset")
            .count()
            == 1
        )

        # site still exist
        assert (
            model.Session.query(Package)
            .filter(Package.type == "site")
            .count()
            == 1
        )


@pytest.mark.usefixtures("clean_db")
class TestRemoveSiteAdmin(object):
    def test_site_admin_remove_deletes_site_admin_user(self):
        """
        Calling ckanext_site_admin_remove deletes SiteAdmin object.
        """
        user = factories.User()

        helpers.call_action(
            "ckanext_site_admin_add", context={}, username=user["name"]
        )

        # There's a SiteAdmin obj
        assert model.Session.query(SiteAdmin).count() == 1

        helpers.call_action(
            "ckanext_site_admin_remove", context={}, username=user["name"]
        )

        # There's no SiteAdmin obj
        assert model.Session.query(SiteAdmin).count() == 0
        assert SiteAdmin.get_site_admin_ids() == []

    def test_site_admin_delete_user_removes_site_admin_object(self):
        """
        Deleting a user also deletes the corresponding SiteAdmin object.
        """
        user = factories.User()

        helpers.call_action(
            "ckanext_site_admin_add", context={}, username=user["name"]
        )

        # There's a SiteAdmin object
        assert model.Session.query(SiteAdmin).count() == 1
        assert user["id"] in SiteAdmin.get_site_admin_ids()

        # purge the user, should also delete the SiteAdmin object
        # associated with it.
        user_obj = model.Session.query(model.User).get(user["id"])
        user_obj.purge()
        model.repo.commit_and_remove()

        # The SiteAdmin has also been removed
        assert model.Session.query(SiteAdmin).count() == 0
        assert SiteAdmin.get_site_admin_ids() == []

    def test_site_admin_remove_retains_user(self):
        """
        Deleting a SiteAdmin object doesn't delete the corresponding user.
        """

        user = factories.User()

        helpers.call_action(
            "ckanext_site_admin_add", context={}, username=user["name"]
        )

        # We have a user
        user_obj = model.Session.query(model.User).get(user["id"])
        assert user_obj is not None

        helpers.call_action(
            "ckanext_site_admin_remove", context={}, username=user["name"]
        )

        # We still have a user
        user_obj = model.Session.query(model.User).get(user["id"])
        assert user_obj is not None

    def test_site_admin_remove_with_bad_username(self):
        """
        Calling site admin remove with a non-existent user raises
        ValidationError.
        """

        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_site_admin_remove",
                context={},
                username="no-one-here",
            )

    def test_site_admin_remove_with_no_args(self):
        """
        Calling site admin remove with no arg raises ValidationError.
        """

        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_site_admin_remove", context={},
            )
