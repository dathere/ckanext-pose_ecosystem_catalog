import ckan.lib.dictization.model_dictize as model_dictize


def extension_list(context, data_dict):
    model = context["model"]

    q = model.Session.query(model.Package) \
        .filter(model.Package.type == 'extension') \
        .filter(model.Package.state == 'active')

    extension_list = []
    for pkg in q.all():
        extension_list.append(model_dictize.package_dictize(pkg, context))

    return extension_list
