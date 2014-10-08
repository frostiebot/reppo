# -*- coding: utf-8 -*-

from flask import Blueprint
from flask import Response

from flask import abort
from flask import current_app
from flask import flash
from flask import g
from flask import get_flashed_messages
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

# from magic import from_buffer as magic_from_buffer

from reppo.lib.highlight import pygmentize

from reppo.utils.pagination import Pagination

bp = Blueprint('repo', __name__, url_prefix='/<repo_key>')


@bp.url_value_preprocessor
def pull_repo_key(endpoint, values):
    g.repo_key = values.pop('repo_key', None)
    g.rev = values.pop('rev', None)


@bp.before_request
def get_repo_and_commit_for_request():
    repo = current_app.config['REPOS'].get(g.repo_key, None)

    if repo is None:
        flash(u'Repo with name "{}" not found'.format(g.repo_key), u'reppo-404')
        abort(404)

    if g.rev is None:
        g.rev = repo.head.shorthand

    try:
        commit = repo.git.revparse_single(g.rev)
    except KeyError:
        flash(u'Commit for rev "{}" in the "{}" repo not found'.format(g.rev, g.repo_key), u'repo-404')
        abort(404)

    g.commit = commit
    g.repo = repo


@bp.url_defaults
def add_repo_url_defaults(endpoint, values):
    values.setdefault('repo_key', g.repo_key)
    # values.setdefault('rev', g.rev)

    if 'rev' in values:
        return

    if current_app.url_map.is_endpoint_expecting(endpoint, 'rev'):
        values['rev'] = g.rev


@bp.context_processor
def inject_repo_template_globals():
    # TODO: Why does this even exist?
    return dict(
        SITE_NAME='reppo'
    )


@bp.context_processor
def inject_pagination_helper():
    def url_for_other_page(page):
        args = request.view_args.copy()
        args['page'] = page
        return url_for(request.endpoint, **args)
    return dict(url_for_other_page=url_for_other_page)


@bp.errorhandler(404)
def not_found(error):
    repo_before_request_messages = get_flashed_messages(category_filter=[u'repo-404'])
    message = u'Nope'
    if repo_before_request_messages:
        message = '\n'.join(repo_before_request_messages)
    return message, 404


@bp.route('/')
def no_tree_no_rev():
    return _redirect_to_tree()


@bp.route('/tree/')
def tree_no_rev():
    return _redirect_to_tree()


def _redirect_to_tree():
    return redirect(url_for('.tree'))


@bp.route('/tree/<rev>/')
@bp.route('/tree/<rev>/<path:path>')
def tree(path=None):
    # TODO: We know if a Blob or Tree is actually a symlink - decorate appropriately in template
    # TODO: format commit summary and commit date for per-object latest commit in template
    # TODO: tree should probably be a table due to latest commit now available
    # TODO: when path is not None show button to repo.commits at far right of breadcrumb
    # TODO: lang summary - will require walking tree completely and dumping file extensions into a set (or a defaultdict that gets passed to a Counter)
    summary = None

    if path is None:
        summary = g.repo.stats(g.commit)

    latest = g.repo.commit(g.commit, path)
    tree = g.repo.tree(g.commit, path)

    return render_template(
        'tree.html',
        latest=latest,
        summary=summary,
        tree=tree,
    )


@bp.route('/commits/<rev>')
@bp.route('/commits/<rev>/<path:path>')
def commits(path=None):
    # TODO: Make pagination cached in user session keyed by rev (pop last n revs)
    page = abs(request.args.get('page', 1, type=int))
    per_page = 30

    count = sum(1 for c in g.repo._walk(g.commit, path))
    skip = (page * per_page) - per_page

    pagination = Pagination(page, per_page, count)

    log = g.repo.log(g.commit, path=path, skip=skip, stop=per_page)

    return render_template(
        'commits.html',
        log=log,
        pagination=pagination
    )


@bp.route('/commit/<rev>')
def commit():
    # TODO: see if we can get branches for commit without explosions
    # TODO: add hunk shas to diff for additional resolution of a diff overall (not possible with pygit2?)
    commit = g.repo.commit(g.commit)
    diff = g.repo.diff(g.commit)
    branches = None  # g.repo.branches_for_commit(rev)

    return render_template(
        'commit.html',
        commit=commit,
        diff=diff,
        branches=branches
    )


@bp.route('/blob/<rev>/<path:path>')
def blob(path):
    # TODO: clean all this crap up
    # TODO: actually do something if file is binary
    # TODO: is_binary + is_possibly_an_image -> display image?
    # TODO: limit display if file too big?
    # TODO: use repo.walk to find contributors for entire history
    # TODO: link to 'history' - see history route
    commit = g.repo.commit(g.commit, path)
    blob = g.repo.blob(g.commit, path)

    # Nope. Don't know why.
    # contributors = set()
    # for c in g.repo._walk(g.commit, path):
    #     contributors.add(c.author.name)
    # current_app.logger.debug(contributors)
    # current_app.logger.debug(len(contributors))

    line_count = blob.data.splitlines()
    loc_count = sum(1 for l in line_count if len(l.strip()) > 0)

    blob.is_binary
    # mimetype = magic_from_buffer(blob_one_k, mime=True)

    highlighted_data = pygmentize(blob.data, path.rsplit('/', 1)[-1])

    return render_template(
        'blob.html',
        commit=commit,
        blob=blob,
        line_count=len(line_count),
        loc_count=loc_count,
        highlighted_data=highlighted_data
    )


@bp.route('/raw/<rev>/<path:path>')
def raw(path):
    # TODO: limit raw display if file too big
    blob = g.repo.blob(g.commit, path)

    def generate():
        for chunk in blob.data:
            yield ''.join(chunk)

    return Response(generate(), mimetype='')


@bp.route('/blame/<rev>/<path:path>')
def blame(path):
    # TODO: everything.
    # blame = repo.blame(g.commit, path)
    return 'Not here yet, thank you come again!'


@bp.route('/<any(branches, tags):ref_type>')
def refs(ref_type):
    # TODO: Probably cut this into distinct functions, since branches view is pretty detailed
    refs = getattr(g.repo, ref_type, [])

    if request.is_xhr:
        return jsonify(**{ref_type: list(refs)})

    return render_template(
        'refs.html',
        ref_type=ref_type,
        refs=refs
    )


@bp.route('/contributors')
def contributors():
    contributors = g.repo.contributors
    return u'Excuse the mess, still working on this...\n\n' + unicode(contributors)
