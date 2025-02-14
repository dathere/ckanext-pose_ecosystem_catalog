from ckanext.pose_theme.base.processor import AbstractParser

__all__ = ["custom_naming_processor"]


class GroupsNaming(AbstractParser):
    form_name = "groups-custom-name"
    title = "Groups Section Title"
    _default_value = "Groups"


class ShowcasesNaming(AbstractParser):
    form_name = "showcases-custom-name"
    title = "Showcases Section Title"
    _default_value = "Showcases"

class ExtensionsNaming(AbstractParser):
    form_name = "extensions-custom-name"
    title = "Extensions Section Title"
    _default_value = "Extensions"


class SitesNaming(AbstractParser):
    form_name = "sites-custom-name"
    title = "Sites Section Title"
    _default_value = "Sites"


class PopularDatasetsNaming(AbstractParser):
    form_name = "popular-datasets-custom-name"
    title = "Popular Datasets Section Title"
    _default_value = "Popular Datasets"


class RecentDatasetsNaming(AbstractParser):
    form_name = "recent-datasets-custom-name"
    title = "Recent Datasets Section Title"
    _default_value = "New and Recent Datasets"


class CustomNamingProcessor:

    def __init__(self):
        self.groups = GroupsNaming()
        self.showcases = ShowcasesNaming()
        self.popular_datasets = PopularDatasetsNaming()
        self.recent_datasets = RecentDatasetsNaming()
        self.extensions = ExtensionsNaming()
        self.sites = SitesNaming()

        self.naming_processors = (
            self.groups,
            self.showcases,
            self.extensions,
            self.sites,
            self.popular_datasets,
            self.recent_datasets
        )

    def get_custom_naming(self, data):
        result = {}
        for processor in self.naming_processors:
            processor.parse_form_data(data)
            result[processor.form_name] = {
                "title": processor.title,
                "value": processor.value,
            }
        return result


custom_naming_processor = CustomNamingProcessor()
