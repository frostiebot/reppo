# -*- coding: utf-8 -*-

from flask import _app_ctx_stack
from flask import current_app
from flask import g

from werkzeug.local import LocalProxy

from reppo.repo.extensions import RepoProxy


def _get_repo_proxy():
    top = _app_ctx_stack.top

    if not hasattr(top, 'repo'):
        repo_name = g.get('repo_name', None)
        rev = g.get('rev', None)

        if repo_name is not None:
            repo = current_app.config['REPOS'].get(repo_name, None)
            if repo is not None:
                top.repo = RepoProxy(repo, rev)

    return top.repo

repo_proxy = LocalProxy(_get_repo_proxy)
