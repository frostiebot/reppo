# -*- coding: utf-8 -*-

from reppo import create_app

app = create_app()

app.config.update(
    TESTING=True
)

app.logger.disabled = True

test_client = app.test_client()
# ctx = app.test_request_context()


def _login(email, password):
    return test_client.post('/login/', data=dict(
        email=email,
        password=password
    ), follow_redirects=True)


def _logout():
    return test_client.get('/logout', follow_redirects=True)

# class HotelsTestBase(object):
#     def setUp(self):
#         app = create_app()

#         app.config.update(
#             TESTING=True
#         )

#         app.logger.disabled = True

#         self.reppo_app = app
#         self.app = app.test_client()



# class HotelsTestCase(unittest.TestCase):
#     def setUp(self):
#         app = create_app()

#         app.config.update(
#             TESTING=True
#         )

#         self.app = app.test_client()

#     def tearDown(self):
#         pass
