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
    configure_helpers(app)

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
            app.logger.debug('found blueprint at "{}" - registering with app...'.format(blueprint_name))
            app.register_blueprint(blueprint, **blueprint_kwargs)


def configure_helpers(app):
    # !!! TODO: Turn this into a function inside reppo.helpers.__init__
    # !!! TODO: to register filters/helpers easily/easier
    # app.jinja_env.filters.update(
    #     datetimeformat=format_datetime,
    #     dateformat=format_date,
    #     timeformat=format_time,
    #     timedeltaformat=format_timedelta,
    # )
    from reppo.utils.filters import jiralink, normalizepath, pathwalk, formatnumber, shortsha, formatdate, isoformattimestamp, parentpath

    for fn in [jiralink, normalizepath, pathwalk, formatnumber, shortsha, formatdate, isoformattimestamp, parentpath, ]:
        app.add_template_filter(fn)


def configure_extensions(app):
    # -- Reppo Repo

    from reppo.lib.repo import name_repo
    from reppo.lib.repo import Reppo

    app.config['REPOS'] = dict(
        (name_repo(repo_path), Reppo(repo_path))
        for repo_path in
        app.config.get('REPO_PATHS')
    )

    from reppo.utils.avatar import init_avatars

    init_avatars(app)

    # -- Flask-Login

    # from hotels.models.customer import Customer
    # from hotels.models.customer import Visitor

    # from hotels.extensions import login_manager

    #TODO: This needs investigation - Flask-Login seems to ignore the value from app config
    # login_manager.session_protection = app.config.get('SESSION_PROTECTION', 'basic')

    # login_manager.login_view = 'user.login'
    # login_manager.refresh_view = 'user.refresh'

    # login_manager.anonymous_user = Visitor

    # @login_manager.user_loader
    # def load_user(user_id):
    #     customer, guest_profiles, billing_profiles = api_service.profiles(user_id)

    #     if customer:
    #         return Customer(user_id, customer)

    #     return None
    # login_manager.init_app(app)
