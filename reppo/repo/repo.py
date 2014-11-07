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

# from pygit2 import GIT_DIFF_IGNORE_WHITESPACE_EOL

from .blob import get_blob
from .diff import get_diff
from .commit import get_commit
from .tree import get_tree_entry
from .stats import get_language_stats


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

    def _object(self, commit, path):
        if path is None:
            return commit.tree
        path = path.strip('/')
        if path in commit.tree:
            return self.git.get(commit.tree[path].id, None)
        return None

    def _walk(self, commit=None, path=None, count=None):
        commit = commit or self.latest
        for c in self.git.walk(commit.id, GIT_SORT_TOPOLOGICAL):
            if path is not None:
                # stop because object is not in commit tree
                if path not in c.tree:
                    break
                parent = next(iter(c.parents), None)
                # yield and stop because this is the first commit that contains object
                # or this is the initial commit, so the object has always been here
                if parent is None or path not in parent.tree:
                    yield c
                    break
                # skip this iteration because object had no changes
                if c.tree[path].id == parent.tree[path].id:
                    continue
            yield c
            if count is not None:
                count -= 1
                if count <= 0:
                    break

    def revparse(self, rev):
        try:
            commit = self.git.revparse_single(rev)
        except (KeyError, TypeError):
            commit = None
        return commit

    def log(self, commit=None, path=None, skip=0, stop=1):
        for commit in islice(self._walk(commit, path), skip, skip + stop):
            yield get_commit(commit)

    def commit(self, commit=None, path=None):
        if path is not None:
            commit = next(self._walk(commit, path, 1), None)
        return get_commit(commit) if (commit is not None) else None

    def tree(self, commit=None, path=None):
        tree = self._object(commit, path)
        if isinstance(tree, Tree):
            for entry in sorted(tree, key=lambda e: self.git[e.id].type):
                yield get_tree_entry(self, commit, entry, path)

    def blob(self, commit, path):
        blob = self._object(commit, path)
        if isinstance(blob, Blob):
            return get_blob(blob, path)
        return None

    def diff(self, commit):
        parent = next(iter(commit.parents), None)
        if parent:
            diff = parent.tree.diff_to_tree(commit.tree)
            diff.find_similar()
        else:
            # If no parent, this must be an initial commit, and diff_to_tree does not accept None for its tree argument
            diff = commit.tree.diff_to_tree(swap=True)
        return get_diff(diff)

    def blame(self, commit, path):
        # TODO: Don't fully know how to work with this yet...
        # TODO: Also need to pass back the raw blame
        # TODO: "Newness heatmap"
        # Maybe use self.blob, since we may actually need formatting? or at least formatting of a different type
        blob = self._object(commit, path)
        blame = self.git.blame(path, newest_commit=commit.id)
        for hunk in blame:
            # Need next hunk to know when to stop
            # next_hunk = blame.next() ... etc
            from_line = hunk.final_start_line_number
            # Need author (name and date) and sha
            # Add hunk_commit to `seen_commits` (a set?) to avoid duplicate lookups (pointless optimization?)
            hunk_commit = self.git[hunk.final_commit_id]
        # for blame_hunk in blame:
        #     yield blame_hunk
        return blame

    def branches_for_commit(self, commit):
        # TODO: does not seem possible to look for branches from commit,
        #       unless you loop over *all* branches and iterate through
        #       each commit and check if commit.id == target_commit.id
        # for branch in self.branches:
        #     if self.git.lookup_branch(branch).target == commit.id:
        #         yield branch
        pass

    def contributors(self, commit=None, path=None):
        contributors = defaultdict(int)
        for commit in self._walk(commit, path):
            contributors[commit.author.name] += 1
        return Counter(contributors).most_common()

    def stats(self, commit=None, path=None):
        # TODO: add kwargs to restrict return value for specific things
        contributors = set()
        commits = 0

        for commit in self._walk(commit, path):
            contributors.add(commit.author.name)
            commits += 1

        return dict(
            commits=commits,
            branches=len(self.branches),
            tags=len(self.tags),
            contributors=len(contributors)
        )

    def lang_stats(self, commit=None):
        if commit is None:
            commit = self.latest
        return get_language_stats(self, commit)
