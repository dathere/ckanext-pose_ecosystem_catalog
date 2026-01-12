import pytest
import ckan.tests.helpers as helpers
import ckan.tests.factories as factories


@pytest.mark.usefixtures('with_plugins', 'clean_db')
@pytest.mark.ckan_config("ckan.plugins", "datastore pose_custom_theme")
class TestDataDictionaryDownload(object):

    def test_data_dictionary_download_basic(self, app):
        resource = factories.Resource()
        data = {
            "resource_id": resource["id"],
            "force": True,
            "records": [{u"book": "annakarenina"}, {u"book": "warandpeace"}],
        }
        helpers.call_action("datastore_create", **data)

        response = app.get(f'/datastore/dictionary_download/{resource["id"]}')
        assert (
            "column,type,label,description\r\n"
            "book,text,,\r\n" == response.get_data(as_text=True)
        )
