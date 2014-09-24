# -*- coding: utf-8 -*-


class SchemeDomainFix(object):
    ''' Wrap the application in this middleware if your application
        serves requests from behind a proxy and has no concept of
        whether or not the incoming request was secure or not.

        Looks for a request header named HTTP_X_HTTPS, which when
        present, indicates the request was indeed secure.

        Also fixes SERVER_NAME and HTTP_HOST mismatching by setting
        SERVER_NAME to whatever HTTP_HOST is, since that's more likely
        the domain that was actually requested.

        Make sure the server proxying the request to this application
        sets this header into the request before passing it on.

        :param app: the WSGI application. In the case of Flask, this is
        Flask.wsgi_app, and not an instance of Flask itself.
    '''
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        scheme = 'https' if any(
            h for h in ['HTTP_X_HTTPS', 'HTTP_X_FORWARDED_SSL']
            if h in environ
        ) else 'http'

        host = environ.get('HTTP_HOST', None)

        if scheme:
            environ['wsgi.url_scheme'] = scheme

        if host:
            environ['SERVER_NAME'] = host

        # Make this print if self.debug - pass debug in a param in the constructor
        # print '[PA] scheme: %s, host: %s' % (scheme, host)

        return self.app(environ, start_response)
