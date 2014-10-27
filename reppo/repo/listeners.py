# -*- coding: utf-8 -*-

import sys
import time

if sys.platform == 'win32':
    timer = time.clock
else:
    timer = time.time

from flask import g


def init_repo_listeners(state):
    for fn in (log_request_response_data,):  # log_template_rendered):
        fn(state.app)


def log_request_response_data(app):
    app.logger.debug('adding log_request_response_data signal listener...')

    from flask import request_started
    from flask import request_finished

    from flask import request

    @request_started.connect_via(app)
    def _log_request(sender, **extra):
        if request.endpoint.startswith('repo.'):
            g.__request_timer = (request.endpoint, timer())

    @request_finished.connect_via(app)
    def _log_response(sender, response, **extra):
        if '__request_timer' in g:
            endpoint, start_time = g.__request_timer

            end_time = ((timer() - start_time) * 1000)
            response_size = response.calculate_content_length()

            sender.logger.info(
                '%s [%s] %sb %03dms',
                response.status_code, endpoint, response_size, end_time
            )

            del g.__request_timer


def log_template_rendered(app):
    app.logger.debug('adding template_rendered signal listener...')

    from flask import template_rendered

    import pprint

    @template_rendered.connect_via(app)
    def _log_template_rendered(sender, template, context, **extra):
        sender.logger.info('Template %s is rendered with: %s', template.name, pprint.pformat(context))
