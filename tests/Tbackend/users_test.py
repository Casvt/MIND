import unittest

from backend.base.custom_exceptions import UsernameInvalid
from backend.base.definitions import Constants
from backend.implementations.users import is_valid_username


class Test_Users(unittest.TestCase):
    def test_username_check(self):
        for test_case in ('', 'test'):
            is_valid_username(test_case)

        for test_case in (' ', '	', '0', 'api', *Constants.INVALID_USERNAMES):
            with self.assertRaises(UsernameInvalid):
                is_valid_username(test_case)
