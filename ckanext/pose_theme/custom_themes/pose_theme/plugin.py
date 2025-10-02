import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.pose_theme.base.helpers as helper
import ckanext.pose_theme.custom_themes.pose_theme.blueprint as view
import ckanext.pose_theme.custom_themes.pose_theme.cli as cli
from ckanext.pose_theme.routes import contact

class PoseThemePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IClick)

    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        """Customize the facets displayed for datasets."""
        if package_type == "site":
            if facets_dict is None:
                # Ensure facets_dict is a dictionary
                facets_dict = {}
            # Remove the "license" facet if it exists
            if "license_id" in facets_dict:
                del facets_dict["license_id"]
            # Remove the "format" facet if it exists
            if "res_format" in facets_dict:
                del facets_dict["res_format"]
        # Return the modified facets dictionary
        return facets_dict

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
            'contact_form_legend_content': [ignore_missing, ignore_not_sysadmin]
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

    def get_commands(self):
        return [cli.pose_theme]

    # IBlueprint
    def get_blueprint(self):
        # Combine both blueprint lists
        blueprints = view.get_blueprints()
        blueprints.extend(contact.get_blueprints())
        return blueprints