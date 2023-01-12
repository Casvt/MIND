#-*- coding: utf-8 -*-

from sqlite3 import IntegrityError
from threading import Thread
from time import sleep, time as epoch_time
from typing import List, Literal

from apprise import Apprise
from flask import Flask

from backend.custom_exceptions import (InvalidTime,
                                       NotificationServiceNotFound,
                                       ReminderNotFound)
from backend.db import close_db, get_db

class ReminderHandler():
	"""Run in a thread to handle the set reminders
	"""
	def __init__(self, context) -> None:
		self.context = context
		self.thread = Thread(target=self._handle, name='Reminder Handler')
		self.stop = False

		return

	def _find_next_reminder(self) -> None:
		"""Note when next reminder is (could be in the past) or otherwise None
		"""

		with self.context():
			next_timestamp = get_db().execute(
				"SELECT time FROM reminders ORDER BY time LIMIT 1;"
			).fetchone()

		if next_timestamp is None:
			self.next_reminder: None = next_timestamp
		else:
			self.next_reminder: int = next_timestamp[0]

		return

	def submit_next_reminder(self, timestamp: int=None) -> bool:
		if timestamp is None:
			self._find_next_reminder()
			return False
		
		if self.next_reminder is None:
			self.next_reminder = timestamp
			return True

		if timestamp < self.next_reminder:
			self.next_reminder = timestamp
			return True

		return False

	def _handle(self) -> None:
		while not self.stop:
			if self.next_reminder and self.next_reminder <= epoch_time():
				with self.context():
					cursor = get_db()
					# Get all reminders for the timestamp
					reminders = cursor.execute(
						"SELECT notification_service, title, text FROM reminders WHERE time = ?",
						(self.next_reminder,)
					).fetchall()
					
					# Send of each reminder
					for reminder in reminders:
						a = Apprise()
						url = cursor.execute(
							"SELECT url FROM notification_services WHERE id = ?",
							(reminder[0],)
						).fetchone()[0]
						a.add(url)
						a.notify(title=reminder[1], body=reminder[2])

					# Delete the reminders from the database
					cursor.execute("DELETE FROM reminders WHERE time = ?", (self.next_reminder,))
					
					# Note when next reminder is (could be in the past) or otherwise None
					self._find_next_reminder()

			sleep(5)
		return

	def stop_handling(self) -> None:
		self.stop = True
		self.thread.join()
		return

handler_context = Flask('handler')
handler_context.teardown_appcontext(close_db)
reminder_handler = ReminderHandler(handler_context.app_context)

class Reminder:
	"""Represents a reminder
	"""	
	def __init__(self, reminder_id: int):
		self.id = reminder_id

		# Check if reminder exists
		if not get_db().execute("SELECT 1 FROM reminders WHERE id = ? LIMIT 1", (self.id,)).fetchone():
			raise ReminderNotFound

	def get(self) -> dict:
		"""Get info about the reminder

		Returns:
			dict: The info about the reminder
		"""
		reminder: dict = get_db(dict).execute("""
			SELECT
				r.id,
				r.title, r.text,
				r.time,
				r.notification_service,
				ns.title AS notification_service_title
			FROM
				reminders r
				INNER JOIN notification_services ns
			ON
				r.notification_service = ns.id
				AND r.id = ?;
			""",
			(self.id,)
		).fetchone()

		return dict(reminder)

	def update(
		self,
		title: str = None,
		time: int = None,
		notification_service: int = None,
		text: str = None
	) -> dict:
		"""Edit the reminder

		Args:
			title (str): The new title of the entry. Defaults to None.
			time (int): The new epoch timestamp the the reminder should be send. Defaults to None.
			notification_service (int): The new id of the notification service to use to send the reminder. Defaults to None.
			text (str, optional): The new body of the reminder. Defaults to None.

		Returns:
			dict: The new password info
		"""
		# Validate data
		if time < epoch_time():
			raise InvalidTime
		time = round(time)

		# Get current data and update it with new values
		data = self.get()
		new_values = {
			'title': title,
			'time': time,
			'notification_service': notification_service,
			'text': text
		}
		for k, v in new_values.items():
			if v is not None:
				data[k] = v

		# Update database
		try:
			get_db().execute("""
				UPDATE reminders
				SET title=?, text=?, time=?, notification_service=?
				WHERE id = ?;
				""", (
					data["title"],
					data["text"],
					data["time"],
					data["notification_service"],
					self.id
			))
		except IntegrityError:
			raise NotificationServiceNotFound
		reminder_handler.submit_next_reminder(time)

		return self.get()

	def delete(self) -> None:
		"""Delete the reminder
		"""		
		get_db().execute("DELETE FROM reminders WHERE id = ?", (self.id,))
		reminder_handler.submit_next_reminder(None)
		return

class Reminders:
	"""Represents the reminder vault of the user account
	"""	
	sort_functions = {
		'title': (lambda r: (r['title'], r['time']), False),
		'title_reversed': (lambda r: (r['title'], r['time']), True),
		'time': (lambda r: r['time'], False),
		'time_reversed': (lambda r: r['time'], True)
	}
	
	def __init__(self, user_id: int):
		self.user_id = user_id

	def fetchall(self, sort_by: Literal["time", "time_reversed", "title", "title_reversed"] = "time") -> List[dict]:
		"""Get all reminders

		Args:
			sort_by (Literal["time", "time_reversed", "title", "title_reversed"], optional): How to sort the result. Defaults to "time".

		Returns:
			List[dict]: The id, title, text, time, notification_service and notification_service_title of each reminder
		"""		
		sort_function = self.sort_functions.get(
			sort_by,
			self.sort_functions['time']
		)

		# Fetch all reminders
		reminders: list = list(map(dict, get_db(dict).execute("""
			SELECT
				r.id,
				r.title, r.text,
				r.time,
				r.notification_service,
				ns.title AS notification_service_title
			FROM
				reminders r
				INNER JOIN notification_services ns
			ON
				r.notification_service = ns.id
				AND r.user_id = ?;
			""",
			(self.user_id,)
		).fetchall()))

		# Sort result
		reminders.sort(key=sort_function[0], reverse=sort_function[1])

		return reminders

	def search(self, query: str) -> List[dict]:
		"""Search for reminders

		Args:
			query (str): The term to search for

		Returns:
			List[dict]: All reminders that match. Similar output to self.fetchall
		"""		
		query = query.lower()
		passwords = self.fetchall()
		passwords = list(filter(
			lambda p: (
				query in p["title"].lower()
				or query in p["text"].lower()
				or query in p["notification_service_title"].lower()
			),
			passwords
		))
		return passwords

	def fetchone(self, id: int) -> Reminder:
		"""Get one reminder

		Args:
			id (int): The id of the reminder to fetch

		Returns:
			Reminder: A Reminder instance
		"""		
		return Reminder(id)

	def add(
		self,
		title: str,
		time: int,
		notification_service: int,
		text: str = ''
	) -> Reminder:
		"""Add a reminder

		Args:
			title (str): The title of the entry
			time (int): The epoch timestamp the the reminder should be send.
			notification_service (int): The id of the notification service to use to send the reminder.
			text (str, optional): The body of the reminder. Defaults to ''.

		Returns:
			dict: The info about the reminder
		"""
		# Validate data
		if time < epoch_time():
			raise InvalidTime
		time = round(time)
		
		# Insert into db
		try:
			id = get_db().execute("""
				INSERT INTO reminders(user_id, title, text, time, notification_service)
				VALUES (?,?,?,?,?);
			""", (self.user_id, title, text, time, notification_service,)
			).lastrowid
		except IntegrityError:
			raise NotificationServiceNotFound
		reminder_handler.submit_next_reminder(time)

		# Return info
		return self.fetchone(id)
