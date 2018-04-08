import ckan.plugins.toolkit as toolkit
import ckan.authz as authz

def ksa_allow_dqs(context, data_dict):
    return authz.is_authorized('package_update', context, data_dict)

@toolkit.auth_allow_anonymous_access
def ksa_update_dqs(context, data_dict=None):
    return {'success': True}
