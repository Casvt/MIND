import unittest

from flask import Blueprint

from backend.custom_exceptions import *
from frontend.api import api, auth, error_handler, return_api

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

	def test_auth(self):
		method = lambda x: x
		result = auth(method)
		self.assertEqual(result.__name__, method.__name__)

	def _raise_exception(self, e, *args):
		raise e(*args)

	def test_error_handler(self):
		result = error_handler(self._raise_exception)
		self.assertEqual(result.__name__, self._raise_exception.__name__)
		self.assertEqual(result(UsernameTaken), return_api(**UsernameTaken.api_response))
		self.assertEqual(result(UsernameInvalid), return_api(**UsernameInvalid.api_response))
		self.assertEqual(result(UserNotFound), return_api(**UserNotFound.api_response))
		self.assertEqual(result(AccessUnauthorized), return_api(**AccessUnauthorized.api_response))
		self.assertEqual(result(ReminderNotFound), return_api(**ReminderNotFound.api_response))
		self.assertEqual(result(NotificationServiceNotFound), return_api(**NotificationServiceNotFound.api_response))
		self.assertEqual(result(InvalidTime), return_api(**InvalidTime.api_response))
		self.assertEqual(result(NotificationServiceInUse, 'test'), return_api(**NotificationServiceInUse('test').api_response))
		self.assertEqual(result(KeyNotFound, 'test'), return_api(**KeyNotFound('test').api_response))
		self.assertEqual(result(InvalidKeyValue, 'test', 'value'), return_api(**InvalidKeyValue('test', 'value').api_response))
		with self.assertRaises(TypeError):
			result(TypeError)
		with self.assertRaises(KeyError):
			result(KeyError)
	