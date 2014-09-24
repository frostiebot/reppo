# -*- coding: utf-8 -*-

import os

from subprocess import check_output

from collections import defaultdict
from collections import Counter
from collections import OrderedDict

from itertools import islice

from dulwich.repo import Repo as DRepo

from reppo.lib.util import commit_name_email
from reppo.lib.util import get_commit_metadata
from reppo.lib.util import get_commit_diff

from reppo.lib.util import force_unicode


class Repo(DRepo):
    REFS_HEADS = 'refs/heads'
    REFS_TAGS = 'refs/tags'

    @property
    def name(self):
        return Repo.get_name(self.path)

    @staticmethod
    def get_name(path):
        return path.replace('.git', '').rstrip(os.sep).split(os.sep)[-1]

    def get_description(self):
        description = super(Repo, self).get_description()
        if description:
            if not description.startswith('Unnamed repository;'):
                return force_unicode(description)

    @property
    def branches(self):
        return self.get_refs(self.REFS_HEADS).iterkeys()

    @property
    def tags(self):
        return self.get_refs(self.REFS_TAGS).iterkeys()

    def _format_ref(self, *paths):
        return '/'.join(filter(None, paths))

    def _format_ref_branch(self, branch):
        return self._format_ref(self.REFS_HEADS, branch)

    def _format_ref_tag(self, tag):
        return self._format_ref(self.REFS_TAGS, tag)

    def _get_commit_from_ref(self, ref):
        return self[ref] if ref in self else None

    def _get_commit_from_branch(self, branch):
        ref = self._format_ref_branch(branch)
        return self._get_commit_from_ref(ref)

    def _get_commit_from_tag(self, tag):
        ref = self._format_ref_tag(tag)
        return self._get_commit_from_ref(ref)

    def _get_commit(self, ref):
        ref = str(ref)
        for fn in (self._get_commit_from_ref, self._get_commit_from_branch, self._get_commit_from_tag):
            commit = fn(ref)
            if commit is not None:
                break
        return commit

    def get_refs(self, prefix=None, sort='commit_time'):
        # sort can also be 'author_time'
        return OrderedDict(
            sorted(
                self.refs.as_dict(prefix).iteritems(),
                key=lambda r: getattr(self[r[1]], sort, None),
                reverse=True
            )
        )

    def commit_walker(self, ref, path=None):
        commit = self._get_commit(ref)
        path = [path] if path else []
        for entry in self.get_walker(include=commit.id, paths=path):
            yield entry.commit

    def history(self, ref, path=None, skip=0, stop=1):
        for commit in islice(self.commit_walker(ref, path), skip, stop + skip):
            yield get_commit_metadata(commit)

    def latest(self, ref, path=None):
        return next(self.history(ref, path, 0, 1), None)

    def get_object(self, sha, path):
        ''' Return either a proper `dulwich.objects.Blob` in the case
            of viewing a file-like object, or a iterable list of pre-sorted
            dicts that represent the directory structure of the commit
            from the path specified

            We play fast and loose with dulwich' types, knowing that a
            type of 3 is a `dulwich.objects.Blob` (a file or file-like thing)
            and 2 is a `dulwich.objects.Tree`, a container that could
            hold yet more Tree and Blob objects.
        '''
        commit = self._get_commit(sha)
        obj = self[commit.tree]

        if path is not None:
            for pth in path.strip('/').split('/'):
                if obj.type == 3:  # 3 iz Blob!
                    break
                obj = self[obj[pth][1]]

        if obj.type == 2:
            return iter(
                {
                    'name': entry.path,
                    'sha': entry.sha,
                    'path': os.path.join(path, entry.path) if path else entry.path,
                    'type': self[entry.sha].type_name
                }
                for entry in
                sorted(obj.items(), key=lambda e: self[e.sha].type)
            )

        return obj

    def summary_for_ref(self, ref):
        return dict(
            commits=self.commit_count(ref),
            branches=sum(1 for b in self.branches),
            tags=sum(1 for t in self.tags),
            contributors=len(self.contributors())
        )

    def commit_count(self, ref):
        return sum(1 for c in self.commit_walker(ref))

    def commit_info(self, sha):
        commit = self._get_commit(sha)
        changes = get_commit_diff(self, commit)

        summary = dict(
            files=sum(1 for c in changes if not c.get('is_header')),
            additions=sum(c.get('additions', 0) for c in changes),
            deletions=sum(c.get('deletions', 0) for c in changes)
        )

        return get_commit_metadata(commit), summary, changes

    def contributors(self):
        # sha = self.latest(self.branches.next(), None).id
        # contributors = defaultdict(int)
        # for commit in self.commit_walker(sha):
        #     name, _ = commit_name_email(commit.author)
        #     contributors[name] += 1
        # return Counter(contributors).most_common()

        cmd = ['git', 'shortlog', '-sn', self.branches.next()]
        output = check_output(cmd, cwd=os.path.abspath(self.path))
        return list(
            c[1] for c in sorted(
                (tuple(o.split('\t')) for o in output.strip().split('\n')),
                key=lambda r: r[0],
                reverse=True
            )
        )

    def branches_for_commit(self, sha):
        #TODO: This can return too many branches in probably a lot of cases. Best to cut down the # of branches.
        commit = self._get_commit(sha)
        cmd = ['git', 'branch', '--contains', commit.id]
        output = check_output(cmd, cwd=os.path.abspath(self.path))
        return output.strip().split('\n')
