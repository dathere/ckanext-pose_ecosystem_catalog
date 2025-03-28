import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.pose_theme.base.helpers as helper
import ckanext.pose_theme.custom_themes.pose_theme.blueprint as view


class PoseThemePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)

    # IConfigurer   
    def update_config(self, ckan_config):
        toolkit.add_template_directory(ckan_config, 'templates')
        toolkit.add_public_directory(ckan_config, 'public')
        toolkit.add_resource('assets', 'pose_theme')
        toolkit.add_public_directory(ckan_config, "assets")

    def update_config_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing')
        ignore_not_sysadmin = toolkit.get_validator('ignore_not_sysadmin')

        schema.update({
            # This is a custom configuration option
            'contact_form_legend_content': [ignore_missing,
                                            ignore_not_sysadmin]
        })

        return schema

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'pose_theme_group_alias': helper.get_group_alias,
            'pose_theme_organization_alias': helper.get_organization_alias,
            'pose_theme_get_default_extent': helper.get_default_extent,
            'pose_theme_is_data_dict_active': helper.is_data_dict_active,
            'version': helper.version_builder,
        }

    # IBlueprint
    def get_blueprint(self):
        return view.get_blueprints()
