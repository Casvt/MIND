import unittest

from backend.custom_exceptions import UsernameInvalid
from backend.users import ONEPASS_INVALID_USERNAMES, _check_username

class Test_Users(unittest.TestCase):
	def test_username_check(self):
		for test_case in ('', 'test'):
			_check_username(test_case)
			
		for test_case in (' ', '	', '0', 'api', *ONEPASS_INVALID_USERNAMES):
			with self.assertRaises(UsernameInvalid):
				_check_username(test_case)
		