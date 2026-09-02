import unittest

from backend.base.definitions import Constants
from backend.implementations.users import is_valid_username


class Test_Users(unittest.TestCase):
    def test_username_check(self):
        for test_case in ('User1', 'test'):
            self.assertIsNone(is_valid_username(test_case))

        for test_case in (' ', '	', '0', 'api', *Constants.INVALID_USERNAMES):
            self.assertIsNotNone(is_valid_username(test_case))
