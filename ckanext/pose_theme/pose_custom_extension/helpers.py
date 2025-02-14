import ckan.lib.helpers as h
from ckan.plugins import toolkit as tk


def facet_remove_field(key, value=None, replace=None):
    """
    A custom remove field function to be used by the Extension search page to
    render the remove link for the tag pills.
    """
    if tk.check_ckan_version(min_version="2.9.0"):
        index_route = "extension_blueprint.index"
    else:
        index_route = "extension_index"

    return h.remove_url_param(
        key, value=value, replace=replace, alternative_url=h.url_for(index_route)
    )


def get_site_statistics():
    """
    Custom stats helper, so we can get the correct number of packages, and a
    count of extensions.
    """

    stats = {}
    stats["extension_count"] = tk.get_action("package_search")(
        {}, {"rows": 1, "fq": "+dataset_type:extension"}
    )["count"]
    stats["dataset_count"] = tk.get_action("package_search")(
        {}, {"rows": 1, "fq": "!dataset_type:extension"}
    )["count"]
    stats["group_count"] = len(tk.get_action("group_list")({}, {}))
    stats["organization_count"] = len(tk.get_action("organization_list")({}, {}))

    return stats


def get_wysiwyg_editor():
    return tk.config.get("ckanext.extension.editor", "")


def get_recent_extension_list(num=24):
    """Return a list of recent extensions."""
    extensions = []
    extensions = tk.get_action("ckanext_extension_list")({}, {})
    sorted_extensions = sorted(
        extensions, key=lambda k: k["metadata_modified"], reverse=True
    )

    return sorted_extensions[:num]


def get_package_extension_list(package_id):
    extensions = []
    try:
        extensions = tk.get_action("ckanext_package_extension_list")(
            {}, {"package_id": package_id}
        )
    except Exception as e:
        return []
    return extensions


def get_value_from_extension_extras(extras, key):
    value = ""
    for item in extras:
        if item.get("key") == key:
            value = item.get("value", "")
    return value


def scheming_groups_choices(dummy_var="none"):
    """Return a list of groups for scheming choices helper"""
    groups = tk.get_action("group_list")({}, {"all_fields": True})

    group_choices = [{"value": g["name"], "label": g["display_name"]} for g in groups]
    return group_choices


def get_package_dict(packages):
    """
    Get a list of package dictionaries from a list of package ids.
    """
    package_dicts = []
    for package in packages:
        package_dict = tk.get_action("package_show")({}, {"id": package})
        package_dicts.append(package_dict)
    return package_dicts
