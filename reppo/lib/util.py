# -*- coding: utf-8 -*-

import re

import locale

from collections import namedtuple

from datetime import date

from textwrap import wrap

try:
    import chardet
except ImportError:
    chardet = None

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from dulwich.object_store import tree_lookup_path

from dulwich.patch import write_tree_diff

from reppo.lib.diff import prepare_udiff

ELL = u'…'
# SIGNED_OFF_BY_RE = re.compile(r'.*Signed-off-by:\s+(.*)\s+<(.*)>\n$')

Contributor = namedtuple('Contributor', 'name email raw')
Message = namedtuple('Message', 'summary description raw_summary raw_description')


class Commit(namedtuple('Commit', 'id parents author committer author_time commit_time message')):
    __slots__ = ()

    @property
    def commit_date(self):
        return date.fromtimestamp(self.commit_time)

    @property
    def author_date(self):
        return date.fromtimestamp(self.author_time)


class Diff(namedtuple('Diff', 'changes')):
    __slots__ = ()

    @property
    def files(self):
        return sum(1 for c in self.changes if not c.get('is_header'))

    def _counter(self, count_type):
        return sum(c.get(count_type, 0) for c in self.changes)

    @property
    def additions(self):
        return self._counter('additions')

    @property
    def deletions(self):
        return self._counter('deletions')


class Tree(namedtuple('Tree', 'path sha type')):
    __slots__ = ()

    @property
    def name(self):
        return self.path.rsplit('/', 1)[-1]


def _name_email(text):
    (name, email) = text.rsplit(' <', 1)
    return (name, email.rstrip('>'))


def contributor_from_raw(raw_contributor):
    name, email = _name_email(raw_contributor)
    return Contributor(name, email, raw_contributor)


def message_from_raw(raw_message):
    # TODO: 'Signed-off-by: ...' can appear multiple times!
    # TODO: think harder about whether or not we want to simply remove signed-off-by or make it an attribute of the commit/author

    # message = re.sub(SIGNED_OFF_BY_RE, u'', raw_message)
    message = raw_message

    lines = iter(message.split(u'\n\n', 1))
    raw_summary = lines.next().rstrip()

    summary_lines = wrap(raw_summary, width=70, replace_whitespace=False)
    description_lines = list(lines)
    raw_description = u''.join(description_lines)

    summary = summary_lines.pop(0).rstrip()

    if len(summary_lines):
        summary = u''.join((summary.rstrip(), ELL))
        description_lines.insert(0, u''.join((ELL, u''.join(summary_lines))))

    description = u'\n\n'.join(description_lines).rstrip()

    return Message(summary, description, raw_summary, raw_description)


def _object_lookup_path(repo, obj, path):
    if path is not None:
        obj = tree_lookup_path(repo.get_object, obj, path)[1]
    return repo[obj]


def get_commit(commit):
    author = contributor_from_raw(commit.author)
    committer = contributor_from_raw(commit.committer)
    message = message_from_raw(commit.message)

    return Commit(
        commit.id,
        commit.parents,
        author,
        committer,
        commit.author_time,
        commit.commit_time,
        message
    )


def get_diff(repo, commit):
    fd = StringIO()

    oldtree = repo[commit.parents[0]].tree if commit.parents else None
    newtree = commit.tree

    print oldtree
    print newtree

    write_tree_diff(fd, repo.object_store, oldtree, newtree)

    # udiff = prepare_udiff(fd.getvalue(), want_header=True)
    # headers = list(h for h in udiff if h.get('is_header') is True)
    # print headers

    changes = prepare_udiff(fd.getvalue(), want_header=True)

    return Diff(changes)


def get_tree(repo, commit, path=None):
    # TODO: verify isinstance(tree, dulwich.objects.Tree)
    # TODO: Oh boy. Use get_walker for each TreeEntry to add the last commit + commit time
    tree = _object_lookup_path(repo, commit.tree, path)

    for entry in sorted(tree.iteritems(), key=lambda e: repo[e.sha].type):
        yield Tree(
            '/'.join(filter(None, [path, entry.path])),
            entry.sha,
            repo[entry.sha].type_name
        )


def get_blob(repo, commit, path):
    # TODO: verify isinstance(blob, dulwich.object.Blob)
    return _object_lookup_path(repo, commit.tree, path)


def force_unicode(s):
    """ Does all kind of magic to turn `s` into unicode """
    # It's already unicode, don't do anything:
    if isinstance(s, unicode):
        return s

    # Try some default encodings:
    try:
        return s.decode('utf-8')
    except UnicodeDecodeError as exc:
        pass
    try:
        return s.decode(locale.getpreferredencoding())
    except UnicodeDecodeError:
        pass

    if chardet is not None:
        # Try chardet, if available
        encoding = chardet.detect(s)['encoding']
        if encoding is not None:
            return s.decode(encoding)

    raise exc  # Give up.
