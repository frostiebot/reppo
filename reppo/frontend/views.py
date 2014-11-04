# -*- coding: utf-8 -*-

import logging

from flask import Blueprint
from flask import Response

from flask import abort
from flask import flash
from flask import g
from flask import get_flashed_messages
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from reppo.utils.pagination import Pagination

from .locals import repo

logger = logging.getLogger(__name__)
bp = Blueprint('repo', __name__, url_prefix='/<repo_name>')


@bp.record
def bp_registered_with_app(state):
    state.app.logger.debug('repo blueprint initializing...')

    from .listeners import init_repo_listeners
    from .handlers import init_repo_handlers
    from .filters import init_repo_template_filters

    init_repo_listeners(state)
    init_repo_handlers(state)
    init_repo_template_filters(state)

    state.app.logger.debug('repo blueprint ready!')


@bp.context_processor
def inject_pagination_helper():
    def url_for_other_page(page):
        args = request.view_args.copy()
        args['page'] = page
        return url_for(request.endpoint, **args)
    return dict(url_for_other_page=url_for_other_page)


@bp.errorhandler(404)
def not_found(error):
    repo_before_request_messages = get_flashed_messages(
        category_filter=[u'repo-404']
    )
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
    return redirect(url_for('.tree', rev=repo.head.shorthand))


@bp.route('/tree/<rev>/')
@bp.route('/tree/<rev>/<path:path>')
def tree(path=None):
    # TODO: format commit summary and commit date for per-object latest commit in template
    # TODO: tree should probably be a table due to latest commit now available
    # TODO: when path is not None show button to repo.commits at far right of breadcrumb
    # TODO: lang summary - will require walking tree completely and dumping file extensions into a set (or a defaultdict that gets passed to a Counter)
    tree = repo.tree(path)
    latest = repo.commit(path)

    summary = None
    if path is None:
        summary = repo.stats()

    return render_template(
        'tree.html',
        tree=tree,
        latest=latest,
        summary=summary,
    )


@bp.route('/commits/<rev>')
@bp.route('/commits/<rev>/<path:path>')
def commits(path=None):
    # TODO: Make pagination cached in user session keyed by rev (pop last n revs)
    # TODO: Recreate instance where path did not appear to be working
    page = abs(request.args.get('page', 1, type=int))
    per_page = 30

    count = repo.stats(path).get('commits', 0)
    skip = (page * per_page) - per_page

    pagination = Pagination(page, per_page, count)

    log = repo.log(path=path, skip=skip, stop=per_page)

    return render_template(
        'commits.html',
        log=log,
        pagination=pagination
    )


@bp.route('/commit/<rev>')
def commit():
    # TODO: see if we can get branches for commit without explosions
    diff = repo.diff()
    commit = repo.commit()
    branches = None  # repo.branches_for_commit(rev)

    return render_template(
        'commit.html',
        diff=diff,
        commit=commit,
        branches=branches
    )


@bp.route('/blob/<rev>/<path:path>')
def blob(path):
    # TODO: limit display if file too big?
    # TODO: clean up compilation and rendering of contributors (perhaps move contributor into Blob?)
    # TODO: handle 404 differently (add to repo.handlers - check endpoint)
    blob = repo.blob(path)

    if blob is None:
        flash(u'Blob "{}" for rev "{}" in the "{}" repo not found'.format(path, g.rev, g.repo_name), u'repo-404')
        abort(404)

    commit = repo.commit(path)

    contributors = list(
        contributor for contributor, count
        in repo.contributors(path)
    )

    return render_template(
        'blob.html',
        blob=blob,
        commit=commit,
        contributors=contributors
    )


@bp.route('/raw/<rev>/<path:path>')
def raw(path):
    # TODO: limit raw display if file too big
    # TODO: handle 404 differently (add to repo.handlers - check endpoint)
    blob = repo.blob(path)

    if blob is None:
        flash(u'Blob "{}" for rev "{}" in the "{}" repo not found'.format(path, g.rev, g.repo_name), u'repo-404')
        abort(404)

    def generate():
        for chunk in blob.data_:
            yield ''.join(chunk)

    return Response(generate(), mimetype='')


@bp.route('/blame/<rev>/<path:path>')
def blame(path):
    # TODO: everything.
    # blame = repo.blame(path)
    return 'Not here yet, thank you come again!'


@bp.route('/<any(branches, tags):ref_type>')
def refs(ref_type):
    # TODO: Probably cut this into distinct functions, since branches view is pretty detailed
    refs = getattr(repo, ref_type, [])

    if request.is_xhr:
        return jsonify(**{ref_type: list(refs)})

    return render_template(
        'refs.html',
        ref_type=ref_type,
        refs=refs
    )


@bp.route('/contributors')
def contributors():
    contributors = repo.contributors()
    return u'Excuse the mess, still working on this...\n\n' + unicode(contributors)