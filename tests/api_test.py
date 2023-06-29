import unittest

from flask import Blueprint

from backend.custom_exceptions import *
from frontend.api import api, return_api

class Test_API(unittest.TestCase):
	def test_blueprint(self):
		self.assertIsInstance(api, Blueprint)
		
	def test_return_api(self):
		for case in ({'result': {}, 'error': 'Error', 'code': 201},
					{'result': ''}):
			result = return_api(**case)
			self.assertEqual(result[0]['result'], case['result'])
			if case.get('error'):
				self.assertEqual(result[0]['error'], case['error'])
			else:
				self.assertIsNone(result[0]['error'])
			if case.get('code'):
				self.assertEqual(result[1], case['code'])
			else:
				self.assertEqual(result[1], 200)
	