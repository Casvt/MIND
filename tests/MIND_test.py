import unittest

from flask import Flask

from frontend.api import api
from frontend.ui import ui
from backend.server import SERVER

class Test_MIND(unittest.TestCase):
	def test_create_app(self):
		SERVER.create_app()
		self.assertTrue(hasattr(SERVER, 'app'))
		app = SERVER.app
		self.assertIsInstance(app, Flask)

		self.assertEqual(app.blueprints.get('ui'), ui)
		self.assertEqual(app.blueprints.get('api'), api)

		handlers = app.error_handler_spec[None].keys()
		required_handlers = 400, 405, 500
		for handler in required_handlers:
			self.assertIn(handler, handlers)
