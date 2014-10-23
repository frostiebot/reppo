# -*- coding: utf-8 -*-

import re

from datetime import datetime

from flask import Markup

from flask import url_for

NOW = datetime.now()

OID_RE = re.compile(r'''[a-fA-F0-9]{40}''', re.I)

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


def init_repo_template_filters(blueprint):
    for fn in (issha, jiralink, pathwalk, formatnumber, shortsha, formatdate, parentpath):
        blueprint.add_app_template_filter(fn)


def issha(rev):
    return OID_RE.match(rev)


def pathwalk(path):
    path = path.strip(u'/').split(u'/')
    for i in xrange(len(path)):
        yield path[i], u'/'.join(path[0:i + 1])


def parentpath(path):
    # works with single dir in path, but our paths always have no leading /
    # return path.rstrip(u'/').rsplit(u'/', 1)[0].strip(u'/')
    return u'/'.join(path.strip(u'/').split(u'/')[0:-1])


def formatdate(dt, force_year=False):
    pattern = '%b %-d'
    if (dt.year != NOW.year) or force_year:
        pattern += ', %Y'
    return dt.strftime(pattern)


def formatnumber(d):
    return u'{:,}'.format(d)


def shortsha(sha, l=7):
    if not isinstance(sha, basestring):
        sha = sha.hex
    if issha(sha):
        return sha[:l]
    return sha


def jiralink(message, rev=None, title=None):
    jira_link = r'''<a class="jira-link" href="https://tablet.atlassian.net/browse/\g<project>-\g<ticket>">\g<project>-\g<ticket></a>'''

    if rev is not None:
        jira_link = r'''</a>{}<a href="{}" title="{}">'''.format(
            jira_link,
            url_for('repo.commit', rev=rev),
            title if title else ''
        )

    return Markup(re.sub(
        JIRA_PROJECT_TICKET_RE,
        lambda m: m.expand(jira_link),
        message
    ))
