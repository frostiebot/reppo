# -*- coding: utf-8 -*-

import os

# from subprocess import check_output

from collections import defaultdict
from collections import Counter
from collections import OrderedDict

from itertools import islice

from dulwich.repo import Repo

from reppo.lib.util import get_commit
from reppo.lib.util import get_diff
from reppo.lib.util import get_tree
from reppo.lib.util import get_blob

from reppo.lib.util import _name_email

# from reppo.lib.util import force_unicode

# xs = 'lib/python/hotels/hotels/'.strip('/').split('/')
# ['/'.join(xs[0:i + 1]) for i in xrange(len(xs))]
# ['lib', 'lib/python', 'lib/python/hotels', 'lib/python/hotels/hotels']

# for r in [key] + ['/'.join((prefix, key)) for prefix in (self.REFS_HEADS, self.REFS_TAGS)]:
# for r in ('/'.join(filter(None, ref)) for ref in ((prefix, key) for prefix in (None, self.REFS_HEADS, self.REFS_TAGS))):


def lazy(fn):
    attr_name = '_'.join(('_lazy', fn.__name__))

    @property
    def _lazy(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)

    return _lazy


def name_repo(path):
    return path.replace('.git', '').rstrip(os.sep).split(os.sep)[-1]


class Reppo(object):
    REFS_HEADS, REFS_TAGS = 'refs/heads', 'refs/tags'

    def __init__(self, path, name=None):
        self.repo = Repo(path)
        self.name = name

        if name is None:
            self.name = name_repo(path)

        self._refish = lambda r: ('/'.join(filter(None, ref)) for ref in ((prefix, str(r)) for prefix in (None, self.REFS_HEADS, self.REFS_TAGS)))

    def __getitem__(self, key):
        return next((self.repo[r] for r in self._refish(key) if r in self.repo), None)

    def __contains__(self, item):
        for r in self._refish(item):
            if r in self.repo:
                return True
        return False

    def _ref_walker(self, ref_type):
        for ref in self.refs.iterkeys():
            if ref.startswith(ref_type):
                yield ref.replace(ref_type, '').lstrip('/')

    @lazy
    def refs(self):
        return OrderedDict(
            sorted(
                self.repo.refs.as_dict().iteritems(),
                key=lambda r: getattr(self.repo[r[1]], 'commit_time', None),
                reverse=True
            )
        )

    @lazy
    def head(self):
        return next(self.refs.itervalues(), None)

    @property
    def branches(self):
        return self._ref_walker(self.REFS_HEADS)

    @property
    def tags(self):
        return self._ref_walker(self.REFS_TAGS)

    @lazy
    def contributors(self):
        # TODO: This is VERY expensive operation. Validate need (currently a glorified count)
        contributors = defaultdict(int)

        for entry in self.repo.get_walker(include=[self.head], paths=[]):
            name = _name_email(entry.commit.author)[0]
            contributors[name] += 1

        return Counter(contributors).most_common()

    def get_repo_summary(self):
        # TODO: convert return dict to tuple?
        # TODO: allow passing `ref` to reflect accurate commit count for the given ref
        # TODO: count of commits needs to be made accurate for the current walker
        return dict(
            commits=sum(c for a, c in self.contributors),
            branches=sum(1 for b in self.branches),
            tags=sum(1 for t in self.tags),
            contributors=len(self.contributors)
        )

    def get_tree(self, ref, path):
        commit = self[ref]
        return get_tree(self.repo, commit, path)

    def get_blob(self, ref, path):
        commit = self[ref]
        return get_blob(self.repo, commit, path)

    def get_commit(self, ref, path=None):
        commit = self[ref]

        if path is None:
            path = []

        if not isinstance(path, list):
            path = [path]

        def _get_commit():
            for entry in self.repo.get_walker(include=[commit.id], paths=path, max_entries=1):
                yield get_commit(entry.commit)

        return next(_get_commit(), None)

    def get_diff(self, ref):
        commit = self[ref]
        return get_diff(self.repo, commit)

    def get_history(self, ref, path=None, skip=0, stop=1):
        # TODO: somehow prefer using max_entries param in get_walker rather than using islice
        commit = self[ref]

        if path is None:
            path = []

        if not isinstance(path, list):
            path = [path]

        for entry in islice(self.repo.get_walker(include=[commit.id], paths=path), skip, stop + skip):
            yield get_commit(entry.commit)
