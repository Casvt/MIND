import unittest

from backend.custom_exceptions import UsernameInvalid
from backend.users import ONEPASS_INVALID_USERNAMES, Users

class Test_Users(unittest.TestCase):
	def test_username_check(self):
		users = Users()
		for test_case in ('', 'test'):
			users._check_username(test_case)
			
		for test_case in (' ', '	', '0', 'api', *ONEPASS_INVALID_USERNAMES):
			with self.assertRaises(UsernameInvalid):
				users._check_username(test_case)
