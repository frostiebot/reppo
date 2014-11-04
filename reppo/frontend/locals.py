# -*- coding: utf-8 -*-

import inspect

from functools import partial

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

from flask import current_app
from flask import g

from werkzeug.local import LocalProxy

# TODO: Expensive to recreate each request... Store as root object and allow for select_commit

class RepoProxy(object):
    def __init__(self, repo):
        self._commit = None

        for name, attr in inspect.getmembers(repo):
            if not name.startswith('_'):
                _attr = attr
                if inspect.ismethod(attr):
                    argspec = inspect.getargspec(attr)
                    if 'commit' in argspec.args:
                        _attr = partial(attr, LocalProxy(lambda: self._commit))
                setattr(self, name, _attr)

    def select_commit(self, rev):
        commit = self.revparse(rev)
        if commit is not None:
            self._commit = commit
            return True
        return False


def _get_repo_proxy():
    ctx = stack.top
    if current_app and not hasattr(ctx, '_repo'):
        repo = current_app.config.get('REPOS', {}).get(g.repo_name, None)
        proxy = None
        if repo is not None:
            proxy = RepoProxy(repo)
        ctx._repo = proxy
    return getattr(ctx, '_repo', None)

repo = LocalProxy(lambda: _get_repo_proxy())
