# -*- coding: utf-8 -*-

'''
git log --pretty="format:%at commit %C(yellow)%H%Creset\nAuthor: %an <%ae>\nDate: %aD\n\n %s\n" | sort -r | cut -d" " -f2- | sed -e "s/\\\n/\\`echo -e '\n\r'`/g" | tr -d '\15\32' | less -R

git log --pretty="format:%at commit %C(yellow)%H%Creset\nAuthor: %an <%ae>\nDate: %aD\n\n %s\n" ready_lmt_152 | sort -r | cut -d" " -f2- | sed -e "s/\\\n/\\`echo -e '\n\r'`/g" | tr -d '\15\32' | less -R
'''

import re

from datetime import datetime

from flask import Flask

from flask import Markup

from flask import g
from flask import render_template
from flask import redirect
from flask import request
from flask import url_for

from reppo import Reppo
from reppo.util import is_sha
from reppo.util import JIRA_PROJECT_TICKET_RE

app = Flask('reppo')

reppo = Reppo('/home/chris/hosted/klaus/tablet.git')

SITE_NAME = 'Reppo!'

NOW = datetime.now()

AUTHORS_JIRANAMES = {
    'Lucidchart': 'addon_lucidchart-app',
    'Aiko Ishikawa': 'aiko',
    'Alexander Ginzburg': 'alex.ginzburg',
    'Alia Connor': 'alia',
    'Andrew Pelimsky': 'andrew.pelimsky',
    'Ari Amanatidis': 'ari',
    'Ash Coleman': 'ash.coleman',
    'Austin Robinson': 'austin',
    'Axel Anderson': 'axel',
    'Ayaka Morohoshi': 'ayaka',
    'Baba Awumbila': 'baba.awumbila',
    'Brian Harney': 'brian.harney',
    'catherine': 'catherine',
    'Chris Ashurst': 'chris.ashurst',
    'Customer Service': 'cs',
    'Daniel Lasaga': 'daniel.lasaga',
    'Dan Kwok': 'dan.kwok',
    'Dante Nolleau': 'dante',
    'Daren Grisham': 'daren',
    'Eamon Banta': 'eamon',
    'Erika Suban': 'erika',
    'Garrett Kinnison': 'garrett',
    'Geoff Rice': 'geoff.rice',
    'Greg Patmore': 'greg',
    'Henry Mendez': 'henry',
    'Hoa Mai': 'hoa.mai',
    'hotelgroup': 'hotelgroup',
    'Ivan Contreras': 'icontreras',
    'Jacob Yuan': 'jacob',
    'John Speranza': 'john',
    'Josh Cotton': 'josh',
    'julie': 'julie',
    'Laurent': 'laurent',
    'Lindsey Gothelf': 'LGothelf',
    'Manja Paschek': 'manja',
    'Mark Fedeli': 'mark',
    'Michael Frankel': 'mfrankel',
    'Michael Davis': 'michael.davis',
    'Mobients': 'mobient',
    'Mike Parker': 'mparker',
    'Matt Petroziello': 'mpetroziello',
    'Nelly Liebrecht': 'nelly',
    'Nick Schwartzmyer': 'nick.schwartzmyer',
    'nobody-lightside': 'nobody',
    'nobody-darkside': 'nobody-darkside',
    'Paulo Grillo': 'paulo',
    'Peng Chia': 'peng',
    'Ron Shi': 'ron',
    'Sam Newbold': 'sam.newbold',
    'Sharanya Venkatasubramanian': 'sharanya',
    'System Administrator': 'sysadmin',
    'Thi Vu': 'thi.vu',
    'Tiffany Nguyen': 'tiffany',
    'Tony Hau': 'tony.hau',
    'translators': 'translators',
    'Triage Me': 'Triage',
    'Tyler Neely': 'tyler.neely',
    'unassigned': 'unassigned',
    'Valeska Holme': 'valeska',
    'Valli Ravindran': 'valli.ravindran',
    'Xiaoyi Liu': 'xiaoyi'
}

REPOS = dict((repo.name, repo) for repo in [reppo])


@app.url_defaults
def set_repo_in_url(endpoint, values):
    # if 'repo' not in values and 'repo' in g.repo:
    #     values['repo'] = g.repo.name
    if 'repo' in values or not g.repo:
        return
    if app.url_map.is_endpoint_expecting(endpoint, 'repo'):
        values['repo'] = g.repo.name


@app.url_value_preprocessor
def pull_repo_from_url(endpoint, values):
    g.repo = REPOS.get(values.pop('repo', None), None)


@app.context_processor
def inject_site_globals():
    return dict(
        SITE_NAME=SITE_NAME,
        JIRA_AVATARS=AUTHORS_JIRANAMES
    )


@app.template_filter()
def formatdate(dt, force_year=False):
    pattern = '%b %-d'
    if (dt.year != NOW.year) or force_year:
        pattern += ', %Y'
    return dt.strftime(pattern)


@app.template_filter()
def shortsha(sha, l=7):
    if is_sha(sha):
        return sha[:l]
    return sha


@app.template_filter()
def thousands(d):
    return '{:,}'.format(d)


@app.template_filter()
def jiralink(message, sha=None):
    # !!! TODO: Move bulk of this code into reppo app utils (not reppo repo utils)
    jira_link = r'''<a class="jira-link"href="https://tablet.atlassian.net/browse/\g<project>-\g<ticket>">\g<project>-\g<ticket></a>'''

    if sha is not None:
        jira_link = r'''</a>{}<a href="{}">'''.format(
            jira_link,
            url_for('commit', ref=sha)
        )

    return Markup(re.sub(
        JIRA_PROJECT_TICKET_RE,
        lambda m: m.expand(jira_link),
        message
    ))


@app.route('/')
def index():
    # !!! TODO: This will be a list at some point, I guess.
    return redirect(url_for('tree', repo='tablet'))


# !!! TODO: Why doesn't auto-appending of trailing slash work
#           here? Some sort of garbage with url preprocesing? Dump it?
@app.route('/<repo>/')
@app.route('/<repo>/tree/<ref>/')
@app.route('/<repo>/tree/<ref>/<path:path>')
def tree(ref=None, path=None):
    if ref is None:
        ref = g.repo.default_branch()

    commit = g.repo.get_commit(ref)
    tree = g.repo.get_tree_or_blob(commit, path)
    latest = g.repo.history(commit.id, path=path, stop=1)

    # !!! TODO: This is rough :/
    parent = None
    if path is not None:
        parent = '/'.join(path.strip('/').split('/')[:-1])

    return render_template(
        'tree.html',
        ref=ref,
        commit=commit,
        latest=latest.next(),
        tree=tree,
        parent=parent,
    )


@app.route('/<repo>/<any(branches, tags):ref_type>/')
def branches_or_tags(ref_type):
    refs = getattr(g.repo, ref_type, None)

    redirect_to_tree = redirect(url_for('tree'))

    if refs is None:
        return redirect_to_tree

    try:
        default_ref = refs.next()
    except StopIteration:
        return redirect_to_tree

    return render_template(
        'refs.html',
        ref_type=ref_type,
        default_ref=default_ref,
        refs=refs
    )


# !!! TODO: Make this real - remove history stuff from commit route
@app.route('/<repo>/commits/<ref>/')
def commits(ref=None):
    if ref is None:
        ref = g.repo.default_branch()

    commit = g.repo.get_commit(ref)

    try:
        page = int(request.args.get('page', 0))
    except ValueError:
        page = 0

    context_page = page
    previous_pages = None

    if page:
        history_length = 30
        skip = (context_page - 1) * 30 + 30

        if page > 7:
            previous_pages = [0, 1, 2, None] + range(page)[-3:]
        else:
            previous_pages = xrange(page)
    else:
        history_length = 30
        skip = 0

    history = g.repo.history(commit.id, skip=skip, stop=history_length + 1)

    return render_template(
        'history.html',
        ref=ref,
        commit=commit,
        history=history,
        page=context_page,
        previous_pages=previous_pages,
        more_commits=True
    )


@app.route('/<repo>/commit/<ref>/')
def commit(ref=None):
    if ref is None:
        return redirect(url_for('show_tree'))

    commit = g.repo.get_commit(ref)
    summary, changes = g.repo.summary_changes_for_commit(commit)
    commit = g.repo.info_for_commit(commit)
    branches = None  # g.repo.branches_with_commit(ref)

    return render_template(
        'commit.html',
        ref=ref,
        commit=commit,
        summary=summary,
        changes=changes,
        branches=branches
    )


# @app.route('/raw/<ref>/<path:path>')
@app.route('/<repo>/blob/<ref>/<path:path>')
def blob(ref, path):
    commit = g.repo.get_commit(ref)
    blob = g.repo.get_tree_or_blob(commit, path)
    return '%s :: %s' % (ref, blob)

if __name__ == '__main__':
    app.run(debug=True)
