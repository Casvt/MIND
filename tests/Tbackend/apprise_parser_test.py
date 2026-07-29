import unittest

from apprise import Apprise
from mock import patch

from backend.implementations.apprise_parser import get_apprise_services


class Test_AppriseParser(unittest.TestCase):
    @patch("backend.implementations.apprise_parser.init_apprise")
    def test_parser(self, init_apprise_mock):
        init_apprise_mock.return_value = Apprise()

        try:
            get_apprise_services()
        except Exception as e:
            self.fail(f"get_apprise_services() raised an exception: {e}")
