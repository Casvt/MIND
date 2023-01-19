import unittest

from flask import Flask

from frontend.api import api
from frontend.ui import ui
from Noted import _create_app

class Test_Noted(unittest.TestCase):
	def test_create_app(self):
		result = _create_app()
		self.assertIsInstance(result, Flask)

		self.assertEqual(result.blueprints.get('ui'), ui)
		self.assertEqual(result.blueprints.get('api'), api)

		handlers = result.error_handler_spec[None].keys()
		required_handlers = 404, 400, 405, 500
		for handler in required_handlers:
			self.assertIn(handler, handlers)
