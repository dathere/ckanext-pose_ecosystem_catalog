import ckan.lib.helpers as h
from ckan.plugins import toolkit as tk


def facet_remove_field(key, value=None, replace=None):
    """
    A custom remove field function to be used by the Showcase search page to
    render the remove link for the tag pills.
    """
    if tk.check_ckan_version(min_version="2.9.0"):
        index_route = "showcase_blueprint.index"
    else:
        index_route = "showcase_index"

    return h.remove_url_param(
        key, value=value, replace=replace, alternative_url=h.url_for(index_route)
    )


def get_site_statistics():
    """
    Custom stats helper, so we can get the correct number of packages, and a
    count of showcases.
    """

    stats = {}
    stats["showcase_count"] = tk.get_action("package_search")(
        {}, {"rows": 1, "fq": "+dataset_type:showcase"}
    )["count"]
    stats["dataset_count"] = tk.get_action("package_search")(
        {}, {"rows": 1, "fq": "!dataset_type:showcase"}
    )["count"]
    stats["group_count"] = len(tk.get_action("group_list")({}, {}))
    stats["organization_count"] = len(tk.get_action("organization_list")({}, {}))

    return stats


def get_wysiwyg_editor():
    return tk.config.get("ckanext.showcase.editor", "")


def get_recent_showcase_list(num=24):
    """Return a list of recent showcases."""
    showcases = []
    showcases = tk.get_action("ckanext_showcase_list")({}, {})
    sorted_showcases = sorted(
        showcases, key=lambda k: k["metadata_modified"], reverse=True
    )

    return sorted_showcases[:num]


def get_image_url(image_url):
    if 'https://' in image_url or 'http://' in image_url:
        return image_url
    print("***********************************", tk.h.url_for_static(image_url))
    return tk.h.url_for_static(image_url)

def get_package_showcase_list(package_id):
    showcases = []
    try:
        showcases = tk.get_action("ckanext_package_showcase_list")(
            {}, {"package_id": package_id}
        )
    except Exception as e:
        return []
    return showcases


def get_value_from_showcase_extras(extras, key):
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
