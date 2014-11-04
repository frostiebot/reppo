# -*- coding: utf-8 -*-

from flask import abort
from flask import current_app
from flask import flash
from flask import g
from flask import request

from .locals import repo

endpoint_expects_rev = lambda: current_app.url_map.is_endpoint_expecting(request.endpoint, 'rev')


def init_repo_handlers(state):
    state.blueprint.url_defaults(_repo_url_defaults)
    state.blueprint.url_value_preprocessor(_repo_url_value_preprocessor)
    state.blueprint.before_request(_before_request_check_repo_and_rev)


def _repo_url_defaults(endpoint, values):
    values.setdefault('repo_name', g.repo_name)

    if 'rev' in values or not g.rev:
        return

    if endpoint_expects_rev:
        values['rev'] = g.rev


def _repo_url_value_preprocessor(endpoint, values):
    # TODO: Had a vague flash of insight into maybe checking endpoint expecting rev here and set repo.head.shorthand?
    g.repo_name = values.pop('repo_name', None)
    g.rev = values.pop('rev', None)


def _before_request_check_repo_and_rev():
    if not repo:
        flash(
            u'Repo with name "{}" not found'.format(g.repo_name),
            u'repo-404'
        )
        abort(404)

    if endpoint_expects_rev() and not repo.select_commit(g.rev):
        flash(
            u'Commit for rev "{}" in the "{}" repo not found'.format(g.rev, g.repo_name),
            u'repo-404'
        )
        abort(404)
