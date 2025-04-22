import unittest

from backend.base.definitions import GeneralReminderData
from backend.base.helpers import search_filter


class Test_Reminder_Handler(unittest.TestCase):
    def test_filter_function(self):
        p = GeneralReminderData(
            id=1,
            title='TITLE',
            text='TEXT',
            color=None,
            notification_services=[]
        )
        for test_case in ('', 'title', 'ex'):
            self.assertTrue(search_filter(test_case, p))
        for test_case in (' ', 'Hello'):
            self.assertFalse(search_filter(test_case, p))
