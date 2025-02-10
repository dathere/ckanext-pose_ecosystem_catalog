import pytest

from ckan.model.package import Package
import ckan.model as model
import ckan.plugins.toolkit as toolkit

from ckan.tests import factories, helpers


from ckanext.site.model import SitePackageAssociation, SiteAdmin


@pytest.mark.usefixtures("clean_db", "site_setup", "clean_session")
class TestCreateSite(object):
    def test_site_create_no_args(self):
        """
        Calling site create without args raises ValidationError.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}

        # no sites exist.
        assert (
            model.Session.query(Package)
            .filter(Package.type == "site")
            .count()
            == 0
        )

        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_site_create", context=context,
            )

        # no sites (dataset of type 'site') created.
        assert (
            model.Session.query(Package)
            .filter(Package.type == "site")
            .count()
            == 0
        )

    def test_site_create_with_name_arg(self):
        """
        Calling site create with a name arg creates a site package.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}

        # no sites exist.
        assert (
            model.Session.query(Package)
            .filter(Package.type == "site")
            .count()
            == 0
        )

        helpers.call_action(
            "ckanext_site_create", context=context, name="my-site"
        )

        # a sites (dataset of type 'site') created.
        assert (
            model.Session.query(Package)
            .filter(Package.type == "site")
            .count()
            == 1
        )

    def test_site_create_with_existing_name(self):
        """
        Calling site create with an existing name raises ValidationError.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}
        factories.Dataset(type="site", name="my-site")

        # a single sites exist.
        assert (
            model.Session.query(Package)
            .filter(Package.type == "site")
            .count()
            == 1
        )

        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_site_create", context=context, name="my-site",
            )

        # still only one site exists.
        assert (
            model.Session.query(Package)
            .filter(Package.type == "site")
            .count()
            == 1
        )


@pytest.mark.usefixtures("clean_db", "site_setup", "clean_session")
class TestCreateSitePackageAssociation(object):
    def test_association_create_no_args(self):
        """
        Calling sc/pkg association create with no args raises
        ValidationError.
        """
        sysadmin = factories.User(sysadmin=True)
        context = {"user": sysadmin["name"]}
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_site_package_association_create", context=context,
            )

        assert model.Session.query(SitePackageAssociation).count() == 0

    def test_association_create_missing_arg(self):
        """
        Calling sc/pkg association create with a missing arg raises
        ValidationError.
        """
        sysadmin = factories.User(sysadmin=True)
        package_id = factories.Dataset()["id"]

        context = {"user": sysadmin["name"]}
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_site_package_association_create",
                context=context,
                package_id=package_id,
            )

        assert model.Session.query(SitePackageAssociation).count() == 0

    def test_association_create_by_id(self):
        """
        Calling sc/pkg association create with correct args (package ids)
        creates an association.
        """
        sysadmin = factories.User(sysadmin=True)
        organization_id = factories.Organization()["id"]
        package_id = factories.Dataset(owner_org=organization_id)["id"]
        site_id = factories.Dataset(type="site")["id"]

        context = {"user": sysadmin["name"]}
        association_dict = helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package_id,
            site_id=site_id,
            organization_id=organization_id
        )

        # One association object created
        assert model.Session.query(SitePackageAssociation).count() == 1
        # Association properties are correct
        assert association_dict.get("site_id") == site_id
        assert association_dict.get("package_id") == package_id

    def test_association_create_by_name(self):
        """
        Calling sc/pkg association create with correct args (package names)
        creates an association.
        """
        sysadmin = factories.User(sysadmin=True)
        org = factories.Organization()
        package = factories.Dataset(owner_org=org["id"])
        package_name = package["name"]
        site = factories.Dataset(type="site")
        site_name = site["name"]

        context = {"user": sysadmin["name"]}
        association_dict = helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package_name,
            site_id=site_name,
            organization_id=org["id"]
        )

        assert model.Session.query(SitePackageAssociation).count() == 1
        assert association_dict.get("site_id") == site["id"]
        assert association_dict.get("package_id") == package["id"]

    def test_association_create_existing(self):
        """
        Attempt to create association with existing details returns Validation
        Error.
        """
        sysadmin = factories.User(sysadmin=True)
        organization_id = factories.Organization()["id"]
        package_id = factories.Dataset(owner_org=organization_id)["id"]
        site_id = factories.Dataset(type="site")["id"]

        context = {"user": sysadmin["name"]}
        # Create association
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=package_id,
            site_id=site_id,
            organization_id=organization_id
        )
        # Attempted duplicate creation results in ValidationError
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_site_package_association_create",
                context=context,
                package_id=package_id,
                site_id=site_id,
                organization_id=organization_id
            )


@pytest.mark.usefixtures("clean_db", "site_setup", "clean_session")
class TestCreateSiteAdmin(object):
    def test_site_admin_add_creates_site_admin_user(self):
        """
        Calling ckanext_site_admin_add adds user to site admin list.
        """
        user_to_add = factories.User()

        assert model.Session.query(SiteAdmin).count() == 0

        helpers.call_action(
            "ckanext_site_admin_add",
            context={},
            username=user_to_add["name"],
        )

        assert model.Session.query(SiteAdmin).count() == 1
        assert user_to_add["id"] in SiteAdmin.get_site_admin_ids()

    def test_site_admin_add_multiple_users(self):
        """
        Calling ckanext_site_admin_add for multiple users correctly adds
        them to site admin list.
        """
        user_to_add = factories.User()
        second_user_to_add = factories.User()

        assert model.Session.query(SiteAdmin).count() == 0

        helpers.call_action(
            "ckanext_site_admin_add",
            context={},
            username=user_to_add["name"],
        )

        helpers.call_action(
            "ckanext_site_admin_add",
            context={},
            username=second_user_to_add["name"],
        )

        assert model.Session.query(SiteAdmin).count() == 2
        assert user_to_add["id"] in SiteAdmin.get_site_admin_ids()
        assert (
            second_user_to_add["id"] in SiteAdmin.get_site_admin_ids()
        )

    def test_site_admin_add_existing_user(self):
        """
        Calling ckanext_site_admin_add twice for same user raises a
        ValidationError.
        """
        user_to_add = factories.User()

        # Add once
        helpers.call_action(
            "ckanext_site_admin_add",
            context={},
            username=user_to_add["name"],
        )

        assert model.Session.query(SiteAdmin).count() == 1

        # Attempt second add
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_site_admin_add",
                context={},
                username=user_to_add["name"],
            )

        # Still only one SiteAdmin object.
        assert model.Session.query(SiteAdmin).count() == 1

    def test_site_admin_add_username_doesnot_exist(self):
        """
        Calling ckanext_site_admin_add with non-existent username raises
        ValidationError and no SiteAdmin object is created.
        """
        with pytest.raises(toolkit.ObjectNotFound):
            helpers.call_action(
                "ckanext_site_admin_add", context={}, username="missing",
            )

        assert model.Session.query(SiteAdmin).count() == 0
        assert SiteAdmin.get_site_admin_ids() == []

    def test_site_admin_add_no_args(self):
        """
        Calling ckanext_site_admin_add with no args raises ValidationError
        and no SiteAdmin object is created.
        """
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_site_admin_add", context={},
            )

        assert model.Session.query(SiteAdmin).count() == 0
        assert SiteAdmin.get_site_admin_ids() == []
