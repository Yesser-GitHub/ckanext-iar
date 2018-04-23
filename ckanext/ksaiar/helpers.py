import ckan.model as model
import ckan.logic as logic
from ckan.common import c, _

def get_ksa_helpers():
    return dict(
        ksa_bit_check=ksa_bit_check,
        relation_attrs_update=relation_attrs_update,
        relations_display=relations_display,
		relation_display=relation_display
    )

def ksa_bit_check(mask, pos):
    return bool(int(mask or 0) & 1 << pos)

def relation_attrs_update(data, attrs):
	api_url = ''
	if data.get('name'):
		current_dataset_name = data.get('name')
		for attr in attrs:
			if attr == 'data-module-source':
				if current_dataset_name not in attrs[attr]:
					api_url = attrs[attr] + "&except=" + current_dataset_name
		if api_url:
			attrs['data-module-source'] = api_url
		return attrs
	return

def relations_display(value):
	dataset_list = []
	context = {
		'model': model, 
	 	'session': model.Session,
        'user': c.user, 
		'auth_user_obj': c.userobj
	}
	if value:
		data = value.split(',')
		for dataset in data:
			# pkg = model.Package.get(dataset)
			pkg = logic.get_action('package_show')(context, {'id': dataset})
			if pkg:
				dataset_list.append(pkg)
		return dataset_list
	return

def relation_display(data):
	context = {
		'model': model, 
	 	'session': model.Session,
        'user': c.user, 
		'auth_user_obj': c.userobj
	}
	if data:
		pkg = ''
		try:
			pkg = logic.get_action('package_show')(context, {'id': data})
		except logic.NotFound:
			return
		return pkg
	return
