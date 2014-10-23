# -*- coding: utf-8 -*-

from flask import current_app
from flask import g

from werkzeug.local import LocalProxy


def _get_repo_from_name():
    if '_current_repo' not in g:
        g._current_repo = current_app.config['REPOS'].get(g.repo_name, None)
    return g._current_repo


def _get_commit_from_rev():
    if '_current_commit' not in g:
        g._current_commit = current_repo.revparse(g.rev)
    return g._current_commit

current_repo = LocalProxy(_get_repo_from_name)
current_commit = LocalProxy(_get_commit_from_rev)
