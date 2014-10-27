# -*- coding: utf-8 -*-

from flask import abort
from flask import current_app
from flask import flash
from flask import g

from reppo.repo.locals import repo_proxy


def init_repo_handlers(state):
    state.blueprint.url_value_preprocessor(_pull_repo_url_values)
    state.blueprint.url_defaults(_push_repo_url_values)
    state.blueprint.before_request(_before_requst_check_repo_rev_commit)


def _pull_repo_url_values(endpoint, values):
    g.repo_name = values.pop('repo_name', None)
    g.rev = values.pop('rev', None)


def _push_repo_url_values(endpoint, values):
    values.setdefault('repo_name', g.repo_name)

    if 'rev' in values:
        return

    if current_app.url_map.is_endpoint_expecting(endpoint, 'rev'):
        values['rev'] = g.rev


def _before_requst_check_repo_rev_commit():
    if not bool(repo_proxy):
        flash(u'Repo with name "{}" not found'.format(g.repo_name), u'repo-404')
        abort(404)

    if not bool(repo_proxy._commit):
        flash(u'Commit for rev "{}" in the "{}" repo not found'.format(g.rev, g.repo_name), u'repo-404')
        abort(404)
