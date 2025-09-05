import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.pose_theme.base.helpers as helper
from ckanext.pose_theme.pose_custom_homepage.constants import CUSTOM_NAMING, CUSTOM_STYLE

if toolkit.check_ckan_version(min_version='2.9.0'):
    from ckanext.pose_theme.pose_custom_homepage.plugin.flask_plugin import MixinPlugin
else:
    from ckanext.pose_theme.pose_custom_homepage.plugin.pylons_plugin import MixinPlugin


class PoseThemeHomepagePlugin(MixinPlugin):
    plugins.implements(plugins.IConfigurable, inherit=True)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer
    def update_config(self, ckan_config):
        toolkit.add_template_directory(ckan_config, '../templates')
        toolkit.add_public_directory(ckan_config, '../public')
        toolkit.add_resource('../assets', 'pose_custom_homepage')

        if toolkit.check_ckan_version(min_version='2.4', max_version='2.9'):
            toolkit.add_ckan_admin_tab(ckan_config, 'custom_homepage', 'Homepage', icon='file-code-o')
        elif toolkit.check_ckan_version(min_version='2.9'):
            toolkit.add_ckan_admin_tab(ckan_config, 'custom-homepage.custom_homepage', 'Homepage', icon='file-code-o')

    def update_config_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing')
        dict_only = toolkit.get_validator('dict_only')
        int_validator = toolkit.get_validator('int_validator')
        schema.update({
            # This is a custom configuration option
            CUSTOM_NAMING: [ignore_missing, dict_only],
            CUSTOM_STYLE: [ignore_missing, int_validator]
        })
        return schema

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'pose_theme_get_dataset_count': helper.dataset_count,
            'pose_theme_get_showcases': helper.showcases,
            'pose_theme_get_extensions': helper.extensions,
            'pose_theme_get_sites': helper.sites,
            'pose_theme_get_story_banner': helper.get_story_banner,
            'pose_theme_get_showcases_story': helper.showcase_story,
            'pose_theme_get_value_from_extras': helper.get_value_from_extras,
            'pose_theme_get_groups': helper.groups,
            'pose_theme_get_organization': helper.organization,
            'pose_theme_get_datasets_new': helper.new_datasets,
            'pose_theme_get_datasets_popular': helper.popular_datasets,
            'pose_theme_get_datasets_recent': helper.recent_datasets,
            'pose_theme_get_package_tracking_summary': helper.package_tracking_summary,
            'pose_theme_get_custom_name': helper.get_custom_name,
            'pose_theme_get_data': helper.get_data,
            'pose_theme_search_document_page_exists': helper.search_document_page_exists,
            'pose_theme_get_featured_extensions': helper.featured_extensions,
            'pose_theme_get_featured_sites': helper.featured_sites,
            'version': helper.version_builder,
            'is_activity_enabled': helper.is_activity_enabled,
        }
