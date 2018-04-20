import uuid

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h
import ckan.logic as logic

import ckanext.ksaiar.logic.auth as ksa_auth
import ckanext.ksaiar.helpers as ksa_helpers
from ckanext.ksaiar.validators import get_validators


class KsaIarPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IAuthFunctions, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IValidators)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'ksaiar')

    # IAuthfunctions
    def get_auth_functions(self):
        return {
            'ksa_allow_dqs': ksa_auth.ksa_allow_dqs,
            'ksa_update_dqs': ksa_auth.ksa_update_dqs
        }

    def before_map(self, routeMap):
        controllerPackage = 'ckanext.ksaiar.controller:KsaPackageController'
        controller_api = 'ckanext.ksaiar.api_controller:APIController'

        routeMap.connect(
            "allow_dataset_dqs",
            '/dataset/{id}/allow_dqs',
            controller=controllerPackage,
            action='allow_dqs'
        )
        routeMap.connect(
            "update_dataset_dqs",
            '/dqs/{dqs_uuid}/update',
            controller=controllerPackage,
            action='update_dqs'
        )
        routeMap.connect(
            "ksa_export_dqs",
            '/dqs/{dqs_uuid}/export',
            controller=controllerPackage,
            action='export_dqs'
        )

        # API
        routeMap.connect(
            '/api/2/util/ksa_dataset/autocomplete',
            controller=controller_api,
            action='ksa_dataset_autocomplete')

        return routeMap

    #IPackageController
    def after_create(self, context, pkg_dict):
        pkg_id = pkg_dict.get('id', '')
        logic.get_action('package_patch')(
            context, {
                'id': pkg_id,
                'dqs_uuid': uuid.uuid4()
            }
        )

    # ITemplateHelpers
    def get_helpers(self):
        return ksa_helpers.get_ksa_helpers()

    # IValidators
    def get_validators(self):
        return get_validators()