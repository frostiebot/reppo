# -*- coding: utf-8 -*-

import re

from collections import Counter
from collections import defaultdict

from itertools import islice

from pygit2 import Repository

from pygit2 import Blob
from pygit2 import Tree

from pygit2 import GIT_SORT_TOPOLOGICAL
# from pygit2 import GIT_SORT_REVERSE
# from pygit2 import GIT_SORT_TIME
# from pygit2 import GIT_SORT_NONE

from reppo.lib.diff import process_diff

from reppo.lib.util import get_commit
from reppo.lib.util import get_tree_entry


def lazy(fn):
    attr_name = '_'.join(('_lazy', fn.__name__))

    @property
    def _lazy(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)

    return _lazy


class Repo(object):
    def __init__(self, path):
        self.git = Repository(path)

    @property
    def head(self):
        return self.git.head

    @lazy
    def latest(self):
        return self.git.get(self.git.head.target)

    @lazy
    def branches(self):
        return self.git.listall_branches()

    @lazy
    def tags(self):
        _re_tags = re.compile(r'^refs/tags/')
        return filter(lambda r: _re_tags.match(r), self.git.listall_references())

    @lazy
    def contributors(self):
        contributors = defaultdict(int)
        for commit in self._walk(self.latest):
            contributors[commit.author.name] += 1
        return Counter(contributors).most_common()

    def _object_from_path(self, commit, path):
        if path is None:
            return commit.tree
        path = path.strip('/')
        obj = None
        if path in commit.tree:
            obj = self.git.get(commit.tree[path].id, None)
        return obj

    def _object(self, commit, path, object_type):
        obj = self._object_from_path(commit, path)
        if not isinstance(obj, object_type):
            return None
        return obj

    def _walk(self, commit=None, paths=None):
        # TODO: Recreate situation that caused the WHAT IS THIS? comment
        if commit is None:
            commit = self.latest

        if paths is not None:
            if isinstance(paths, basestring):
                paths = [paths]

        for commit in self.git.walk(commit.id, GIT_SORT_TOPOLOGICAL):
            if paths:
                parent = next(iter(commit.parents), None)

                for path in paths:
                    a = self._object_from_path(commit, path)
                    if parent is None:
                        if a:
                            break
                    else:
                        b = self._object_from_path(parent, path)
                        # WHAT IS THIS?
                        if not b:
                            break
                        if a.id != b.id:
                            break
                else:
                    continue

            yield commit

    def stats(self, commit=None):
        return dict(
            commits=sum(1 for c in self._walk(commit or self.latest)),
            branches=len(self.branches),
            tags=len(self.tags),
            contributors=len(self.contributors)
        )

    def log(self, commit=None, path=None, skip=0, stop=1):
        for commit in islice(self._walk(commit, path), skip, skip + stop):
            yield get_commit(commit)

    def commit(self, commit=None, path=None):
        return next(self.log(commit, path), None)

    def tree(self, commit=None, path=None):
        tree = self._object(commit, path, Tree)

        if tree is None:
            yield None

        for entry in sorted(tree, key=lambda e: self.git[e.id].type):
            yield get_tree_entry(self, commit, entry, path)

    def blob(self, commit=None, path=None):
        return self._object(commit, path, Blob)

    def diff(self, commit):
        parent = next(iter(commit.parents), None)

        new_tree = commit.tree
        old_tree = parent.tree if parent else None

        if new_tree and old_tree:
            diff = old_tree.diff_to_tree(new_tree)
            # html = prepare_udiff(diff.patch, want_header=False)

            # return list(patch for patch in diff), html
            return process_diff(diff)

        return None

    def blame(self, commit, path):
        # TODO: Don't fully know how to work with this yet...
        # TODO: Need blob - match blob lines with BlameHunk lines, I guess
        # >>> dir(blame_hunk)
        # ['__class__', '__delattr__', '__dict__', '__doc__', '__format__', '__getattribute__', '__hash__', '__init__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_blame', '_from_c', '_hunk', 'boundary', 'final_commit_id', 'final_committer', 'final_start_line_number', 'lines_in_hunk', 'orig_commit_id', 'orig_committer', 'orig_path', 'orig_start_line_number']
        blame = self.git.blame(path, newest_commit=commit.id)
        # for blame_hunk in blame:
        #     yield blame_hunk
        return blame
