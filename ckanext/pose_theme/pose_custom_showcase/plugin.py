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


import ckanext.pose_theme.pose_custom_showcase.helpers as showcase_helpers
import ckanext.pose_theme.pose_custom_showcase.actions as actions

_ = tk._

log = logging.getLogger(__name__)

DATASET_TYPE_NAME = "showcase"


class PoseShowcasePlugin(plugins.SingletonPlugin, lb.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions, inherit=True)

    # IConfigurer
    def update_config(self, config):
        tk.add_template_directory(config, "templates")
        tk.add_public_directory(config, "public")
        tk.add_resource("assets", "showcase")

    # ITemplateHelpers
    def get_helpers(self):
        return {
            "facet_remove_field": showcase_helpers.facet_remove_field,
            "get_site_statistics": showcase_helpers.get_site_statistics,
            "get_showcase_wysiwyg_editor": showcase_helpers.get_wysiwyg_editor,
            "get_recent_showcase_list": showcase_helpers.get_recent_showcase_list,
            "get_package_showcase_list": showcase_helpers.get_package_showcase_list,
            "get_value_from_showcase_extras": showcase_helpers.get_value_from_showcase_extras,
            "scheming_groups_choices": showcase_helpers.scheming_groups_choices,
            "get_package_dict": showcase_helpers.get_package_dict,
            "get_image_url": showcase_helpers.get_image_url,
        }

    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        """Only show tags for Showcase search list."""
        if package_type != DATASET_TYPE_NAME:
            return facets_dict
        return OrderedDict({"tags": _("Tags")})

    # IPackageController
    def before_dataset_search(self, search_params):

        if tk.request and tk.request.path[0:8] == "/dataset":
            search_params.update(
                {"fq": "+dataset_type:dataset {}".format(search_params.get("fq"))}
            )

        if tk.request and tk.request.path[0:6] == "/group":
            search_params.update(
                {"fq": "+dataset_type:dataset {}".format(search_params.get("fq"))}
            )

        return search_params

    # IActions
    def get_actions(self):
        return {
            "ckanext_showcase_list": actions.showcase_list,
        }