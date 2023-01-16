import unittest
from threading import Thread

from backend.reminders import filter_function, ReminderHandler

class Test_Reminder_Handler(unittest.TestCase):
	def test_starting_stopping(self):
		context = 'test'
		instance = ReminderHandler(context)
		self.assertIs(context, instance.context)

		self.assertIsInstance(instance.thread, Thread)

		self.assertFalse(instance.stop)
		with self.assertRaises(RuntimeError):
			instance.stop_handling()
		self.assertTrue(instance.stop)

	def test_filter_function(self):
		p = {
			'title': 'TITLE',
			'text': 'TEXT',
			'notification_service_title': 'NOTIFICATION_SERVICE_TITLE'
		}
		for test_case in ('', 'title', 'service', 'ex'):
			self.assertTrue(filter_function(test_case, p))
		for test_case in (' ', 'Hello'):
			self.assertFalse(filter_function(test_case, p))

