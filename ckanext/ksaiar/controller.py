import math
import uuid
import json
import StringIO
import pdfkit
from datetime import datetime

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.logic as logic
import ckan.model as model
import ckan.plugins as p
from ckan.common import response
from ckan.lib.base import BaseController, c, render, request
from ckan.controllers.package import PackageController
from ckan.model import Session
import ckanext.ksaiar.questionnaire as questionnaire
import ckanext.ksaiar.questionnaire_ar as questionnaire_ar

from paste.deploy.converters import asbool
from pylons import config

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
UsernamePasswordError = logic.UsernamePasswordError

class KsaPackageController(PackageController):

    def allow_dqs(self, id):
        """
        """
        context = {
            'model': model,
            'session': model.Session,
            'user': c.user or c.author,
            'auth_user_obj': c.userobj,
            'for_view': True
        }

        try:
            p.toolkit.check_access('ksa_update_dqs', context)
            package = logic.get_action('package_show')(context, {'id': id})
            pkg = context['package']
        except NotFound:
            base.abort(404, _('Dataset not found'))
        except NotAuthorized:
            base.abort(
                401,
                _('User %s not authorized to enable DQS of %s') % (c.user, id)
            )

        logic.get_action('package_patch')(
            context, {
                'id': id,
                'dqs_uuid': uuid.uuid4()
            }
        )
        return h.redirect_to('dataset_edit', id=id)

    def _get_pkg_id_by_dqs_uuid(self, dqs_uuid):
        pkg = model.Session.query(model.Package.id).join(
            model.PackageExtra,
            model.Package.id == model.PackageExtra.package_id
        ).filter_by(
            key='dqs_uuid', value=dqs_uuid
        ).first()
        if pkg is None:
            raise p.toolkit.ObjectNotFound
        return pkg.id

    def _get_pkg_by_dqs_uuid(self, dqs_uuid):
        context = {
            'model': model,
            'session': model.Session,
            'user': c.user or c.author,
            'auth_user_obj': c.userobj,
            'for_view': True
        }
        try:
            id = self._get_pkg_id_by_dqs_uuid(dqs_uuid)
            p.toolkit.check_access('ksa_update_dqs', context)
            package = logic.get_action('package_show')(context, {'id': id})
        except NotFound:
            base.abort(404, _('Dataset not found'))
        except NotAuthorized:
            base.abort(
                401,
                _('User %s not authorized to edit DQS of %s') % (c.user, id)
            )
        return package, context

    def _resource_create(self, context, data_dict):
        model = context['model']

        package_id = logic.get_or_bust(data_dict, 'package_id')
        logic.get_or_bust(data_dict, 'url')

        pkg_dict = logic.get_action('package_show')(context, {'id': package_id})

        logic.check_access('resource_create', context, data_dict)

        for plugin in p.PluginImplementations(p.IResourceController):
            plugin.before_create(context, data_dict)

        if 'resources' not in pkg_dict:
            pkg_dict['resources'] = []

        pkg_dict['resources'].append(data_dict)

        logic.get_action('package_patch')(
                context, {
                    'id': package_id,
                    'resources': pkg_dict['resources']
                })

    def update_dqs(self, dqs_uuid):
        """
        """
        package, context = self._get_pkg_by_dqs_uuid(dqs_uuid)
        if request.method == 'POST':
            bit_dqs = 0
            for name, value in request.POST.items():
                if not name.startswith('q-'):
                    continue
                idx = int(name[2:])
                bit_dqs |= 1 << idx
            user = logic.get_action('get_site_user')({
                'ignore_auth': True
            }, None)
            context = {'model': model, 'user': user['name']}
            package = logic.get_action('package_patch')(
                context, {
                    'id': package['id'],
                    'bit_dqs': bit_dqs
                }
            )
            allow_send_emails = asbool(config.get('ckan.ksa_dqs_allow_emails_send', 'False'))
            notif_emails = config.get('ckan.ksa_dqs_admin_emails', '').split()
            if len(notif_emails) > 0 and allow_send_emails:
                site_url = config.get('ckan.site_url', '')
                url = site_url + '/dataset/' + package['name']
                notif_names = 'admin'
                subject = 'DQS Updated for {0}'.format(package.get('title'))
                msg = '''The DQS for {title} dataset has been updated: {url}'''\
                    .format(title=package.get('title'), url=url)

                try:
                    for email in notif_emails:
                        mailer.mail_recipient(notif_names, email, subject, msg)
                except mailer.MailerException as e:
                    h.flash("Email error: {0}".format(
                        e.message), allow_html=False)

            data = {
                'id': dqs_uuid,
                'name': 'Data Quality Statement',
                'format': 'PDF',
                'package_id': package['id'],
                'url': h.url_for('ksa_export_dqs', dqs_uuid=dqs_uuid, qualified=True)
            }
            self._resource_create(context, data)
            return h.redirect_to('update_dataset_dqs', dqs_uuid=dqs_uuid)

        questionnaire_data = questionnaire.data
        if h.lang() == 'ar':
            questionnaire_data = questionnaire_ar.data

        extra_vars = {'pkg_dict': package, 'questionnaire': questionnaire_data}
        return base.render('package/update_dqs.html', extra_vars=extra_vars)

    def export_dqs(self, dqs_uuid):
        package, context = self._get_pkg_by_dqs_uuid(dqs_uuid)
        return self.dq_generate_pdf(package['id'])

    def dq_generate_pdf(self, id):
        """Generate data quality report in PDF format."""

        context = {
            'model': model,
            'session': model.Session,
            'user': c.user or c.author,
            'auth_user_obj': c.userobj,
            'for_view': True
        }
        try:
            package = logic.get_action('package_show')(context, {'id': id})
            pkg = context['package']
            package['asset_details'] = getattr(pkg, 'asset_details', {})
        except NotFound:
            base.abort(404, _('Dataset not found'))
        except NotAuthorized:
            base.abort(401, _('User not authorized') % (c.user, id))
        asset_details = pkg.extras.get('asset_details', '{}')
        package['asset_details'] = json.loads(asset_details)
        tpl_name = 'dq_pdf'
        if package['type'] == 'dataset':
            tpl_name = 'ksa_dq_pdf'

        questionnaire_data = questionnaire.data
        if h.lang() == 'ar':
            questionnaire_data = questionnaire_ar.data

        html = base.render(
            'package/{}.html'.format(tpl_name),
            extra_vars={
                'package': package,
                'date': datetime.now(),
                'questionnaire': questionnaire_data
            }
        )
        result = StringIO.StringIO()

        result = pdfkit.from_file(StringIO.StringIO(html), False)
        response.content_type = 'application/pdf'
        return result
