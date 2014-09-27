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

from reppo.lib.repo import Reppo

from reppo.lib.highlight import pygmentize

from reppo.utils.pagination import Pagination

bp = Blueprint('repo', __name__, url_prefix='/<repo_key>')

'''
    http://stackoverflow.com/questions/7782046/how-do-i-use-url-for-if-my-method-has-multiple-route-annotations/7876088#7876088

    Flask Author appears to discourage the concept of stacking routes on a
    single endpoint.

    Instead, it is apparently "better" to make the "odd" routes return the
    endpoint you wanted as a function call.

    Meh.

    ===============================================================================

    TODO:

    *   Need branch selector for tree and commits views.
        (Branch selector on commits views can also show a sha as "current"
         branch, but the underlying selector still only allows refs)

    *   Refs view is unstyled and shit-tastic.

    *   Derp. LDAP login protection.

    *   http://stackoverflow.com/questions/2529441/how-to-work-with-diff-representation-in-git

    *   /<repo_key>/blame/<ref>/<path:path> (ie. blame view of a blob). bleh.

    Order of execution per-request is as follows:
        1. url_value_preprocessor
        2. before_request

    Any functions decorated with the above will be executed in the
    order they were defined here.

    For example, if you have decorate two functions with
    url_value_preprocessor, then those functions would be called in
    the order they are physically defined in the code, but they would
    still both be called *before* any before_request decorated functions
    are called.
'''


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

    g.repo = Reppo(repo_path)


@bp.url_defaults
def add_repo_url_defaults(endpoint, values):
    values.setdefault('repo_key', g.repo_key)

    if 'ref' in values:
        return

    if current_app.url_map.is_endpoint_expecting(endpoint, 'ref'):
        values['ref'] = request.view_args.get('ref', g.repo.branches.next())


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
    return 'Nope', 404


@bp.route('/')
def no_tree_no_ref():
    return _redirect_to_tree()


@bp.route('/tree/')
def tree_no_ref():
    return _redirect_to_tree()


def _redirect_to_tree():
    return redirect(url_for('.tree'))


@bp.route('/tree/<ref>/')
@bp.route('/tree/<ref>/<path:path>')
def tree(ref, path=None):
    # TODO: no trailing slash when no path?
    # TODO: when ref is sha, don't display 'branch' in branch selector
    summary = None

    if path is None:
        summary = g.repo.get_repo_summary()

    latest = g.repo.get_commit(ref, path)
    tree = g.repo.get_tree(ref, path)

    return render_template(
        'tree.html',
        summary=summary,
        latest=latest,
        tree=tree,
    )


@bp.route('/commits/<ref>')
@bp.route('/commits/<ref>/<path:path>')
def commits(ref, path=None):
    # TODO: add back count! (oops)
    per_page = 30
    page = abs(request.args.get('page', 1, type=int))
    skip = (page * per_page) - per_page

    count = 11007  # g.repo.commit_count(ref)
    pagination = Pagination(page, per_page, count)

    history = g.repo.get_history(ref, path=path, skip=skip, stop=per_page)

    return render_template(
        'history.html',
        ref=ref,
        history=history,
        pagination=pagination
    )


@bp.route('/commit/<sha>')
def commit(sha):
    # TODO: check summary really is no longer used
    # TODO: see if we can get branches for commit without explosions
    # TODO: clean up 'changes' to 'diff'
    # TODO: add chunk shas to diff for additional resolution of a diff overall
    commit = g.repo.get_commit(sha)
    changes = g.repo.get_diff(sha)
    summary = {}
    branches = None  # g.repo.branches_for_commit(sha)

    return render_template(
        'commit.html',
        commit=commit,
        summary=summary,
        changes=changes,
        branches=branches
    )


@bp.route('/blob/<ref>/<path:path>')
def blob(ref, path):
    # TODO: clean all this crap up
    # TODO: actually do something if file is binary
    # TODO: is_binary + is_possibly_an_image -> display image?
    # TODO: limit display if file too big?
    # TODO: use repo.get_walker to find contributors for entire history
    # TODO: link to 'history' - see history route
    # TODO: use max_entries=1 in repo.get_walker when we know we want just one commit?
    commit = g.repo.get_commit(ref, path)
    blob = g.repo.get_blob(ref, path)

    line_count = blob.data.splitlines()
    loc_count = sum(1 for l in line_count if len(l.strip()) > 0)

    # for line in line_count:
    #     print repr(line)

    textchars = ''.join(map(chr, [7, 8, 9, 10, 12, 13, 27] + range(0x20, 0x100)))
    is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))

    blob_one_k = blob.data[:1024]

    is_binary = is_binary_string(blob_one_k)
    mimetype = magic_from_buffer(blob_one_k, mime=True)

    highlighted_data = pygmentize(blob.data, path.rsplit('/', 1)[-1])

    # return '[BLOB] {repo} :: {ref} :: {blob}'.format(repo=g.repo.name, ref=ref, blob=blob)
    return render_template(
        'blob.html',
        commit=commit,
        line_count=len(line_count),
        loc_count=loc_count,
        blob_data_size=blob.raw_length(),
        # blob_id=blob.id,
        highlighted_data=highlighted_data
    )


@bp.route('/raw/<ref>/<path:path>')
def raw(ref, path):
    # TODO: limit raw display if file too big
    blob = g.repo.get_blob(ref, path)

    def generate():
        for chunk in blob.chunked:
            yield ''.join(chunk)

    return Response(generate(), mimetype='')


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
