import pytest
from bs4 import BeautifulSoup

from ckan.lib.helpers import url_for


from ckan.plugins import toolkit as tk
import ckan.model as model

from ckan.tests import factories, helpers

from ckanext.site.model import SitePackageAssociation

import logging

log = logging.getLogger(__name__)


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSiteIndex(object):
    def test_site_listed_on_index(self, app):
        """
        An added Site will appear on the Site index page.
        """

        factories.Dataset(type="site", name="my-site")

        response = app.get("/site", status=200)
        assert "1 site found" in response.body
        assert "my-site" in response.body


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSiteNewView(object):
    def test_site_create_form_renders(self, app):

        sysadmin = factories.Sysadmin()

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(url=url_for("site_new"), extra_environ=env,)
        assert "dataset-edit" in response

    def test_site_new_redirects_to_manage_datasets(self, app):
        """Creating a new site redirects to the manage datasets form."""
        if tk.check_ckan_version("2.9"):
            pytest.skip("submit_and_follow not supported")

        sysadmin = factories.Sysadmin()
        # need a dataset for the 'bulk_action.site_add' button to show
        factories.Dataset()

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(url=url_for("site_new"), extra_environ=env,)

        # create site
        form = response.forms["dataset-edit"]
        form["name"] = u"my-site"
        create_response = helpers.submit_and_follow(app, form, env, "save")

        # Unique to manage_datasets page
        assert "bulk_action.site_add" in create_response
        # Requested page is the manage_datasets url.
        assert (
            url_for("site_manage_datasets", id="my-site")
            == create_response.request.path
        )

    def test_create_site(self, app):
        if not tk.check_ckan_version(min_version='2.9.0'):
            # Remove when dropping support for 2.8
            pytest.skip("data argument not supported in post()")

        sysadmin = factories.Sysadmin()

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        app.post(
            url=url_for("site_new"),
            extra_environ=env,
            data={
                "name": "my-test-site",
                "image_url": "",
                "notes": "My new description!"
                }
            )

        res = app.get(
            url=url_for("site_read", id="my-test-site"),
            extra_environ=env,
        )
        assert "my-test-site" in res.body
        assert "My new description!" in res.body



@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSiteEditView(object):
    def test_site_edit_form_renders(self, app):
        """
        Edit form renders in response for SiteController edit action.
        """

        sysadmin = factories.Sysadmin()
        factories.Dataset(name="my-site", type="site")

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(
            url=url_for("site_edit", id="my-site"), extra_environ=env,
        )
        assert "dataset-edit" in response

    def test_site_edit_redirects_to_site_details(self, app):
        """Editing a site redirects to the site details page."""
        if tk.check_ckan_version("2.9"):
            pytest.skip("submit_and_follow not supported")

        sysadmin = factories.Sysadmin()
        factories.Dataset(name="my-site", type="site")

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(
            url=url_for("site_edit", id="my-site"), extra_environ=env,
        )

        # edit site
        form = response.forms["dataset-edit"]
        form["name"] = u"my-changed-site"
        edit_response = helpers.submit_and_follow(app, form, env, "save")

        # Requested page is the site read url.
        assert (
            url_for("site_read", id="my-changed-site")
            == edit_response.request.path
        )

    def test_edit_site(self, app):
        if not tk.check_ckan_version(min_version='2.9.0'):
            # Remove when dropping support for 2.8
            pytest.skip("data argument not supported in post()")

        sysadmin = factories.Sysadmin()
        factories.Dataset(name="my-site", type="site")
        env = {"REMOTE_USER": sysadmin["name"]}

        app.post(
            url=url_for("site_edit", id="my-site"),
            extra_environ=env,
            data={
                "name": "my-edited-site",
                "notes": "My new description!",
                "image_url": ""
            }
        )
        res = app.get(
            url=url_for("site_edit", id="my-edited-site"),
            extra_environ=env,
        )
        assert "my-edited-site" in res.body
        assert "My new description!" in res.body


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestDatasetView(object):

    """Plugin adds a new sites view for datasets."""

    def test_dataset_read_has_sites_tab(self, app):
        """
        Dataset view page has a new Sites tab linked to the correct place.
        """

        dataset = factories.Dataset(name="my-dataset")

        if tk.check_ckan_version("2.9"):
            url = url = url_for("dataset.read", id=dataset["id"])
        else:
            url = url_for(
                controller="package", action="read", id=dataset["id"]
            )
        response = app.get(url)
        # response contains link to dataset's site list
        assert "/dataset/sites/{0}".format(dataset["name"]) in response

    def test_dataset_site_page_lists_sites_no_associations(self, app):
        """
        No sites are listed if dataset has no site associations.
        """

        dataset = factories.Dataset(name="my-dataset")

        response = app.get(
            url=url_for("site_dataset_site_list", id=dataset["id"])
        )

        assert (
            len(
                BeautifulSoup(response.body).select(
                    "ul.media-grid li.media-item"
                )
            )
            == 0
        )

    def test_dataset_site_page_lists_sites_two_associations(self, app):
        """
        Two sites are listed for dataset with two site associations.
        """

        sysadmin = factories.Sysadmin()
        org = factories.Organization()
        dataset = factories.Dataset(name="my-dataset", owner_org=org["id"])
        site_one = factories.Dataset(
            name="my-first-site", type="site"
        )
        site_two = factories.Dataset(
            name="my-second-site", type="site"
        )
        factories.Dataset(name="my-third-site", type="site")

        context = {"user": sysadmin["name"]}
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=dataset["id"],
            site_id=site_one["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=dataset["id"],
            site_id=site_two["id"],
            organization_id=org["id"]
        )

        response = app.get(
            url=url_for("site_dataset_site_list", id=dataset["id"])
        )

        assert len(BeautifulSoup(response.body).select("li.media-item")) == 2
        assert "my-first-site" in response
        assert "my-second-site" in response
        assert "my-third-site" not in response

    def test_dataset_site_page_add_to_site_dropdown_list(self, app):
        """
        Add to site dropdown only lists sites that aren't already
        associated with dataset.
        """
        if tk.check_ckan_version("2.9"):
            pytest.skip("submit_and_follow not supported")

        sysadmin = factories.Sysadmin()
        org = factories.Organization()
        dataset = factories.Dataset(name="my-dataset", owner_org=org["id"])
        site_one = factories.Dataset(
            name="my-first-site", type="site"
        )
        site_two = factories.Dataset(
            name="my-second-site", type="site"
        )
        site_three = factories.Dataset(
            name="my-third-site", type="site"
        )

        context = {"user": sysadmin["name"]}
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=dataset["id"],
            site_id=site_one["id"],
            organization_id=org["id"]
        )

        response = app.get(
            url=url_for("site_dataset_site_list", id=dataset["id"]),
            extra_environ={"REMOTE_USER": str(sysadmin["name"])},
        )

        site_add_form = response.forms["site-add"]
        site_added_options = [
            value for (value, _) in site_add_form["site_added"].options
        ]
        assert site_one["id"] not in site_added_options
        assert site_two["id"] in site_added_options
        assert site_three["id"] in site_added_options

    def test_dataset_site_page_add_to_site_dropdown_submit(self, app):
        """
        Submitting 'Add to site' form with selected site value creates
        a sc/pkg association.
        """

        sysadmin = factories.Sysadmin()
        org = factories.Organization()
        dataset = factories.Dataset(name="my-dataset", owner_org=org["id"])
        site_one = factories.Dataset(
            name="my-first-site", type="site"
        )
        factories.Dataset(name="my-second-site", type="site")
        factories.Dataset(name="my-third-site", type="site")

        assert model.Session.query(SitePackageAssociation).count() == 0
        if tk.check_ckan_version("2.9"):
            pytest.skip("submit_and_follow not supported")

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}

        response = app.get(
            url=url_for("site_dataset_site_list", id=dataset["id"]),
            extra_environ=env,
        )

        form = response.forms["site-add"]
        form["site_added"] = site_one["id"]
        site_add_response = helpers.submit_and_follow(app, form, env)

        # returns to the correct page
        assert (
            site_add_response.request.path
            == "/dataset/sites/my-dataset"
        )
        # an association is created
        assert model.Session.query(SitePackageAssociation).count() == 1

    def test_dataset_site_page_remove_site_button_submit(self, app):
        """
        Submitting 'Remove' form with selected site value deletes a sc/pkg
        association.
        """

        sysadmin = factories.Sysadmin()
        org = factories.Organization()
        dataset = factories.Dataset(name="my-dataset", owner_org=org["id"])
        site_one = factories.Dataset(
            name="my-first-site", type="site"
        )

        context = {"user": sysadmin["name"]}
        helpers.call_action(
            "ckanext_site_package_association_create",
            context=context,
            package_id=dataset["id"],
            site_id=site_one["id"],
            organization_id=org["id"]
        )

        assert model.Session.query(SitePackageAssociation).count() == 1
        if tk.check_ckan_version("2.9"):
            pytest.skip("submit_and_follow not supported")

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(
            url=url_for("site_dataset_site_list", id=dataset["id"]),
            extra_environ=env,
        )
        # Submit the remove form.
        form = response.forms[1]
        assert form["remove_site_id"].value == site_one["id"]
        site_remove_response = helpers.submit_and_follow(app, form, env)

        # returns to the correct page
        assert (
            site_remove_response.request.path
            == "/dataset/sites/my-dataset"
        )
        # the association is deleted
        assert model.Session.query(SitePackageAssociation).count() == 0


@pytest.mark.usefixtures("clean_db")
class TestSiteAdminManageView(object):

    """Plugin adds a site admin management page to ckan-admin section."""

    def test_ckan_admin_has_site_config_tab(self, app):
        """
        ckan-admin index page has a site config tab.
        """
        if not tk.check_ckan_version(min_version="2.4"):
            pytest.skip(
                "Site config tab only available for CKAN 2.4+"
            )

        sysadmin = factories.Sysadmin()

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(
            url=url_for(controller="admin", action="index"), extra_environ=env
        )
        # response contains link to dataset's site list
        assert "/ckan-admin/site_admins" in response

    def test_site_admin_manage_page_returns_correct_status(self, app):
        """
        /ckan-admin/site_admins can be successfully accessed.
        """

        sysadmin = factories.Sysadmin()

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        app.get(url=url_for("site_admins"), status=200, extra_environ=env)

    def test_site_admin_manage_page_lists_site_admins(self, app):
        """
        Site admins are listed on the site admin page.
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

        sysadmin = factories.Sysadmin()

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(
            url=url_for("site_admins"), status=200, extra_environ=env
        )

        assert "/user/{0}".format(user_one["name"]) in response
        assert "/user/{0}".format(user_two["name"]) in response
        assert "/user/{0}".format(user_three["name"]) not in response

    def test_site_admin_manage_page_no_admins_message(self, app):
        """
        Site admins page displays message if no site admins present.
        """

        sysadmin = factories.Sysadmin()

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(
            url=url_for("site_admins"), status=200, extra_environ=env
        )

        assert "There are currently no Site Admins" in response


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSearch(object):
    def test_search_with_nonascii_filter_query(self, app):
        """
        Searching with non-ASCII filter queries works.

        See https://github.com/ckan/ckanext-site/issues/34.
        """

        tag = u"\xe4\xf6\xfc"
        factories.Dataset(tags=[{"name": tag, "state": "active"}])
        result = helpers.call_action("package_search", fq="tags:" + tag)
        assert result["count"] == 1


@pytest.mark.usefixtures('clean_db')
class TestCKEditor(object):
    @pytest.mark.ckan_config("ckanext.site.editor", "ckeditor")
    def test_rich_text_editor_is_shown_when_configured(self, app):

        sysadmin = factories.Sysadmin()
        factories.Dataset(name="my-site", type="site")

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(
            url=url_for("site_edit", id="my-site",), extra_environ=env,
        )
        assert '<textarea id="editor"' in response.body

    def test_rich_text_editor_is_not_shown_when_not_configured(self, app):

        sysadmin = factories.Sysadmin()
        factories.Dataset(name="my-site", type="site")

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(
            url=url_for("site_edit", id="my-site",), extra_environ=env,
        )
        assert '<textarea id="editor"' not in response.body

    @pytest.mark.ckan_config("ckanext.site.editor", "ckeditor")
    def test_custom_div_content_is_used_with_ckeditor(self, app):
        sysadmin = factories.Sysadmin()
        factories.Dataset(name='my-site', type='site')

        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}
        response = app.get(
            url=url_for("site_read", id="my-site",), extra_environ=env,
        )
        assert '<div class="ck-content">' in response.body
