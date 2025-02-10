import pytest
from bs4 import BeautifulSoup

from ckan.lib.helpers import url_for


from ckan.plugins import toolkit as tk
import ckan.model as model

from ckan.tests import factories, helpers

from ckanext.extension.model import ExtensionPackageAssociation

import logging

log = logging.getLogger(__name__)


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestExtensionIndex(object):
    def test_extension_listed_on_index(self, app):
        """
        An added Extension will appear on the Extension index page.
        """

        factories.Dataset(type="extension", name="my-extension")

        response = app.get("/extension", status=200)
        assert "1 extension found" in response.body
        assert "my-extension" in response.body


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestExtensionNewView(object):
    def test_extension_create_form_renders(self, app):

        sysadmin = factories.Sysadmin()

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(url=url_for("extension_new"), extra_environ=env,)
        assert "dataset-edit" in response

    def test_extension_new_redirects_to_manage_datasets(self, app):
        """Creating a new extension redirects to the manage datasets form."""
        if tk.check_ckan_version("2.9"):
            pytest.skip("submit_and_follow not supported")

        sysadmin = factories.Sysadmin()
        # need a dataset for the 'bulk_action.extension_add' button to show
        factories.Dataset()

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(url=url_for("extension_new"), extra_environ=env,)

        # create extension
        form = response.forms["dataset-edit"]
        form["name"] = u"my-extension"
        create_response = helpers.submit_and_follow(app, form, env, "save")

        # Unique to manage_datasets page
        assert "bulk_action.extension_add" in create_response
        # Requested page is the manage_datasets url.
        assert (
            url_for("extension_manage_datasets", id="my-extension")
            == create_response.request.path
        )

    def test_create_extension(self, app):
        if not tk.check_ckan_version(min_version='2.9.0'):
            # Remove when dropping support for 2.8
            pytest.skip("data argument not supported in post()")

        sysadmin = factories.Sysadmin()

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        app.post(
            url=url_for("extension_new"),
            extra_environ=env,
            data={
                "name": "my-test-extension",
                "image_url": "",
                "notes": "My new description!"
                }
            )

        res = app.get(
            url=url_for("extension_read", id="my-test-extension"),
            extra_environ=env,
        )
        assert "my-test-extension" in res.body
        assert "My new description!" in res.body



@pytest.mark.usefixtures("clean_db", "clean_index")
class TestExtensionEditView(object):
    def test_extension_edit_form_renders(self, app):
        """
        Edit form renders in response for ExtensionController edit action.
        """

        sysadmin = factories.Sysadmin()
        factories.Dataset(name="my-extension", type="extension")

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(
            url=url_for("extension_edit", id="my-extension"), extra_environ=env,
        )
        assert "dataset-edit" in response

    def test_extension_edit_redirects_to_extension_details(self, app):
        """Editing a extension redirects to the extension details page."""
        if tk.check_ckan_version("2.9"):
            pytest.skip("submit_and_follow not supported")

        sysadmin = factories.Sysadmin()
        factories.Dataset(name="my-extension", type="extension")

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(
            url=url_for("extension_edit", id="my-extension"), extra_environ=env,
        )

        # edit extension
        form = response.forms["dataset-edit"]
        form["name"] = u"my-changed-extension"
        edit_response = helpers.submit_and_follow(app, form, env, "save")

        # Requested page is the extension read url.
        assert (
            url_for("extension_read", id="my-changed-extension")
            == edit_response.request.path
        )

    def test_edit_extension(self, app):
        if not tk.check_ckan_version(min_version='2.9.0'):
            # Remove when dropping support for 2.8
            pytest.skip("data argument not supported in post()")

        sysadmin = factories.Sysadmin()
        factories.Dataset(name="my-extension", type="extension")
        env = {"REMOTE_USER": sysadmin["name"]}

        app.post(
            url=url_for("extension_edit", id="my-extension"),
            extra_environ=env,
            data={
                "name": "my-edited-extension",
                "notes": "My new description!",
                "image_url": ""
            }
        )
        res = app.get(
            url=url_for("extension_edit", id="my-edited-extension"),
            extra_environ=env,
        )
        assert "my-edited-extension" in res.body
        assert "My new description!" in res.body


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestDatasetView(object):

    """Plugin adds a new extensions view for datasets."""

    def test_dataset_read_has_extensions_tab(self, app):
        """
        Dataset view page has a new Extensions tab linked to the correct place.
        """

        dataset = factories.Dataset(name="my-dataset")

        if tk.check_ckan_version("2.9"):
            url = url = url_for("dataset.read", id=dataset["id"])
        else:
            url = url_for(
                controller="package", action="read", id=dataset["id"]
            )
        response = app.get(url)
        # response contains link to dataset's extension list
        assert "/dataset/extensions/{0}".format(dataset["name"]) in response

    def test_dataset_extension_page_lists_extensions_no_associations(self, app):
        """
        No extensions are listed if dataset has no extension associations.
        """

        dataset = factories.Dataset(name="my-dataset")

        response = app.get(
            url=url_for("extension_dataset_extension_list", id=dataset["id"])
        )

        assert (
            len(
                BeautifulSoup(response.body).select(
                    "ul.media-grid li.media-item"
                )
            )
            == 0
        )

    def test_dataset_extension_page_lists_extensions_two_associations(self, app):
        """
        Two extensions are listed for dataset with two extension associations.
        """

        sysadmin = factories.Sysadmin()
        org = factories.Organization()
        dataset = factories.Dataset(name="my-dataset", owner_org=org["id"])
        extension_one = factories.Dataset(
            name="my-first-extension", type="extension"
        )
        extension_two = factories.Dataset(
            name="my-second-extension", type="extension"
        )
        factories.Dataset(name="my-third-extension", type="extension")

        context = {"user": sysadmin["name"]}
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=dataset["id"],
            extension_id=extension_one["id"],
            organization_id=org["id"]
        )
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=dataset["id"],
            extension_id=extension_two["id"],
            organization_id=org["id"]
        )

        response = app.get(
            url=url_for("extension_dataset_extension_list", id=dataset["id"])
        )

        assert len(BeautifulSoup(response.body).select("li.media-item")) == 2
        assert "my-first-extension" in response
        assert "my-second-extension" in response
        assert "my-third-extension" not in response

    def test_dataset_extension_page_add_to_extension_dropdown_list(self, app):
        """
        Add to extension dropdown only lists extensions that aren't already
        associated with dataset.
        """
        if tk.check_ckan_version("2.9"):
            pytest.skip("submit_and_follow not supported")

        sysadmin = factories.Sysadmin()
        org = factories.Organization()
        dataset = factories.Dataset(name="my-dataset", owner_org=org["id"])
        extension_one = factories.Dataset(
            name="my-first-extension", type="extension"
        )
        extension_two = factories.Dataset(
            name="my-second-extension", type="extension"
        )
        extension_three = factories.Dataset(
            name="my-third-extension", type="extension"
        )

        context = {"user": sysadmin["name"]}
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=dataset["id"],
            extension_id=extension_one["id"],
            organization_id=org["id"]
        )

        response = app.get(
            url=url_for("extension_dataset_extension_list", id=dataset["id"]),
            extra_environ={"REMOTE_USER": str(sysadmin["name"])},
        )

        extension_add_form = response.forms["extension-add"]
        extension_added_options = [
            value for (value, _) in extension_add_form["extension_added"].options
        ]
        assert extension_one["id"] not in extension_added_options
        assert extension_two["id"] in extension_added_options
        assert extension_three["id"] in extension_added_options

    def test_dataset_extension_page_add_to_extension_dropdown_submit(self, app):
        """
        Submitting 'Add to extension' form with selected extension value creates
        a sc/pkg association.
        """

        sysadmin = factories.Sysadmin()
        org = factories.Organization()
        dataset = factories.Dataset(name="my-dataset", owner_org=org["id"])
        extension_one = factories.Dataset(
            name="my-first-extension", type="extension"
        )
        factories.Dataset(name="my-second-extension", type="extension")
        factories.Dataset(name="my-third-extension", type="extension")

        assert model.Session.query(ExtensionPackageAssociation).count() == 0
        if tk.check_ckan_version("2.9"):
            pytest.skip("submit_and_follow not supported")

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}

        response = app.get(
            url=url_for("extension_dataset_extension_list", id=dataset["id"]),
            extra_environ=env,
        )

        form = response.forms["extension-add"]
        form["extension_added"] = extension_one["id"]
        extension_add_response = helpers.submit_and_follow(app, form, env)

        # returns to the correct page
        assert (
            extension_add_response.request.path
            == "/dataset/extensions/my-dataset"
        )
        # an association is created
        assert model.Session.query(ExtensionPackageAssociation).count() == 1

    def test_dataset_extension_page_remove_extension_button_submit(self, app):
        """
        Submitting 'Remove' form with selected extension value deletes a sc/pkg
        association.
        """

        sysadmin = factories.Sysadmin()
        org = factories.Organization()
        dataset = factories.Dataset(name="my-dataset", owner_org=org["id"])
        extension_one = factories.Dataset(
            name="my-first-extension", type="extension"
        )

        context = {"user": sysadmin["name"]}
        helpers.call_action(
            "ckanext_extension_package_association_create",
            context=context,
            package_id=dataset["id"],
            extension_id=extension_one["id"],
            organization_id=org["id"]
        )

        assert model.Session.query(ExtensionPackageAssociation).count() == 1
        if tk.check_ckan_version("2.9"):
            pytest.skip("submit_and_follow not supported")

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(
            url=url_for("extension_dataset_extension_list", id=dataset["id"]),
            extra_environ=env,
        )
        # Submit the remove form.
        form = response.forms[1]
        assert form["remove_extension_id"].value == extension_one["id"]
        extension_remove_response = helpers.submit_and_follow(app, form, env)

        # returns to the correct page
        assert (
            extension_remove_response.request.path
            == "/dataset/extensions/my-dataset"
        )
        # the association is deleted
        assert model.Session.query(ExtensionPackageAssociation).count() == 0


@pytest.mark.usefixtures("clean_db")
class TestExtensionAdminManageView(object):

    """Plugin adds a extension admin management page to ckan-admin section."""

    def test_ckan_admin_has_extension_config_tab(self, app):
        """
        ckan-admin index page has a extension config tab.
        """
        if not tk.check_ckan_version(min_version="2.4"):
            pytest.skip(
                "Extension config tab only available for CKAN 2.4+"
            )

        sysadmin = factories.Sysadmin()

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(
            url=url_for(controller="admin", action="index"), extra_environ=env
        )
        # response contains link to dataset's extension list
        assert "/ckan-admin/extension_admins" in response

    def test_extension_admin_manage_page_returns_correct_status(self, app):
        """
        /ckan-admin/extension_admins can be successfully accessed.
        """

        sysadmin = factories.Sysadmin()

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        app.get(url=url_for("extension_admins"), status=200, extra_environ=env)

    def test_extension_admin_manage_page_lists_extension_admins(self, app):
        """
        Extension admins are listed on the extension admin page.
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

        sysadmin = factories.Sysadmin()

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(
            url=url_for("extension_admins"), status=200, extra_environ=env
        )

        assert "/user/{0}".format(user_one["name"]) in response
        assert "/user/{0}".format(user_two["name"]) in response
        assert "/user/{0}".format(user_three["name"]) not in response

    def test_extension_admin_manage_page_no_admins_message(self, app):
        """
        Extension admins page displays message if no extension admins present.
        """

        sysadmin = factories.Sysadmin()

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(
            url=url_for("extension_admins"), status=200, extra_environ=env
        )

        assert "There are currently no Extension Admins" in response


@pytest.mark.usefixtures("clean_db", "clean_index")
class TestSearch(object):
    def test_search_with_nonascii_filter_query(self, app):
        """
        Searching with non-ASCII filter queries works.

        See https://github.com/ckan/ckanext-extension/issues/34.
        """

        tag = u"\xe4\xf6\xfc"
        factories.Dataset(tags=[{"name": tag, "state": "active"}])
        result = helpers.call_action("package_search", fq="tags:" + tag)
        assert result["count"] == 1


@pytest.mark.usefixtures('clean_db')
class TestCKEditor(object):
    @pytest.mark.ckan_config("ckanext.extension.editor", "ckeditor")
    def test_rich_text_editor_is_shown_when_configured(self, app):

        sysadmin = factories.Sysadmin()
        factories.Dataset(name="my-extension", type="extension")

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(
            url=url_for("extension_edit", id="my-extension",), extra_environ=env,
        )
        assert '<textarea id="editor"' in response.body

    def test_rich_text_editor_is_not_shown_when_not_configured(self, app):

        sysadmin = factories.Sysadmin()
        factories.Dataset(name="my-extension", type="extension")

        env = {"REMOTE_USER": sysadmin["name"].encode("ascii")}
        response = app.get(
            url=url_for("extension_edit", id="my-extension",), extra_environ=env,
        )
        assert '<textarea id="editor"' not in response.body

    @pytest.mark.ckan_config("ckanext.extension.editor", "ckeditor")
    def test_custom_div_content_is_used_with_ckeditor(self, app):
        sysadmin = factories.Sysadmin()
        factories.Dataset(name='my-extension', type='extension')

        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}
        response = app.get(
            url=url_for("extension_read", id="my-extension",), extra_environ=env,
        )
        assert '<div class="ck-content">' in response.body
