import pytest

from ckan.model.package import Package
import ckan.model as model
import ckan.plugins.toolkit as toolkit

from ckan.tests import factories, helpers


from ckanext.extension.model import ExtensionPackageAssociation, ExtensionAdmin


@pytest.mark.usefixtures("clean_db", "extension_setup", "clean_session")
class TestCreateExtension(object):
    def test_extension_create_no_args(self):
        """
        Calling extension create without args raises ValidationError.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}

        # no extensions exist.
        assert (
            model.Session.query(Package)
            .filter(Package.type == "extension")
            .count()
            == 0
        )

        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_extension_create", context=context,
            )

        # no extensions (dataset of type 'extension') created.
        assert (
            model.Session.query(Package)
            .filter(Package.type == "extension")
            .count()
            == 0
        )

    def test_extension_create_with_name_arg(self):
        """
        Calling extension create with a name arg creates a extension package.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}

        # no extensions exist.
        assert (
            model.Session.query(Package)
            .filter(Package.type == "extension")
            .count()
            == 0
        )

        helpers.call_action(
            "ckanext_extension_create", context=context, name="my-extension"
        )

        # a extensions (dataset of type 'extension') created.
        assert (
            model.Session.query(Package)
            .filter(Package.type == "extension")
            .count()
            == 1
        )

    def test_extension_create_with_existing_name(self):
        """
        Calling extension create with an existing name raises ValidationError.
        """
        sysadmin = factories.Sysadmin()
        context = {"user": sysadmin["name"]}
        factories.Dataset(type="extension", name="my-extension")

        # a single extensions exist.
        assert (
            model.Session.query(Package)
            .filter(Package.type == "extension")
            .count()
            == 1
        )

        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_extension_create", context=context, name="my-extension",
            )

        # still only one extension exists.
        assert (
            model.Session.query(Package)
            .filter(Package.type == "extension")
            .count()
            == 1
        )


@pytest.mark.usefixtures("clean_db", "extension_setup", "clean_session")
class TestCreateExtensionPackageAssociation(object):
    def test_association_create_no_args(self):
        """
        Calling sc/pkg association create with no args raises
        ValidationError.
        """
        sysadmin = factories.User(sysadmin=True)
        context = {"user": sysadmin["name"]}
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_extension_package_association_create", context=context,
            )

        assert model.Session.query(ExtensionPackageAssociation).count() == 0

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
                "ckanext_extension_package_association_create",
                context=context,
                package_id=package_id,
            )

        assert model.Session.query(ExtensionPackageAssociation).count() == 0

    def test_association_create_by_id(self):
        """
        Calling sc/pkg association create with correct args (package ids)
        creates an association.
        """
        sysadmin = factories.User(sysadmin=True)
        organization_id = factories.Organization()["id"]
        package_id = factories.Dataset(owner_org=organization_id)["id"]
        extension_id = factories.Dataset(type="extension")["id"]

        context = {"user": sysadmin["name"]}
        association_dict = helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package_id,
            extension_id=extension_id,
            organization_id=organization_id
        )

        # One association object created
        assert model.Session.query(ExtensionPackageAssociation).count() == 1
        # Association properties are correct
        assert association_dict.get("extension_id") == extension_id
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
        extension = factories.Dataset(type="extension")
        extension_name = extension["name"]

        context = {"user": sysadmin["name"]}
        association_dict = helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package_name,
            extension_id=extension_name,
            organization_id=org["id"]
        )

        assert model.Session.query(ExtensionPackageAssociation).count() == 1
        assert association_dict.get("extension_id") == extension["id"]
        assert association_dict.get("package_id") == package["id"]

    def test_association_create_existing(self):
        """
        Attempt to create association with existing details returns Validation
        Error.
        """
        sysadmin = factories.User(sysadmin=True)
        organization_id = factories.Organization()["id"]
        package_id = factories.Dataset(owner_org=organization_id)["id"]
        extension_id = factories.Dataset(type="extension")["id"]

        context = {"user": sysadmin["name"]}
        # Create association
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=package_id,
            extension_id=extension_id,
            organization_id=organization_id
        )
        # Attempted duplicate creation results in ValidationError
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_extension_package_association_create",
                context=context,
                package_id=package_id,
                extension_id=extension_id,
                organization_id=organization_id
            )


@pytest.mark.usefixtures("clean_db", "extension_setup", "clean_session")
class TestCreateExtensionAdmin(object):
    def test_extension_admin_add_creates_extension_admin_user(self):
        """
        Calling ckanext_extension_admin_add adds user to extension admin list.
        """
        user_to_add = factories.User()

        assert model.Session.query(ExtensionAdmin).count() == 0

        helpers.call_action(
            "ckanext_extension_admin_add",
            context={},
            username=user_to_add["name"],
        )

        assert model.Session.query(ExtensionAdmin).count() == 1
        assert user_to_add["id"] in ExtensionAdmin.get_extension_admin_ids()

    def test_extension_admin_add_multiple_users(self):
        """
        Calling ckanext_extension_admin_add for multiple users correctly adds
        them to extension admin list.
        """
        user_to_add = factories.User()
        second_user_to_add = factories.User()

        assert model.Session.query(ExtensionAdmin).count() == 0

        helpers.call_action(
            "ckanext_extension_admin_add",
            context={},
            username=user_to_add["name"],
        )

        helpers.call_action(
            "ckanext_extension_admin_add",
            context={},
            username=second_user_to_add["name"],
        )

        assert model.Session.query(ExtensionAdmin).count() == 2
        assert user_to_add["id"] in ExtensionAdmin.get_extension_admin_ids()
        assert (
            second_user_to_add["id"] in ExtensionAdmin.get_extension_admin_ids()
        )

    def test_extension_admin_add_existing_user(self):
        """
        Calling ckanext_extension_admin_add twice for same user raises a
        ValidationError.
        """
        user_to_add = factories.User()

        # Add once
        helpers.call_action(
            "ckanext_extension_admin_add",
            context={},
            username=user_to_add["name"],
        )

        assert model.Session.query(ExtensionAdmin).count() == 1

        # Attempt second add
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_extension_admin_add",
                context={},
                username=user_to_add["name"],
            )

        # Still only one ExtensionAdmin object.
        assert model.Session.query(ExtensionAdmin).count() == 1

    def test_extension_admin_add_username_doesnot_exist(self):
        """
        Calling ckanext_extension_admin_add with non-existent username raises
        ValidationError and no ExtensionAdmin object is created.
        """
        with pytest.raises(toolkit.ObjectNotFound):
            helpers.call_action(
                "ckanext_extension_admin_add", context={}, username="missing",
            )

        assert model.Session.query(ExtensionAdmin).count() == 0
        assert ExtensionAdmin.get_extension_admin_ids() == []

    def test_extension_admin_add_no_args(self):
        """
        Calling ckanext_extension_admin_add with no args raises ValidationError
        and no ExtensionAdmin object is created.
        """
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                "ckanext_extension_admin_add", context={},
            )

        assert model.Session.query(ExtensionAdmin).count() == 0
        assert ExtensionAdmin.get_extension_admin_ids() == []
