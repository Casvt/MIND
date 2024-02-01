import unittest
from inspect import getmembers, getmro, isclass
from sys import modules
from typing import List

import backend.custom_exceptions

class Test_Custom_Exceptions(unittest.TestCase):
	def test_type(self):
		defined_exceptions: List[Exception] = filter(
			lambda c: c.__module__ == 'backend.custom_exceptions'
						and c is not backend.custom_exceptions.CustomException,
			map(
				lambda c: c[1],
				getmembers(modules['backend.custom_exceptions'], isclass)
			)
		)

		for defined_exception in defined_exceptions:
			self.assertIn(
				getmro(defined_exception)[1],
				(
					backend.custom_exceptions.CustomException,
					Exception
				)
			)
			try:
				result = defined_exception().api_response
			except TypeError:
				try:
					result = defined_exception('1').api_response
				except TypeError:
					result = defined_exception('1', '2').api_response
				
			self.assertIsInstance(result, dict)
			result['error']
			result['result']
			result['code']
			self.assertIsInstance(result['code'], int)
