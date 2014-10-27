# -*- coding: utf-8 -*-

import inspect

from functools import partial

from werkzeug.local import LocalProxy


class RepoProxy(object):
    '''
    from reppo.lib.repo import Repo
    from reppo.repo.locals import RepoProxy
    repo = Repo('/home/chris/hosted/reppo/tablet.git')
    x = RepoProxy(repo, 'ready_lmt_152')
    '''
    def __init__(self, repo, rev):
        self.rev = rev

        self._commit = repo.revparse(rev)

        for name, method in inspect.getmembers(repo, predicate=inspect.ismethod):
            argspec = inspect.getargspec(method)

            if 'commit' in argspec.args and not name.startswith('_'):
                proxied_repo_method = partial(method, LocalProxy(lambda: self._commit))
                setattr(self, name, proxied_repo_method)
