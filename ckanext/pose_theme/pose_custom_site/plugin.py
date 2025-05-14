# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
from collections import OrderedDict

from six import string_types

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ckan.lib.plugins as lb
import ckan.lib.helpers as h


import ckanext.pose_theme.pose_custom_site.helpers as site_helpers
import ckanext.pose_theme.pose_custom_site.actions as actions

_ = tk._

log = logging.getLogger(__name__)

DATASET_TYPE_NAME = "site"


class PoseSitePlugin(plugins.SingletonPlugin, lb.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions, inherit=True)

    # IConfigurer
    def update_config(self, config):
        tk.add_template_directory(config, "templates")
        tk.add_public_directory(config, "public")
        tk.add_resource("assets", "site")

    # ITemplateHelpers
    def get_helpers(self):
        return {
            "facet_remove_field": site_helpers.facet_remove_field,
            "get_site_statistics": site_helpers.get_site_statistics,
            "get_site_wysiwyg_editor": site_helpers.get_wysiwyg_editor,
            "get_recent_site_list": site_helpers.get_recent_site_list,
            "get_package_site_list": site_helpers.get_package_site_list,
            "get_value_from_site_extras": site_helpers.get_value_from_site_extras,
            "scheming_groups_choices": site_helpers.scheming_groups_choices,
            "get_package_dict": site_helpers.get_package_dict,
        }

    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        """Only show tags for Site search list."""
        if package_type != DATASET_TYPE_NAME:
            return facets_dict
        return OrderedDict({"tags": _("Tags")})

    # IActions
    def get_actions(self):
        return {
            "ckanext_site_list": actions.site_list,
        }