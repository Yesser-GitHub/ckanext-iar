from ckan.common import _, c, request, response, config
import ckan.logic as logic
import ckan.model as model
import ckan.lib.base as base
import sqlalchemy
from ckan.controllers.api import ApiController
import requests
import time
import ckan.lib.jsonp as jsonp
import json
from paste.deploy.converters import asbool

get_action = logic.get_action
_check_access = logic.check_access
_or_ = sqlalchemy.or_
api_cntr = ApiController()


def get_dataset_data(context, data_dict):
    model = context['model']

    _check_access('package_autocomplete', context, data_dict)

    limit = data_dict.get('limit', 10)
    q = data_dict['q']
    exc = data_dict.get('except')
    like_q = u"%s%%" % q
    query = model.Session.query(model.Package)
    query = query.filter(model.Package.state == 'active')
    query = query.filter(model.Package.private == False)
    query = query.filter(_or_(model.Package.name.ilike(like_q),
                              model.Package.title.ilike(like_q)))\
        .filter(model.Package.name != exc)
    query = query.limit(limit)

    q_lower = q.lower()
    pkg_list = []
    for package in query:
        if package.name.startswith(q_lower):
            match_field = 'name'
            match_displayed = package.name
        else:
            match_field = 'title'
            match_displayed = '%s (%s)' % (package.title, package.name)
        result_dict = {
            'name': package.name,
            'title': package.title,
            'match_field': match_field,
            'match_displayed': match_displayed}
        pkg_list.append(result_dict)

    return pkg_list


class APIController(base.BaseController):

    def ksa_dataset_autocomplete(self):
        q = request.params.get('incomplete', '')
        limit = request.params.get('limit', 10)
        exc = request.params.get('except', '')
        package_dicts = []
        if q:
            context = {'model': model, 'session': model.Session,
                       'user': c.user, 'auth_user_obj': c.userobj}

            data_dict = {'q': q, 'limit': limit, 'except': exc}

            package_dicts = get_dataset_data(context, data_dict)
        resultSet = {'ResultSet': {'Result': package_dicts}}
        return api_cntr._finish_ok(resultSet)

