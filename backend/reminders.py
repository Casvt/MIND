#-*- coding: utf-8 -*-

from datetime import datetime
from sqlite3 import IntegrityError
from threading import Thread
from time import sleep
from time import time as epoch_time
from typing import List, Literal

from apprise import Apprise
from dateutil.relativedelta import relativedelta
from flask import Flask

from backend.custom_exceptions import (InvalidKeyValue, InvalidTime,
                                       NotificationServiceNotFound,
                                       ReminderNotFound)
from backend.db import close_db, get_db

filter_function = lambda query, p: (
	query in p["title"].lower()
	or query in p["text"].lower()
	or query in p["notification_service_title"].lower()
)

def _find_next_time(
	original_time: int,
	repeat_quantity: Literal["year", "month", "week", "day", "hours", "minutes"],
	repeat_interval: int
) -> int:
	td = relativedelta(**{repeat_quantity: repeat_interval})
	new_time = datetime.fromtimestamp(original_time)
	current_time = datetime.fromtimestamp(datetime.utcnow().timestamp())
	while new_time <= current_time:
		new_time += td
	return int(new_time.timestamp())

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
			if self.next_reminder and self.next_reminder <= datetime.utcnow().timestamp():
				with self.context():
					cursor = get_db(dict)
					# Get all reminders for the timestamp
					reminders = cursor.execute("""
						SELECT
							id,
							notification_service, title, text,
							repeat_quantity, repeat_interval, original_time
						FROM reminders
						WHERE time = ?;
						""",
						(self.next_reminder,)
					).fetchall()
					
					for reminder in reminders:
						# Send of reminder
						a = Apprise()
						url = cursor.execute(
							"SELECT url FROM notification_services WHERE id = ?",
							(reminder["notification_service"],)
						).fetchone()["url"]
						a.add(url)
						a.notify(title=reminder["title"], body=reminder["text"])

						if reminder['repeat_quantity'] is None:
							# Delete the reminders from the database
							cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder['id'],))
						else:
							# Set next time
							new_time = _find_next_time(
								reminder['original_time'],
								reminder['repeat_quantity'],
								reminder['repeat_interval']
							)
							self.submit_next_reminder(new_time)
							cursor.execute(
								"UPDATE reminders SET time = ? WHERE id = ?;",
								(new_time, reminder['id'])
							)

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
				ns.title AS notification_service_title,
				r.repeat_quantity,
				r.repeat_interval
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
		text: str = None,
		repeat_quantity: Literal["year", "month", "week", "day", "hours", "minutes"] = None,
		repeat_interval: int = None
	) -> dict:
		"""Edit the reminder

		Args:
			title (str): The new title of the entry. Defaults to None.
			time (int): The new UTC epoch timestamp the the reminder should be send. Defaults to None.
			notification_service (int): The new id of the notification service to use to send the reminder. Defaults to None.
			text (str, optional): The new body of the reminder. Defaults to None.

		Returns:
			dict: The new reminder info
		"""
		cursor = get_db()

		# Validate data
		if repeat_quantity is None and repeat_interval is not None:
			raise InvalidKeyValue('repeat_quantity', repeat_quantity)
		elif repeat_quantity is not None and repeat_interval is None:
			raise InvalidKeyValue('repeat_interval', repeat_interval)
		repeated_reminder = repeat_quantity is not None and repeat_interval is not None

		if time is not None:
			if not repeated_reminder:
				if time < datetime.utcnow().timestamp():
					raise InvalidTime
			time = round(time)

		# Get current data and update it with new values
		data = self.get()
		new_values = {
			'title': title,
			'time': time,
			'notification_service': notification_service,
			'text': text,
			'repeat_quantity': repeat_quantity,
			'repeat_interval': repeat_interval
		}
		for k, v in new_values.items():
			if k in ('repeat_quantity', 'repeat_interval') or v is not None:
				data[k] = v

		# Update database
		try:
			if not repeated_reminder:
				next_time = data["time"]
				cursor.execute("""
					UPDATE reminders
					SET title=?, text=?, time=?, notification_service=?, repeat_quantity=?, repeat_interval=?
					WHERE id = ?;
					""", (
						data["title"],
						data["text"],
						data["time"],
						data["notification_service"],
						data["repeat_quantity"],
						data["repeat_interval"],
						self.id
				))
			else:
				next_time = _find_next_time(data["time"], data["repeat_quantity"], data["repeat_interval"])
				cursor.execute("""
					UPDATE reminders
					SET title=?, text=?, time=?, notification_service=?, repeat_quantity=?, repeat_interval=?, original_time=?
					WHERE id = ?;
					""", (
						data["title"],
						data["text"],
						next_time,
						data["notification_service"],
						data["repeat_quantity"],
						data["repeat_interval"],
						data["time"],
						self.id
				))
		except IntegrityError:
			raise NotificationServiceNotFound
		reminder_handler.submit_next_reminder(next_time)

		return self.get()

	def delete(self) -> None:
		"""Delete the reminder
		"""		
		get_db().execute("DELETE FROM reminders WHERE id = ?", (self.id,))
		reminder_handler.submit_next_reminder(None)
		return

class Reminders:
	"""Represents the reminder library of the user account
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
				ns.title AS notification_service_title,
				r.repeat_quantity,
				r.repeat_interval
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
		reminders = list(filter(
			lambda p: filter_function(query, p),
			self.fetchall()
		))
		return reminders

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
		text: str = '',
		repeat_quantity: Literal["year", "month", "week", "day", "hours", "minutes"] = None,
		repeat_interval: int = None
	) -> Reminder:
		"""Add a reminder

		Args:
			title (str): The title of the entry
			time (int): The UTC epoch timestamp the the reminder should be send.
			notification_service (int): The id of the notification service to use to send the reminder.
			text (str, optional): The body of the reminder. Defaults to ''.
			repeat_quantity (Literal["year", "month", "week", "day", "hours", "minutes"], optional): The quantity of the repeat specified for the reminder. Defaults to None.
			repeat_interval (int, optional): The amount of repeat_quantity, like "5" (hours). Defaults to None.

		Returns:
			dict: The info about the reminder
		"""
		if time < datetime.utcnow().timestamp():
			raise InvalidTime
		time = round(time)

		if repeat_quantity is None and repeat_interval is not None:
			raise InvalidKeyValue('repeat_quantity', repeat_quantity)
		elif repeat_quantity is not None and repeat_interval is None:
			raise InvalidKeyValue('repeat_interval', repeat_interval)

		try:
			if repeat_quantity is None and repeat_interval is None:
				id = get_db().execute("""
					INSERT INTO reminders(user_id, title, text, time, notification_service)
					VALUES (?,?,?,?,?);
				""", (self.user_id, title, text, time, notification_service)
				).lastrowid
			else:
				id = get_db().execute("""
					INSERT INTO reminders(user_id, title, text, time, notification_service, repeat_quantity, repeat_interval, original_time)
					VALUES (?, ?, ?, ?, ?, ?, ?, ?);
				""", (self.user_id, title, text, time, notification_service, repeat_quantity, repeat_interval, time)
				).lastrowid
		except IntegrityError:
			raise NotificationServiceNotFound
		reminder_handler.submit_next_reminder(time)

		# Return info
		return self.fetchone(id)
