# -*- coding: utf-8 -*-

from collections import namedtuple

from datetime import date

from textwrap import wrap

# from flask import Markup

# from pygit2 import GIT_FILEMODE_BLOB as BLOB
# from pygit2 import GIT_FILEMODE_BLOB_EXECUTABLE as BLOB_EXECUTABLE
# from pygit2 import GIT_FILEMODE_COMMIT as COMMIT
from pygit2 import GIT_FILEMODE_LINK as SYMLINK
# from pygit2 import GIT_FILEMODE_NEW as NEW
# from pygit2 import GIT_FILEMODE_TREE as TREE


ELL = u'…'
# SIGNED_OFF_BY_RE = re.compile(r'.*Signed-off-by:\s+(.*)\s+<(.*)>\n$')

Message = namedtuple('Message', 'summary description raw_summary raw_description')


class Commit(namedtuple('Commit', 'id parents author committer author_time commit_time message')):
    __slots__ = ()

    @property
    def commit_date(self):
        return date.fromtimestamp(self.commit_time)

    @property
    def author_date(self):
        return date.fromtimestamp(self.author_time)


class TreeEntry(namedtuple('TreeEntry', 'path sha type_id mode')):
    __slots__ = ()

    @property
    def name(self):
        return self.path.rsplit('/', 1)[-1]

    @property
    def type(self):
        return 'tree' if self.type_id == 2 else 'blob'

    @property
    def is_symlink(self):
        return self.mode == SYMLINK


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


def get_commit(commit):
    author = commit.author
    committer = commit.committer
    message = message_from_raw(commit.message)

    return Commit(
        commit.hex,
        commit.parent_ids,
        author,
        committer,
        commit.author.time,
        commit.committer.time,
        message
    )


def get_tree_entry(repo, commit, entry, path):
    path = '/'.join(filter(None, [path, entry.name]))
    return TreeEntry(
        path,
        entry.hex,
        repo.git[entry.id].type,
        entry.filemode
    )


# def force_unicode(s):
#     """ Does all kind of magic to turn `s` into unicode """
#     # It's already unicode, don't do anything:
#     if isinstance(s, unicode):
#         return s

#     # Try some default encodings:
#     try:
#         return s.decode('utf-8')
#     except UnicodeDecodeError as exc:
#         pass
#     try:
#         return s.decode(locale.getpreferredencoding())
#     except UnicodeDecodeError:
#         pass

#     if chardet is not None:
#         # Try chardet, if available
#         encoding = chardet.detect(s)['encoding']
#         if encoding is not None:
#             return s.decode(encoding)

#     raise exc  # Give up.
