import pytest

import ckan.model as model
from ckan.plugins import toolkit

from ckanext.extension.model import setup as model_setup

@pytest.fixture
def extension_setup():
    model_setup()

@pytest.fixture
def clean_session():
    if toolkit.check_ckan_version(max_version='2.9.0'):
        if hasattr(model.Session, 'revision'):
            model.Session.revision = None
