# -*- coding: utf-8 -*-

import os

project_name = u'reppo'

PROJECT_ROOT = os.path.abspath(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

DEBUG = True
TESTING = False

SECRET_KEY = u'\x8c\x92\xbb\xa0[C@\xb0\x02\xd4\xeaW\x00\xdfeP-|m\xe5\x18\xa9=!'
SESSION_COOKIE_NAME = u'reppo'

BLUEPRINTS = (
    'reppo.frontend',  # 'package.module' - or - ('package.module', {'url_prefix': '/path'}),
)

AVATAR_CACHE = os.path.join(PROJECT_ROOT, '.avatars')

REPOS = (
    ('tablet', '/home/chris/src/tablet.git'),
    ('reppo', '/home/chris/hosted/reppo')
)
