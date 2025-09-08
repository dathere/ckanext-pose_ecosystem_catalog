'''
import ckan.lib.dictization.model_dictize as model_dictize

def showcase_list(context, data_dict):
    model = context["model"]

    q = model.Session.query(model.Package) \
        .filter(model.Package.type == 'site') \
        .filter(model.Package.state == 'active') \
        .filter(model.PackageExtra.key == 'is_featured') \
        .filter(model.PackageExtra.value == 'TRUE')

    showcase_list = []
    for pkg in q.all():
        showcase_list.append(model_dictize.package_dictize(pkg, context))

    return showcase_list 

'''

import ckan.plugins.toolkit as toolkit

def showcase_list(context, data_dict):
    """Return list of featured site packages"""
    search_result = toolkit.get_action('package_search')(context, {
        'q': 'type:site',
        'fq': 'extras_is_featured:TRUE',
        'rows': 100,
        'start': 0
    })
    
    return search_result.get('results', [])

