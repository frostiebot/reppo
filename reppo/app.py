# -*- coding: utf-8 -*-

'''AUTH_LDAP_SERVER = 'ldap://auth1'
AUTH_LDAP_ANON_DN = 'cn=admin,dc=tablet,dc=tab'
AUTH_LDAP_ANON_PASS = 'ldap'
AUTH_LDAP_BASE_DN = 'dc=tablet,dc=tab'
AUTH_LDAP_FILTER = 'cn=%s'

cn=chris,dc=tablet,dc=tab
'''


def create_app(config=None, blueprints=None):
    from flask import Flask
    from reppo import defaults

    app = Flask(defaults.project_name)

    config = config or defaults

    configure_app(app, config)
    configure_blueprints(app, blueprints or config.BLUEPRINTS)
    configure_extensions(app)

    return app


def configure_app(app, config):
    app.config.from_object(config)
    app.config.from_envvar('REPPO_UWSGI_APP_CONFIG', silent=True)

    # Ensure we know if a request is secure or not and also which domain
    # the request was for.
    from reppo.middleware.fixers import SchemeDomainFix
    app.wsgi_app = SchemeDomainFix(app.wsgi_app)

    # from werkzeug.contrib.profiler import ProfilerMiddleware
    # app.wsgi_app = ProfilerMiddleware(app.wsgi_app)

    if app.debug:
        # Inject the debug middleware.
        # This is instead of using app.run(debug=True), since this
        # function is an application factory - it's up to the caller
        # to actually call run on the returned app instance.
        from werkzeug.debug import DebuggedApplication
        app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True, console_path='/console')


def configure_blueprints(app, blueprints):
    from werkzeug.utils import import_string

    for blueprint_config in blueprints:
        blueprint_name = None
        blueprint_kwargs = {}

        if isinstance(blueprint_config, basestring):
            blueprint_name = blueprint_config
        elif isinstance(blueprint_config, tuple):
            blueprint_name, blueprint_kwargs = blueprint_config

        blueprint = import_string('{}:bp'.format(blueprint_name))

        if blueprint:
            app.logger.debug('registering blueprint "{}"'.format(blueprint.name))
            app.register_blueprint(blueprint, **blueprint_kwargs)


def configure_extensions(app):
    # -- Reppo Repo

    from reppo.repo import Repo

    repos = app.config['REPOS']
    app.config['REPOS'] = dict((name, Repo(path)) for name, path in repos)

    # -- Reppo Avatars

    from reppo.utils.avatar import init_avatars

    init_avatars(app)
