import unittest

from backend.helpers import search_filter

class Test_Reminder_Handler(unittest.TestCase):
	def test_filter_function(self):
		p = {
			'title': 'TITLE',
			'text': 'TEXT'
		}
		for test_case in ('', 'title', 'ex'):
			self.assertTrue(search_filter(test_case, p))
		for test_case in (' ', 'Hello'):
			self.assertFalse(search_filter(test_case, p))
