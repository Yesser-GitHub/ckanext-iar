import ckan.model as model
from ckan.common import _

def get_validators():
    return dict(
        validate_relations=validate_relations
        )

def validate_relations(key, data, errors, context):
    collect_not_exist_datasets = []
    value = data.get(key)
    datasets_list = ''
    if value:
        datasets_list = value.split(',')
    if datasets_list:
        for name in datasets_list:
            pkg = model.Package.get(name)
            if not pkg:
                collect_not_exist_datasets.append(name)
                # rebuilded_name = name.strip()
                # rebuilded_name = rebuilded_name.replace(' ','-').lower()
                # pkg = model.Package.get(rebuilded_name)
                # if not pkg:
                #     collect_not_exist_datasets.append(name)
                # else:
                #     value = value.replace(name,rebuilded_name)
                #     data[key] = value
        if collect_not_exist_datasets:
            if len(collect_not_exist_datasets) == 1:
                errors[key].append(_("Dataset '{0}' does not exist.").format(','.join(collect_not_exist_datasets)))
            else:
                errors[key].append(_('There is a list of datasets that not exist: {0}.').format(', '.join(collect_not_exist_datasets)))