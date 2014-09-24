# -*- coding: utf-8 -*-

from flask import Blueprint
from flask import Response

from flask import current_app
from flask import g
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from magic import from_buffer as magic_from_buffer

from reppo.lib.repo import Repo

from reppo.utils.pagination import Pagination

bp = Blueprint('repo', __name__, url_prefix='/<repo_key>')


@bp.url_defaults
def add_repo_key(endpoint, values):
    values.setdefault('repo_key', g.repo_key)


@bp.url_value_preprocessor
def pull_repo_key(endpoint, values):
    g.repo_key = values.pop('repo_key')


@bp.before_request
def get_repo_for_request():
    repo_path = current_app.config['REPOS'].get(g.repo_key, None)
    if repo_path is None:
        return make_response(
            'Repo with name "{}" not found.'.format(g.repo_key),
            404
        )
    g.repo = Repo(repo_path)


@bp.context_processor
def inject_repo_template_globals():
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

'''
http://stackoverflow.com/questions/7782046/how-do-i-use-url-for-if-my-method-has-multiple-route-annotations/7876088#7876088

Flask Author appears to discourage the concept of stacking routes on a
single endpoint.

Instead, it is apparently "better" to make the "odd" routes return the
endpoint you wanted as a function call.

Meh.

===============================================================================

TODO:

*   Tree header (commit count, etc) needs to go away when no longer at
    root of the branch file system.

*   Need branch selector for tree and commits views.
    (Branch selector on commits views can also show a sha as "current"
     branch, but the underlying selector still only allows refs)

*   Blob view. Raw view was easy! Probably will need pygments or
    something similar - mostly the same display as commit/diff view.

*   Refs view is unstyled and shit-tastic.

*   Contributors doesn't exist beyond plain text saying "CONTRIBUTORS"

*   Derp. LDAP login protection.

*   http://stackoverflow.com/questions/2529441/how-to-work-with-diff-representation-in-git

'''


@bp.errorhandler(404)
def not_found(error):
    return 'Nope', 404


@bp.route('/')
def no_tree_no_ref():
    return _redirect_to_tree()


@bp.route('/tree/')
def tree_no_ref():
    return _redirect_to_tree()


def _redirect_to_tree():
    return redirect(url_for('.tree', ref=g.repo.branches.next()))


@bp.route('/tree/<ref>/')
@bp.route('/tree/<ref>/<path:path>')
def tree(ref, path=None):
    summary = g.repo.summary_for_ref(ref)
    latest = g.repo.latest(ref, path)
    tree = g.repo.get_object(latest.id, path)
    path = path.split('/') if path else []

    return render_template(
        'tree.html',
        ref=ref,
        path=path,
        summary=summary,
        latest=latest,
        tree=tree,
    )


@bp.route('/commits/<ref>')
def commits(ref):
    per_page = 30
    page = abs(request.args.get('page', 1, type=int))
    skip = (page * per_page) - per_page

    count = g.repo.commit_count(ref)
    pagination = Pagination(page, per_page, count)

    history = g.repo.history(ref, skip=skip, stop=per_page)

    return render_template(
        'history.html',
        ref=ref,
        history=history,
        pagination=pagination
    )


@bp.route('/commit/<sha>')
def commit(sha):
    commit, summary, changes = g.repo.commit_info(sha)
    branches = g.repo.branches_for_commit(sha)

    return render_template(
        'commit.html',
        commit=commit,
        summary=summary,
        changes=changes,
        branches=branches
    )


@bp.route('/blob/<ref>/<path:path>')
def blob(ref, path):
    blob = g.repo.get_object(ref, path)

    textchars = ''.join(map(chr, [7, 8, 9, 10, 12, 13, 27] + range(0x20, 0x100)))
    is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))

    blob_one_k = blob.data[:1024]

    is_binary = is_binary_string(blob_one_k)
    mimetype = magic_from_buffer(blob_one_k, mime=True)

    return '[BLOB] {repo} :: {ref} :: {blob}'.format(repo=g.repo.name, ref=ref, blob=blob)


@bp.route('/raw/<ref>/<path:path>')
def raw(ref, path):
    blob = g.repo.get_object(ref, path)

    def generate():
        for chunk in blob.chunked:
            yield ''.join(chunk)

    return Response(generate(), mimetype='')


@bp.route('/<any(branches, tags):ref_type>')
def refs(ref_type):
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
    contributors = g.repo.contributors()
    return '{contributors}'.format(contributors='\n'.join(contributors))
