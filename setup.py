# -*- coding: utf-8 -*-

from setuptools import setup

'''
Dependency Graph
----------------

Flask-Script==0.6.7
    Flask==0.10.1
        itsdangerous==0.24
        Werkzeug==0.9.6
        Jinja2==2.7.3
            MarkupSafe==0.23

pygit2==0.21.3
    cffi==0.8.6
        pycparser==2.10

retricon==1.2.0
    pillowfight==0.2
        Pillow==2.5.3

Pygments==1.6

Experimental
------------

PyYAML==3.11

Testing
-------

coverage==3.7.1
mock==1.0.1
nose==1.3.4
'''

project = 'reppo'

setup(
    name=project,
    version='0.0.3',
    description='Reppo is a github-style gitweb replacement using Flask and pygit2',
    author='Chris Ashurst',
    author_email='chris@tablethotels.com',
    packages=['reppo'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask',            # 0.10.1
        'Flask-Script',     # 0.6.7
        'pygit2',           # 0.21.3
        'retricon',         # 1.2.0
        'Pygments',         # 1.6
        'gevent',           # 1.0.1
        'PyYAML',           # 3.11
    ],
    test_suite='nose.collector',
    tests_require=[
        'mock',             # 1.0.1
        'nose',             # 1.3.4
        'coverage',         # 3.7.1
    ]
)
