import unittest

from flask import Blueprint, Flask

from frontend.ui import methods, ui

class Test_UI(unittest.TestCase):
	def test_methods(self):
		self.assertEqual(len(methods), 1)
		self.assertEqual(methods[0], 'GET')

	def test_blueprint(self):
		self.assertIsInstance(ui, Blueprint)
		
	def test_route_methods(self):
		temp_app = Flask(__name__)
		temp_app.register_blueprint(ui)
		for rule in temp_app.url_map.iter_rules():
			self.assertEqual(len(rule.methods), 3)
			self.assertIn(methods[0], rule.methods)
