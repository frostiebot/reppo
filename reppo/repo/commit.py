# -*- coding: utf-8 -*-

from collections import namedtuple

from datetime import date

from textwrap import wrap


ELL = u'…'
# SIGNED_OFF_BY_RE = re.compile(r'.*Signed-off-by:\s+(.*)\s+<(.*)>\n$')

Message = namedtuple('Message', 'summary description raw_summary raw_description')

Signature = namedtuple('Signature', 'email raw_email name raw_name time offset')


class Commit(namedtuple('Commit', 'id parents author committer author_time commit_time message')):
    __slots__ = ()

    @property
    def commit_date(self):
        return date.fromtimestamp(self.commit_time)

    @property
    def author_date(self):
        return date.fromtimestamp(self.author_time)


def _message_from_raw(raw_message):
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
    message = _message_from_raw(commit.message)

    return Commit(
        commit.hex,
        commit.parent_ids,
        commit.author,
        commit.committer,
        commit.author.time,
        commit.committer.time,
        message
    )
