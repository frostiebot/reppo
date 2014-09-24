# -*- coding: utf-8 -*-

from nose.tools import *

from tests import test_client
from tests import app

# from flask import current_app
from flask import g
from flask import request

TBLT_REPO = '/tablet'


# def test_request_context():
#     with app.test_request_context('/tablet/'):
#         app.preprocess_request()


def test_repos_in_app_extensions():
    assert_in('repos', app.extensions)


def test_no_such_repo():
    with test_client as c:
        rv = c.get('/fishcakes', follow_redirects=True)
        eq_(rv.status_code, 404)


def test_slash_goes_to_tree_endpoint():
    with test_client as c:
        rv = c.get('/tablet', follow_redirects=True)
        eq_(rv.status_code, 200)

        eq_('repo.tree', request.endpoint)
        assert_not_in('path', request.view_args)

        assert_in('repo_key', g)
        assert_in('repo', g)

        ok_(g.repo.name in rv.data)
        ok_(g.repo.latest_branch in rv.data)


def test_tree_default():
    with test_client as c:
        rv = c.get('/tablet/tree', follow_redirects=True)
        eq_(rv.status_code, 200)

        ok_(g.repo.latest_branch in rv.data)


def test_tree_with_ref():
    with test_client as c:
        rv = c.get('/tablet/tree/foobar', follow_redirects=True)
        eq_(rv.status_code, 200)

        assert_in('ref', request.view_args)
        eq_('foobar', request.view_args['ref'])


def test_tree_with_ref_and_path():
    with test_client as c:
        rv = c.get('/tablet/tree/foobar/lemon/curry/isgood.txt', follow_redirects=True)
        eq_(rv.status_code, 200)

        assert_in('ref', request.view_args)
        eq_('foobar', request.view_args['ref'])

        assert_in('path', request.view_args)
        eq_('lemon/curry/isgood.txt', request.view_args['path'])


def test_commits():
    with test_client as c:
        rv = c.get('/tablet/commits/foobar', follow_redirects=True)
        eq_(rv.status_code, 200)


def test_commit():
    with test_client as c:
        rv = c.get('/tablet/commit/abcd1234', follow_redirects=True)
        eq_(rv.status_code, 200)


def test_blob():
    with test_client as c:
        rv = c.get('/tablet/blob/foobar/lemoncurry.txt', follow_redirects=True)
        eq_(rv.status_code, 200)


def test_raw():
    with test_client as c:
        rv = c.get('/tablet/raw/foobar/lemoncurry.txt', follow_redirects=True)
        eq_(rv.status_code, 200)


def test_branches():
    with test_client as c:
        rv = c.get('/tablet/branches', follow_redirects=True)
        eq_(rv.status_code, 200)


def test_tags():
    with test_client as c:
        rv = c.get('/tablet/tags', follow_redirects=True)
        eq_(rv.status_code, 200)


def test_contributors():
    with test_client as c:
        rv = c.get('/tablet/contributors', follow_redirects=True)
        eq_(rv.status_code, 200)
