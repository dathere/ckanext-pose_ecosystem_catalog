import pytest
import json

import ckan.plugins.toolkit as toolkit

from ckan.tests import factories, helpers


def _get_request(app, url, status):
    ''' Wrapper around app.get() for compatibility between CKAN versions.

    CKAN 2.9's app.get() forces a redirect and 2.8's doesn't. Also
    follow_redirects parameter is not supported in CKAN 2.8.

    Can be removed when CKAN 2.8 is no longer supported.
    '''
    try:
        # CKAN 2.9
        app.get(url, status=status, follow_redirects=False)
    except TypeError:
        # CKAN 2.8
        app.get(url, status=status)


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestExtensionAuthIndex(object):
    def test_auth_anon_user_can_view_extension_index(self, app):
        """An anon (not logged in) user can view the Extensions index."""

        app.get("/extension", status=200)

    def test_auth_logged_in_user_can_view_extension_index(self, app):
        """
        A logged in user can view the Extension index.
        """

        user = factories.User()

        app.get(
            "/extension",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_anon_user_cant_see_add_extension_button(self, app):
        """
        An anon (not logged in) user can't see the Add Extension button on the
        extension index page.
        """

        response = app.get("/extension", status=200)

        # test for new extension link in response
        assert "/extension/new" not in response.body

    def test_auth_logged_in_user_cant_see_add_extension_button(self, app):
        """
        A logged in user can't see the Add Extension button on the extension
        index page.
        """

        user = factories.User()

        response = app.get(
            "/extension",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        # test for new extension link in response
        assert "/extension/new" not in response.body

    def test_auth_sysadmin_can_see_add_extension_button(self, app):
        """
        A sysadmin can see the Add Extension button on the extension index
        page.
        """

        user = factories.Sysadmin()

        response = app.get(
            "/extension",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        # test for new extension link in response
        assert "/extension/new" in response.body


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestExtensionAuthDetails(object):
    def test_auth_anon_user_can_view_extension_details(self, app):
        """
        An anon (not logged in) user can view an individual Extension details page.
        """

        factories.Dataset(type="extension", name="my-extension")

        app.get("/extension/my-extension", status=200)

    def test_auth_logged_in_user_can_view_extension_details(self, app):
        """
        A logged in user can view an individual Extension details page.
        """

        user = factories.User()

        factories.Dataset(type="extension", name="my-extension")

        app.get(
            "/extension/my-extension",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_anon_user_cant_see_manage_button(self, app):
        """
        An anon (not logged in) user can't see the Manage button on an individual
        extension details page.
        """

        factories.Dataset(type="extension", name="my-extension")

        response = app.get("/extension/my-extension", status=200)

        assert "/extension/edit/my-extension" not in response.body

    def test_auth_logged_in_user_can_see_manage_button(self, app):
        """
        A logged in user can't see the Manage button on an individual extension
        details page.
        """

        user = factories.User()

        factories.Dataset(type="extension", name="my-extension")

        response = app.get(
            "/extension/my-extension",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        # test for url to edit page
        assert "/extension/edit/my-extension" not in response.body

    def test_auth_sysadmin_can_see_manage_button(self, app):
        """
        A sysadmin can see the Manage button on an individual extension details
        page.
        """

        user = factories.Sysadmin()

        factories.Dataset(type="extension", name="my-extension")

        response = app.get(
            "/extension/my-extension",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        # test for url to edit page
        assert "/extension/edit/my-extension" in response.body

    def test_auth_extension_show_anon_can_access(self, app):
        """
        Anon user can request extension show.
        """

        factories.Dataset(type="extension", name="my-extension")

        response = app.get(
            "/api/3/action/ckanext_extension_show?id=my-extension", status=200
        )

        json_response = json.loads(response.body)

        assert json_response["success"]

    def test_auth_extension_show_normal_user_can_access(self, app):
        """
        Normal logged in user can request extension show.
        """
        user = factories.User()

        factories.Dataset(type="extension", name="my-extension")

        response = app.get(
            "/api/3/action/ckanext_extension_show?id=my-extension",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        json_response = json.loads(response.body)

        assert json_response["success"]

    def test_auth_extension_show_sysadmin_can_access(self, app):
        """
        Normal logged in user can request extension show.
        """
        user = factories.Sysadmin()

        factories.Dataset(type="extension", name="my-extension")

        response = app.get(
            "/api/3/action/ckanext_extension_show?id=my-extension",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        json_response = json.loads(response.body)

        assert json_response["success"]


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestExtensionAuthCreate(object):
    def test_auth_anon_user_cant_view_create_extension(self, app):
        """
        An anon (not logged in) user can't access the create extension page.
        """
        if toolkit.check_ckan_version(min_version='2.10.0'):
            _get_request(app, "/extension/new", status=401)
        else:
            # Remove when dropping support for 2.9
            _get_request(app, "/extension/new", status=302)

    def test_auth_logged_in_user_cant_view_create_extension_page(self, app):
        """
        A logged in user can't access the create extension page.
        """
        user = factories.User()
        app.get(
            "/extension/new",
            status=401,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_sysadmin_can_view_create_extension_page(self, app):
        """
        A sysadmin can access the create extension page.
        """
        user = factories.Sysadmin()
        app.get(
            "/extension/new",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestExtensionAuthList(object):
    def test_auth_extension_list_anon_can_access(self, app):
        """
        Anon user can request extension list.
        """

        factories.Dataset(type="extension", name="my-extension")

        response = app.get("/api/3/action/ckanext_extension_list", status=200)

        json_response = json.loads(response.body)

        assert json_response["success"]

    def test_auth_extension_list_normal_user_can_access(self, app):
        """
        Normal logged in user can request extension list.
        """
        user = factories.User()

        factories.Dataset(type="extension", name="my-extension")

        response = app.get(
            "/api/3/action/ckanext_extension_list",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        json_response = json.loads(response.body)

        assert json_response["success"]

    def test_auth_extension_list_sysadmin_can_access(self, app):
        """
        Normal logged in user can request extension list.
        """
        user = factories.Sysadmin()

        factories.Dataset(type="extension", name="my-extension")

        response = app.get(
            "/api/3/action/ckanext_extension_list",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        json_response = json.loads(response.body)

        assert json_response["success"]


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestExtensionAuthEdit(object):
    def test_auth_anon_user_cant_view_edit_extension_page(self, app):
        """
        An anon (not logged in) user can't access the extension edit page.
        """
        factories.Dataset(type="extension", name="my-extension")
        if toolkit.check_ckan_version(min_version='2.10.0'):
            _get_request(app, "/extension/edit/my-extension", status=401)
        else:
            # Remove when dropping support for 2.9
            _get_request(app, "/extension/edit/my-extension", status=302)

    def test_auth_logged_in_user_cant_view_edit_extension_page(self, app):
        """
        A logged in user can't access the extension edit page.
        """

        user = factories.User()

        factories.Dataset(type="extension", name="my-extension")

        app.get(
            "/extension/edit/my-extension",
            status=401,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_sysadmin_can_view_edit_extension_page(self, app):
        """
        A sysadmin can access the extension edit page.
        """

        user = factories.Sysadmin()

        factories.Dataset(type="extension", name="my-extension")

        app.get(
            "/extension/edit/my-extension",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_extension_admin_can_view_edit_extension_page(self, app):
        """
        A extension admin can access the extension edit page.
        """

        user = factories.User()

        # Make user a extension admin
        helpers.call_action(
            "ckanext_extension_admin_add", context={}, username=user["name"]
        )

        factories.Dataset(type="extension", name="my-extension")

        app.get(
            "/extension/edit/my-extension",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_anon_user_cant_view_manage_datasets(self, app):
        """
        An anon (not logged in) user can't access the extension manage datasets page.
        """

        factories.Dataset(type="extension", name="my-extension")
        if toolkit.check_ckan_version(min_version='2.10.0'):
            _get_request(app, "/extension/manage_datasets/my-extension", status=401)
        else:
            # Remove when dropping support for 2.9
            _get_request(app, "/extension/manage_datasets/my-extension", status=302)

    def test_auth_logged_in_user_cant_view_manage_datasets(self, app):
        """
        A logged in user (not sysadmin) can't access the extension manage datasets page.
        """

        user = factories.User()

        factories.Dataset(type="extension", name="my-extension")

        app.get(
            "/extension/manage_datasets/my-extension",
            status=401,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_sysadmin_can_view_manage_datasets(self, app):
        """
        A sysadmin can access the extension manage datasets page.
        """

        user = factories.Sysadmin()

        factories.Dataset(type="extension", name="my-extension")

        app.get(
            "/extension/manage_datasets/my-extension",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_extension_admin_can_view_manage_datasets(self, app):
        """
        A extension admin can access the extension manage datasets page.
        """

        user = factories.User()

        # Make user a extension admin
        helpers.call_action(
            "ckanext_extension_admin_add", context={}, username=user["name"]
        )

        factories.Dataset(type="extension", name="my-extension")

        app.get(
            "/extension/manage_datasets/my-extension",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_anon_user_cant_view_delete_extension_page(self, app):
        """
        An anon (not logged in) user can't access the extension delete page.
        """

        factories.Dataset(type="extension", name="my-extension")
        if toolkit.check_ckan_version(min_version='2.10.0'):
            _get_request(app, "/extension/delete/my-extension", status=401)
        else:
            # Remove when dropping support for 2.9
            _get_request(app, "/extension/delete/my-extension", status=302)

    def test_auth_logged_in_user_cant_view_delete_extension_page(self, app):
        """
        A logged in user can't access the extension delete page.
        """

        user = factories.User()

        factories.Dataset(type="extension", name="my-extension")

        app.get(
            "/extension/delete/my-extension",
            status=401,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_sysadmin_can_view_delete_extension_page(self, app):
        """
        A sysadmin can access the extension delete page.
        """

        user = factories.Sysadmin()

        factories.Dataset(type="extension", name="my-extension")

        app.get(
            "/extension/delete/my-extension",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_extension_admin_can_view_delete_extension_page(self, app):
        """
        A extension admin can access the extension delete page.
        """

        user = factories.User()

        # Make user a extension admin
        helpers.call_action(
            "ckanext_extension_admin_add", context={}, username=user["name"]
        )

        factories.Dataset(type="extension", name="my-extension")

        app.get(
            "/extension/delete/my-extension",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_anon_user_cant_view_addtoextension_dropdown_dataset_extension_list(
        self, app
    ):
        """
        An anonymous user can't view the 'Add to extension' dropdown selector
        from a datasets extension list page.
        """

        factories.Dataset(name="my-extension", type="extension")
        factories.Dataset(name="my-dataset")

        extension_list_response = app.get(
            "/dataset/extensions/my-dataset", status=200
        )

        assert "extension-add" not in extension_list_response.body

    def test_auth_normal_user_cant_view_addtoextension_dropdown_dataset_extension_list(
        self, app
    ):
        """
        A normal (logged in) user can't view the 'Add to extension' dropdown
        selector from a datasets extension list page.
        """
        user = factories.User()

        factories.Dataset(name="my-extension", type="extension")
        factories.Dataset(name="my-dataset")

        extension_list_response = app.get(
            "/dataset/extensions/my-dataset",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        assert "extension-add" not in extension_list_response.body

    def test_auth_sysadmin_can_view_addtoextension_dropdown_dataset_extension_list(
        self, app
    ):
        """
        A sysadmin can view the 'Add to extension' dropdown selector from a
        datasets extension list page.
        """
        user = factories.Sysadmin()

        factories.Dataset(name="my-extension", type="extension")
        factories.Dataset(name="my-dataset")

        extension_list_response = app.get(
            "/dataset/extensions/my-dataset",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        assert "extension-add" in extension_list_response.body

    def test_auth_extension_admin_can_view_addtoextension_dropdown_dataset_extension_list(
        self, app
    ):
        """
        A extension admin can view the 'Add to extension' dropdown selector from
        a datasets extension list page.
        """

        user = factories.User()

        # Make user a extension admin
        helpers.call_action(
            "ckanext_extension_admin_add", context={}, username=user["name"]
        )

        factories.Dataset(name="my-extension", type="extension")
        factories.Dataset(name="my-dataset")

        extension_list_response = app.get(
            "/dataset/extensions/my-dataset",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        assert "extension-add" in extension_list_response.body


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestExtensionPackageAssociationCreate(object):
    def test_extension_package_association_create_no_user(self):
        """
        Calling extension package association create with no user raises
        NotAuthorized.
        """

        context = {"user": None, "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_extension_package_association_create", context=context,
            )

    def test_extension_package_association_create_sysadmin(self):
        """
        Calling extension package association create by a sysadmin doesn't
        raise NotAuthorized.
        """
        a_sysadmin = factories.Sysadmin()
        context = {"user": a_sysadmin["name"], "model": None}
        helpers.call_auth(
            "ckanext_extension_package_association_create", context=context
        )

    def test_extension_package_association_create_extension_admin(self):
        """
        Calling extension package association create by a extension admin
        doesn't raise NotAuthorized.
        """
        extension_admin = factories.User()

        # Make user a extension admin
        helpers.call_action(
            "ckanext_extension_admin_add",
            context={},
            username=extension_admin["name"],
        )

        context = {"user": extension_admin["name"], "model": None}
        helpers.call_auth(
            "ckanext_extension_package_association_create", context=context
        )

    def test_extension_package_association_create_unauthorized_creds(self):
        """
        Calling extension package association create with unauthorized user
        raises NotAuthorized.
        """
        not_a_sysadmin = factories.User()
        context = {"user": not_a_sysadmin["name"], "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_extension_package_association_create", context=context,
            )


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestExtensionPackageAssociationDelete(object):
    def test_extension_package_association_delete_no_user(self):
        """
        Calling extension package association create with no user raises
        NotAuthorized.
        """

        context = {"user": None, "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_extension_package_association_delete", context=context,
            )

    def test_extension_package_association_delete_sysadmin(self):
        """
        Calling extension package association create by a sysadmin doesn't
        raise NotAuthorized.
        """
        a_sysadmin = factories.Sysadmin()
        context = {"user": a_sysadmin["name"], "model": None}
        helpers.call_auth(
            "ckanext_extension_package_association_delete", context=context
        )

    def test_extension_package_association_delete_extension_admin(self):
        """
        Calling extension package association create by a extension admin
        doesn't raise NotAuthorized.
        """
        extension_admin = factories.User()

        # Make user a extension admin
        helpers.call_action(
            "ckanext_extension_admin_add",
            context={},
            username=extension_admin["name"],
        )

        context = {"user": extension_admin["name"], "model": None}
        helpers.call_auth(
            "ckanext_extension_package_association_delete", context=context
        )

    def test_extension_package_association_delete_unauthorized_creds(self):
        """
        Calling extension package association create with unauthorized user
        raises NotAuthorized.
        """
        not_a_sysadmin = factories.User()
        context = {"user": not_a_sysadmin["name"], "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_extension_package_association_delete", context=context,
            )


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestExtensionAdminAddAuth(object):
    def test_extension_admin_add_no_user(self):
        """
        Calling extension admin add with no user raises NotAuthorized.
        """

        context = {"user": None, "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_extension_admin_add", context=context,
            )

    def test_extension_admin_add_correct_creds(self):
        """
        Calling extension admin add by a sysadmin doesn't raise
        NotAuthorized.
        """
        a_sysadmin = factories.Sysadmin()
        context = {"user": a_sysadmin["name"], "model": None}
        helpers.call_auth("ckanext_extension_admin_add", context=context)

    def test_extension_admin_add_unauthorized_creds(self):
        """
        Calling extension admin add with unauthorized user raises
        NotAuthorized.
        """
        not_a_sysadmin = factories.User()
        context = {"user": not_a_sysadmin["name"], "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_extension_admin_add", context=context,
            )


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestExtensionAdminRemoveAuth(object):
    def test_extension_admin_remove_no_user(self):
        """
        Calling extension admin remove with no user raises NotAuthorized.
        """

        context = {"user": None, "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_extension_admin_remove", context=context,
            )

    def test_extension_admin_remove_correct_creds(self):
        """
        Calling extension admin remove by a sysadmin doesn't raise
        NotAuthorized.
        """
        a_sysadmin = factories.Sysadmin()
        context = {"user": a_sysadmin["name"], "model": None}
        helpers.call_auth("ckanext_extension_admin_remove", context=context)

    def test_extension_admin_remove_unauthorized_creds(self):
        """
        Calling extension admin remove with unauthorized user raises
        NotAuthorized.
        """
        not_a_sysadmin = factories.User()
        context = {"user": not_a_sysadmin["name"], "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_extension_admin_remove", context=context,
            )


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestExtensionAdminListAuth(object):
    def test_extension_admin_list_no_user(self):
        """
        Calling extension admin list with no user raises NotAuthorized.
        """

        context = {"user": None, "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_extension_admin_list", context=context,
            )

    def test_extension_admin_list_correct_creds(self):
        """
        Calling extension admin list by a sysadmin doesn't raise
        NotAuthorized.
        """
        a_sysadmin = factories.Sysadmin()
        context = {"user": a_sysadmin["name"], "model": None}
        helpers.call_auth("ckanext_extension_admin_list", context=context)

    def test_extension_admin_list_unauthorized_creds(self):
        """
        Calling extension admin list with unauthorized user raises
        NotAuthorized.
        """
        not_a_sysadmin = factories.User()
        context = {"user": not_a_sysadmin["name"], "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_extension_admin_list", context=context,
            )


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestExtensionAuthManageExtensionAdmins(object):
    def test_auth_anon_user_cant_view_extension_admin_manage_page(self, app):
        """
        An anon (not logged in) user can't access the manage extension admin
        page.
        """
        if toolkit.check_ckan_version(min_version='2.10.0'):
            _get_request(app, "/extension/new", status=401)
        else:
            # Remove when dropping support for 2.9
            _get_request(app, "/extension/new", status=302)

    def test_auth_logged_in_user_cant_view_extension_admin_manage_page(
        self, app
    ):
        """
        A logged in user can't access the manage extension admin page.
        """

        user = factories.User()
        app.get(
            "/extension/new",
            status=401,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_sysadmin_can_view_extension_admin_manage_page(self, app):
        """
        A sysadmin can access the manage extension admin page.
        """

        user = factories.Sysadmin()
        app.get(
            "/extension/new",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )
