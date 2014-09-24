# -*- coding: utf-8 -*-

import re

import locale

from collections import namedtuple

from datetime import datetime
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

# from dulwich.patch import write_object_diff
from dulwich.patch import write_tree_diff
# from dulwich.patch import is_binary

from reppo.lib.diff import prepare_udiff

ELL = u'…'
SIGNED_OFF_BY_RE = re.compile(r'.*Signed-off-by:\s+(.*)\s+<(.*)>\n$')
AUTHOR_NAME_EMAIL_RE = re.compile(r'^(.*)<(.*)>$')

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


def is_sha(sha):
    return isinstance(sha, basestring) and len(sha) == 40


# def dict_diff(object_store, old, new):
#     udiff = prepare_udiff(
#         object_diff(object_store, old, new),
#         want_header=False
#     )
#     return next(iter(udiff), None)


# def object_diff(*args, **kwargs):
#     fd = StringIO()
#     write_object_diff(fd, *args, **kwargs)
#     return fd.getvalue()


# def changes_tree_diff(object_store, old_tree, new_tree):
#     return object_store.tree_changes(old_tree, new_tree)


def commit_name_email(commit_author, pattern=None):
    if pattern is None:
        pattern = AUTHOR_NAME_EMAIL_RE

    try:
        m = re.search(pattern, commit_author)
        if m:
            name, email = m.groups()
    except:
        name = commit_author
        email = ''

    return name.strip(), email.strip()


def contributor_from_raw(raw_contributor, pattern=None):
    name, email = commit_name_email(raw_contributor, pattern)
    return Contributor(name, email, raw_contributor)


def message_from_raw(raw_message):
    # !!! TODO: 'Signed-off-by: ...' can appear multiple times!
    message = re.sub(SIGNED_OFF_BY_RE, u'', raw_message)

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


def get_commit_metadata(commit):
    author = contributor_from_raw(commit.author)
    committer = contributor_from_raw(commit.committer)
    # signer = contributor_from_raw(commit.message, SIGNED_OFF_BY_RE)
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


def get_commit_diff(repo, commit):
    fd = StringIO()

    oldtree = repo[commit.parents[0]].tree if commit.parents else None
    newtree = commit.tree

    write_tree_diff(fd, repo.object_store, oldtree, newtree)

    # udiff = prepare_udiff(fd.getvalue(), want_header=True)
    # headers = list(h for h in udiff if h.get('is_header') is True)
    # print headers

    return prepare_udiff(fd.getvalue(), want_header=True)


# def get_commit_diff(repo, commit):
#     oldtree = repo[commit.parents[0]].tree if commit.parents else None
#     newtree = commit.tree

#     object_store = repo.object_store

#     changes = []

#     for (oldpath, newpath), (oldmode, newmode), (oldsha, newsha) in changes_tree_diff(object_store, oldtree, newtree):
#         oldinfo = (oldpath, oldmode, oldsha)
#         newinfo = (newpath, newmode, newsha)

#         change = dict(
#             diffs=None,
#             old=dict(zip(('path', 'mode', 'sha'), oldinfo)),
#             new=dict(zip(('path', 'mode', 'sha'), newinfo)),
#             additions=0,
#             deletions=0
#         )

#         if not any(sha and sha in repo and is_binary(repo[sha].data) for sha in (newsha, oldsha)):
#             diff = dict_diff(object_store, oldinfo, newinfo)

#             if diff is not None:
#                 change['chunks'] = diff.get('chunks', [])
#                 change['additions'] = diff.get('additions', 0)
#                 change['deletions'] = diff.get('deletions', 0)

#         # print change
#         changes.append(change)

#     return changes


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
