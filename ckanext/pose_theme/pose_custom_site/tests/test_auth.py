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
class TestSiteAuthIndex(object):
    def test_auth_anon_user_can_view_site_index(self, app):
        """An anon (not logged in) user can view the Sites index."""

        app.get("/site", status=200)

    def test_auth_logged_in_user_can_view_site_index(self, app):
        """
        A logged in user can view the Site index.
        """

        user = factories.User()

        app.get(
            "/site",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_anon_user_cant_see_add_site_button(self, app):
        """
        An anon (not logged in) user can't see the Add Site button on the
        site index page.
        """

        response = app.get("/site", status=200)

        # test for new site link in response
        assert "/site/new" not in response.body

    def test_auth_logged_in_user_cant_see_add_site_button(self, app):
        """
        A logged in user can't see the Add Site button on the site
        index page.
        """

        user = factories.User()

        response = app.get(
            "/site",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        # test for new site link in response
        assert "/site/new" not in response.body

    def test_auth_sysadmin_can_see_add_site_button(self, app):
        """
        A sysadmin can see the Add Site button on the site index
        page.
        """

        user = factories.Sysadmin()

        response = app.get(
            "/site",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        # test for new site link in response
        assert "/site/new" in response.body


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSiteAuthDetails(object):
    def test_auth_anon_user_can_view_site_details(self, app):
        """
        An anon (not logged in) user can view an individual Site details page.
        """

        factories.Dataset(type="site", name="my-site")

        app.get("/site/my-site", status=200)

    def test_auth_logged_in_user_can_view_site_details(self, app):
        """
        A logged in user can view an individual Site details page.
        """

        user = factories.User()

        factories.Dataset(type="site", name="my-site")

        app.get(
            "/site/my-site",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_anon_user_cant_see_manage_button(self, app):
        """
        An anon (not logged in) user can't see the Manage button on an individual
        site details page.
        """

        factories.Dataset(type="site", name="my-site")

        response = app.get("/site/my-site", status=200)

        assert "/site/edit/my-site" not in response.body

    def test_auth_logged_in_user_can_see_manage_button(self, app):
        """
        A logged in user can't see the Manage button on an individual site
        details page.
        """

        user = factories.User()

        factories.Dataset(type="site", name="my-site")

        response = app.get(
            "/site/my-site",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        # test for url to edit page
        assert "/site/edit/my-site" not in response.body

    def test_auth_sysadmin_can_see_manage_button(self, app):
        """
        A sysadmin can see the Manage button on an individual site details
        page.
        """

        user = factories.Sysadmin()

        factories.Dataset(type="site", name="my-site")

        response = app.get(
            "/site/my-site",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        # test for url to edit page
        assert "/site/edit/my-site" in response.body

    def test_auth_site_show_anon_can_access(self, app):
        """
        Anon user can request site show.
        """

        factories.Dataset(type="site", name="my-site")

        response = app.get(
            "/api/3/action/ckanext_site_show?id=my-site", status=200
        )

        json_response = json.loads(response.body)

        assert json_response["success"]

    def test_auth_site_show_normal_user_can_access(self, app):
        """
        Normal logged in user can request site show.
        """
        user = factories.User()

        factories.Dataset(type="site", name="my-site")

        response = app.get(
            "/api/3/action/ckanext_site_show?id=my-site",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        json_response = json.loads(response.body)

        assert json_response["success"]

    def test_auth_site_show_sysadmin_can_access(self, app):
        """
        Normal logged in user can request site show.
        """
        user = factories.Sysadmin()

        factories.Dataset(type="site", name="my-site")

        response = app.get(
            "/api/3/action/ckanext_site_show?id=my-site",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        json_response = json.loads(response.body)

        assert json_response["success"]


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSiteAuthCreate(object):
    def test_auth_anon_user_cant_view_create_site(self, app):
        """
        An anon (not logged in) user can't access the create site page.
        """
        if toolkit.check_ckan_version(min_version='2.10.0'):
            _get_request(app, "/site/new", status=401)
        else:
            # Remove when dropping support for 2.9
            _get_request(app, "/site/new", status=302)

    def test_auth_logged_in_user_cant_view_create_site_page(self, app):
        """
        A logged in user can't access the create site page.
        """
        user = factories.User()
        app.get(
            "/site/new",
            status=401,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_sysadmin_can_view_create_site_page(self, app):
        """
        A sysadmin can access the create site page.
        """
        user = factories.Sysadmin()
        app.get(
            "/site/new",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSiteAuthList(object):
    def test_auth_site_list_anon_can_access(self, app):
        """
        Anon user can request site list.
        """

        factories.Dataset(type="site", name="my-site")

        response = app.get("/api/3/action/ckanext_site_list", status=200)

        json_response = json.loads(response.body)

        assert json_response["success"]

    def test_auth_site_list_normal_user_can_access(self, app):
        """
        Normal logged in user can request site list.
        """
        user = factories.User()

        factories.Dataset(type="site", name="my-site")

        response = app.get(
            "/api/3/action/ckanext_site_list",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        json_response = json.loads(response.body)

        assert json_response["success"]

    def test_auth_site_list_sysadmin_can_access(self, app):
        """
        Normal logged in user can request site list.
        """
        user = factories.Sysadmin()

        factories.Dataset(type="site", name="my-site")

        response = app.get(
            "/api/3/action/ckanext_site_list",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        json_response = json.loads(response.body)

        assert json_response["success"]


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSiteAuthEdit(object):
    def test_auth_anon_user_cant_view_edit_site_page(self, app):
        """
        An anon (not logged in) user can't access the site edit page.
        """
        factories.Dataset(type="site", name="my-site")
        if toolkit.check_ckan_version(min_version='2.10.0'):
            _get_request(app, "/site/edit/my-site", status=401)
        else:
            # Remove when dropping support for 2.9
            _get_request(app, "/site/edit/my-site", status=302)

    def test_auth_logged_in_user_cant_view_edit_site_page(self, app):
        """
        A logged in user can't access the site edit page.
        """

        user = factories.User()

        factories.Dataset(type="site", name="my-site")

        app.get(
            "/site/edit/my-site",
            status=401,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_sysadmin_can_view_edit_site_page(self, app):
        """
        A sysadmin can access the site edit page.
        """

        user = factories.Sysadmin()

        factories.Dataset(type="site", name="my-site")

        app.get(
            "/site/edit/my-site",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_site_admin_can_view_edit_site_page(self, app):
        """
        A site admin can access the site edit page.
        """

        user = factories.User()

        # Make user a site admin
        helpers.call_action(
            "ckanext_site_admin_add", context={}, username=user["name"]
        )

        factories.Dataset(type="site", name="my-site")

        app.get(
            "/site/edit/my-site",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_anon_user_cant_view_manage_datasets(self, app):
        """
        An anon (not logged in) user can't access the site manage datasets page.
        """

        factories.Dataset(type="site", name="my-site")
        if toolkit.check_ckan_version(min_version='2.10.0'):
            _get_request(app, "/site/manage_datasets/my-site", status=401)
        else:
            # Remove when dropping support for 2.9
            _get_request(app, "/site/manage_datasets/my-site", status=302)

    def test_auth_logged_in_user_cant_view_manage_datasets(self, app):
        """
        A logged in user (not sysadmin) can't access the site manage datasets page.
        """

        user = factories.User()

        factories.Dataset(type="site", name="my-site")

        app.get(
            "/site/manage_datasets/my-site",
            status=401,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_sysadmin_can_view_manage_datasets(self, app):
        """
        A sysadmin can access the site manage datasets page.
        """

        user = factories.Sysadmin()

        factories.Dataset(type="site", name="my-site")

        app.get(
            "/site/manage_datasets/my-site",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_site_admin_can_view_manage_datasets(self, app):
        """
        A site admin can access the site manage datasets page.
        """

        user = factories.User()

        # Make user a site admin
        helpers.call_action(
            "ckanext_site_admin_add", context={}, username=user["name"]
        )

        factories.Dataset(type="site", name="my-site")

        app.get(
            "/site/manage_datasets/my-site",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_anon_user_cant_view_delete_site_page(self, app):
        """
        An anon (not logged in) user can't access the site delete page.
        """

        factories.Dataset(type="site", name="my-site")
        if toolkit.check_ckan_version(min_version='2.10.0'):
            _get_request(app, "/site/delete/my-site", status=401)
        else:
            # Remove when dropping support for 2.9
            _get_request(app, "/site/delete/my-site", status=302)

    def test_auth_logged_in_user_cant_view_delete_site_page(self, app):
        """
        A logged in user can't access the site delete page.
        """

        user = factories.User()

        factories.Dataset(type="site", name="my-site")

        app.get(
            "/site/delete/my-site",
            status=401,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_sysadmin_can_view_delete_site_page(self, app):
        """
        A sysadmin can access the site delete page.
        """

        user = factories.Sysadmin()

        factories.Dataset(type="site", name="my-site")

        app.get(
            "/site/delete/my-site",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_site_admin_can_view_delete_site_page(self, app):
        """
        A site admin can access the site delete page.
        """

        user = factories.User()

        # Make user a site admin
        helpers.call_action(
            "ckanext_site_admin_add", context={}, username=user["name"]
        )

        factories.Dataset(type="site", name="my-site")

        app.get(
            "/site/delete/my-site",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_anon_user_cant_view_addtosite_dropdown_dataset_site_list(
        self, app
    ):
        """
        An anonymous user can't view the 'Add to site' dropdown selector
        from a datasets site list page.
        """

        factories.Dataset(name="my-site", type="site")
        factories.Dataset(name="my-dataset")

        site_list_response = app.get(
            "/dataset/sites/my-dataset", status=200
        )

        assert "site-add" not in site_list_response.body

    def test_auth_normal_user_cant_view_addtosite_dropdown_dataset_site_list(
        self, app
    ):
        """
        A normal (logged in) user can't view the 'Add to site' dropdown
        selector from a datasets site list page.
        """
        user = factories.User()

        factories.Dataset(name="my-site", type="site")
        factories.Dataset(name="my-dataset")

        site_list_response = app.get(
            "/dataset/sites/my-dataset",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        assert "site-add" not in site_list_response.body

    def test_auth_sysadmin_can_view_addtosite_dropdown_dataset_site_list(
        self, app
    ):
        """
        A sysadmin can view the 'Add to site' dropdown selector from a
        datasets site list page.
        """
        user = factories.Sysadmin()

        factories.Dataset(name="my-site", type="site")
        factories.Dataset(name="my-dataset")

        site_list_response = app.get(
            "/dataset/sites/my-dataset",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        assert "site-add" in site_list_response.body

    def test_auth_site_admin_can_view_addtosite_dropdown_dataset_site_list(
        self, app
    ):
        """
        A site admin can view the 'Add to site' dropdown selector from
        a datasets site list page.
        """

        user = factories.User()

        # Make user a site admin
        helpers.call_action(
            "ckanext_site_admin_add", context={}, username=user["name"]
        )

        factories.Dataset(name="my-site", type="site")
        factories.Dataset(name="my-dataset")

        site_list_response = app.get(
            "/dataset/sites/my-dataset",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

        assert "site-add" in site_list_response.body


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSitePackageAssociationCreate(object):
    def test_site_package_association_create_no_user(self):
        """
        Calling site package association create with no user raises
        NotAuthorized.
        """

        context = {"user": None, "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_site_package_association_create", context=context,
            )

    def test_site_package_association_create_sysadmin(self):
        """
        Calling site package association create by a sysadmin doesn't
        raise NotAuthorized.
        """
        a_sysadmin = factories.Sysadmin()
        context = {"user": a_sysadmin["name"], "model": None}
        helpers.call_auth(
            "ckanext_site_package_association_create", context=context
        )

    def test_site_package_association_create_site_admin(self):
        """
        Calling site package association create by a site admin
        doesn't raise NotAuthorized.
        """
        site_admin = factories.User()

        # Make user a site admin
        helpers.call_action(
            "ckanext_site_admin_add",
            context={},
            username=site_admin["name"],
        )

        context = {"user": site_admin["name"], "model": None}
        helpers.call_auth(
            "ckanext_site_package_association_create", context=context
        )

    def test_site_package_association_create_unauthorized_creds(self):
        """
        Calling site package association create with unauthorized user
        raises NotAuthorized.
        """
        not_a_sysadmin = factories.User()
        context = {"user": not_a_sysadmin["name"], "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_site_package_association_create", context=context,
            )


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSitePackageAssociationDelete(object):
    def test_site_package_association_delete_no_user(self):
        """
        Calling site package association create with no user raises
        NotAuthorized.
        """

        context = {"user": None, "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_site_package_association_delete", context=context,
            )

    def test_site_package_association_delete_sysadmin(self):
        """
        Calling site package association create by a sysadmin doesn't
        raise NotAuthorized.
        """
        a_sysadmin = factories.Sysadmin()
        context = {"user": a_sysadmin["name"], "model": None}
        helpers.call_auth(
            "ckanext_site_package_association_delete", context=context
        )

    def test_site_package_association_delete_site_admin(self):
        """
        Calling site package association create by a site admin
        doesn't raise NotAuthorized.
        """
        site_admin = factories.User()

        # Make user a site admin
        helpers.call_action(
            "ckanext_site_admin_add",
            context={},
            username=site_admin["name"],
        )

        context = {"user": site_admin["name"], "model": None}
        helpers.call_auth(
            "ckanext_site_package_association_delete", context=context
        )

    def test_site_package_association_delete_unauthorized_creds(self):
        """
        Calling site package association create with unauthorized user
        raises NotAuthorized.
        """
        not_a_sysadmin = factories.User()
        context = {"user": not_a_sysadmin["name"], "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_site_package_association_delete", context=context,
            )


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSiteAdminAddAuth(object):
    def test_site_admin_add_no_user(self):
        """
        Calling site admin add with no user raises NotAuthorized.
        """

        context = {"user": None, "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_site_admin_add", context=context,
            )

    def test_site_admin_add_correct_creds(self):
        """
        Calling site admin add by a sysadmin doesn't raise
        NotAuthorized.
        """
        a_sysadmin = factories.Sysadmin()
        context = {"user": a_sysadmin["name"], "model": None}
        helpers.call_auth("ckanext_site_admin_add", context=context)

    def test_site_admin_add_unauthorized_creds(self):
        """
        Calling site admin add with unauthorized user raises
        NotAuthorized.
        """
        not_a_sysadmin = factories.User()
        context = {"user": not_a_sysadmin["name"], "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_site_admin_add", context=context,
            )


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSiteAdminRemoveAuth(object):
    def test_site_admin_remove_no_user(self):
        """
        Calling site admin remove with no user raises NotAuthorized.
        """

        context = {"user": None, "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_site_admin_remove", context=context,
            )

    def test_site_admin_remove_correct_creds(self):
        """
        Calling site admin remove by a sysadmin doesn't raise
        NotAuthorized.
        """
        a_sysadmin = factories.Sysadmin()
        context = {"user": a_sysadmin["name"], "model": None}
        helpers.call_auth("ckanext_site_admin_remove", context=context)

    def test_site_admin_remove_unauthorized_creds(self):
        """
        Calling site admin remove with unauthorized user raises
        NotAuthorized.
        """
        not_a_sysadmin = factories.User()
        context = {"user": not_a_sysadmin["name"], "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_site_admin_remove", context=context,
            )


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSiteAdminListAuth(object):
    def test_site_admin_list_no_user(self):
        """
        Calling site admin list with no user raises NotAuthorized.
        """

        context = {"user": None, "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_site_admin_list", context=context,
            )

    def test_site_admin_list_correct_creds(self):
        """
        Calling site admin list by a sysadmin doesn't raise
        NotAuthorized.
        """
        a_sysadmin = factories.Sysadmin()
        context = {"user": a_sysadmin["name"], "model": None}
        helpers.call_auth("ckanext_site_admin_list", context=context)

    def test_site_admin_list_unauthorized_creds(self):
        """
        Calling site admin list with unauthorized user raises
        NotAuthorized.
        """
        not_a_sysadmin = factories.User()
        context = {"user": not_a_sysadmin["name"], "model": None}
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth(
                "ckanext_site_admin_list", context=context,
            )


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSiteAuthManageSiteAdmins(object):
    def test_auth_anon_user_cant_view_site_admin_manage_page(self, app):
        """
        An anon (not logged in) user can't access the manage site admin
        page.
        """
        if toolkit.check_ckan_version(min_version='2.10.0'):
            _get_request(app, "/site/new", status=401)
        else:
            # Remove when dropping support for 2.9
            _get_request(app, "/site/new", status=302)

    def test_auth_logged_in_user_cant_view_site_admin_manage_page(
        self, app
    ):
        """
        A logged in user can't access the manage site admin page.
        """

        user = factories.User()
        app.get(
            "/site/new",
            status=401,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )

    def test_auth_sysadmin_can_view_site_admin_manage_page(self, app):
        """
        A sysadmin can access the manage site admin page.
        """

        user = factories.Sysadmin()
        app.get(
            "/site/new",
            status=200,
            extra_environ={"REMOTE_USER": str(user["name"])},
        )
