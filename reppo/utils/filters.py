# -*- coding: utf-8 -*-

import re

from datetime import datetime

from flask import Markup

from flask import url_for

NOW = datetime.now()

JIRA_PROJECT_TICKET_RE = re.compile(r'''
    (?P<jira>
        (?P<project>
            \b[a-z]{2,4}
        )
        [_|-]*
        (?P<ticket>
            \d+
        )
    )
    ''', re.IGNORECASE | re.VERBOSE)


def is_sha(sha):
    return isinstance(sha, basestring) and len(sha) == 40


def normalizepath(path):
    ''' expects some kind of iterable or sequence. Please be sensible.'''
    return u'/'.join(*filter(None, path))


def pathwalk(path):
    path = path.strip(u'/').split(u'/')
    for i in xrange(len(path)):
        yield path[i], '/'.join(path[0:i + 1])


def parentpath(path):
    return u'/'.join(path.strip(u'/').split(u'/')[0:-1])


def formatdate(dt, force_year=False):
    pattern = '%b %-d'
    if (dt.year != NOW.year) or force_year:
        pattern += ', %Y'
    return dt.strftime(pattern)


def isoformattimestamp(ts):
    return datetime.fromtimestamp(ts).isoformat()


def formatnumber(d):
    return u'{:,}'.format(d)


def shortsha(sha, l=7):
    if is_sha(sha):
        return sha[:l]
    return sha


def jiralink(message, sha=None, title=None):
    jira_link = r'''<a class="jira-link" href="https://tablet.atlassian.net/browse/\g<project>-\g<ticket>">\g<project>-\g<ticket></a>'''

    if sha is not None:
        jira_link = r'''</a>{}<a href="{}" title="{}">'''.format(
            jira_link,
            url_for('repo.commit', sha=sha),
            title if title else ''
        )

    return Markup(re.sub(
        JIRA_PROJECT_TICKET_RE,
        lambda m: m.expand(jira_link),
        message
    ))
