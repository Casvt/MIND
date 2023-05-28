#-*- coding: utf-8 -*-

from datetime import datetime
from sqlite3 import IntegrityError
from threading import Timer
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
	repeat_quantity: Literal["years", "months", "weeks", "days", "hours", "minutes"],
	repeat_interval: int
) -> int:
	td = relativedelta(**{repeat_quantity: repeat_interval})
	new_time = datetime.fromtimestamp(original_time)
	current_time = datetime.fromtimestamp(datetime.utcnow().timestamp())
	while new_time <= current_time:
		new_time += td
	return int(new_time.timestamp())

class ReminderHandler:
	"""Handle set reminders
	"""	
	def __init__(self, context) -> None:
		self.context = context
		self.next_trigger = {
			'thread': None,
			'time': None
		}

		return

	def __trigger_reminders(self, time: int) -> None:
		"""Trigger all reminders that are set for a certain time

		Args:
			time (int): The time of the reminders to trigger
		"""
		with self.context():
			cursor = get_db(dict)
			cursor.execute("""
				SELECT
					r.id,
					r.title, r.text,
					r.repeat_quantity, r.repeat_interval, r.original_time
				FROM reminders r
				WHERE time = ?;
			""", (time,))
			reminders = list(map(dict, cursor))
			
			for reminder in reminders:
				cursor.execute("""
					SELECT url
					FROM reminder_services rs
					INNER JOIN notification_services ns
					ON rs.notification_service_id = ns.id
					WHERE rs.reminder_id = ?;
				""", (reminder['id'],))
				
				# Send of reminder
				a = Apprise()
				for url in cursor:
					a.add(url['url'])
				a.notify(title=reminder["title"], body=reminder["text"])

				if reminder['repeat_quantity'] is None:
					# Delete the reminder from the database
					cursor.execute(
						"DELETE FROM reminders WHERE id = ?;",
						(reminder['id'],)
					)
				else:
					# Set next time
					new_time = _find_next_time(
						reminder['original_time'],
						reminder['repeat_quantity'],
						reminder['repeat_interval']
					)
					cursor.execute(
						"UPDATE reminders SET time = ? WHERE id = ?;",
						(new_time, reminder['id'])
					)

				self.next_trigger.update({
					'thread': None,
					'time': None
				})
				self.find_next_reminder()

	def find_next_reminder(self, time: int=None) -> None:
		"""Determine when the soonest reminder is and set the timer to that time

		Args:
			time (int, optional): The timestamp to check for. Otherwise check soonest in database. Defaults to None.
		"""
		if not time:
			with self.context():
				time = get_db().execute("""
					SELECT DISTINCT r1.time
					FROM reminders r1
					LEFT JOIN reminders r2
					ON r1.time > r2.time
					WHERE r2.id IS NULL;
				""").fetchone()
				if time is None:
					return
				time = time[0]

		if (self.next_trigger['thread'] is None
		or time < self.next_trigger['time']):
			if self.next_trigger['thread'] is not None:
				self.next_trigger['thread'].cancel()
			t = time - datetime.utcnow().timestamp()
			self.next_trigger['thread'] = Timer(t, self.__trigger_reminders, (time,))
			self.next_trigger['thread'].start()
			self.next_trigger['time'] = time
	
	def stop_handling(self) -> None:
		"""Stop the timer if it's active
		"""
		if self.next_trigger['thread'] is not None:
			self.next_trigger['thread'].cancel()
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
		if not get_db().execute(
			"SELECT 1 FROM reminders WHERE id = ? LIMIT 1",
			(self.id,)
		).fetchone():
			raise ReminderNotFound

	def get(self) -> dict:
		"""Get info about the reminder

		Returns:
			dict: The info about the reminder
		"""
		reminder = get_db(dict).execute("""
			SELECT
				id,
				title, text,
				time,
				repeat_quantity,
				repeat_interval,
				color
			FROM reminders
			WHERE id = ?
			LIMIT 1;
			""",
			(self.id,)
		).fetchone()
		reminder = dict(reminder)

		reminder['notification_services'] = list(map(lambda r: r[0], get_db().execute("""
			SELECT notification_service_id
			FROM reminder_services
			WHERE reminder_id = ?;
		""", (self.id,))))

		return reminder

	def update(
		self,
		title: str = None,
		time: int = None,
		notification_services: List[int] = None,
		text: str = None,
		repeat_quantity: Literal["years", "months", "weeks", "days", "hours", "minutes"] = None,
		repeat_interval: int = None,
		color: str = None
	) -> dict:
		"""Edit the reminder

		Args:
			title (str): The new title of the entry. Defaults to None.
			time (int): The new UTC epoch timestamp the the reminder should be send. Defaults to None.
			notification_services (List[int]): The new list of id's of the notification services to use to send the reminder. Defaults to None.
			text (str, optional): The new body of the reminder. Defaults to None.
			repeat_quantity (Literal["years", "months", "weeks", "days", "hours", "minutes"], optional): The new quantity of the repeat specified for the reminder. Defaults to None.
			repeat_interval (int, optional): The new amount of repeat_quantity, like "5" (hours). Defaults to None.
			color (str, optional): The new hex code of the color of the reminder, which is shown in the web-ui. Defaults to None.

		Raises:
			NotificationServiceNotFound: One of the notification services was not found

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
			'text': text,
			'repeat_quantity': repeat_quantity,
			'repeat_interval': repeat_interval,
			'color': color
		}
		for k, v in new_values.items():
			if k in ('repeat_quantity', 'repeat_interval', 'color') or v is not None:
				data[k] = v

		# Update database
		if not repeated_reminder:
			next_time = data["time"]
			cursor.execute("""
				UPDATE reminders
				SET
					title=?, text=?,
					time=?,
					repeat_quantity=?, repeat_interval=?,
					color=?
				WHERE id = ?;
				""", (
					data["title"],
					data["text"],
					data["time"],
					data["repeat_quantity"],
					data["repeat_interval"],
					data["color"],
					self.id
			))
		else:
			next_time = _find_next_time(
				data["time"],
				data["repeat_quantity"], data["repeat_interval"]
			)
			cursor.execute("""
				UPDATE reminders
				SET
					title=?, text=?,
					time=?,
					repeat_quantity=?, repeat_interval=?, original_time=?,
					color=?
				WHERE id = ?;
				""", (
					data["title"],
					data["text"],
					next_time,
					data["repeat_quantity"],
					data["repeat_interval"],
					data["time"],
					data["color"],
					self.id
			))

		if notification_services:
			cursor.connection.isolation_level = None
			cursor.execute("BEGIN TRANSACTION;")
			cursor.execute("DELETE FROM reminder_services WHERE reminder_id = ?", (self.id,))
			try:
				cursor.executemany(
					"INSERT INTO reminder_services(reminder_id, notification_service_id) VALUES (?,?)",
					((self.id, s) for s in notification_services)
				)
				cursor.execute("COMMIT;")
			except IntegrityError:
				raise NotificationServiceNotFound
			cursor.connection.isolation_level = ""

		reminder_handler.find_next_reminder(next_time)
		return self.get()

	def delete(self) -> None:
		"""Delete the reminder
		"""		
		get_db().execute("DELETE FROM reminders WHERE id = ?", (self.id,))
		reminder_handler.find_next_reminder()
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
			List[dict]: The id, title, text, time and color of each reminder
		"""		
		sort_function = self.sort_functions.get(
			sort_by,
			self.sort_functions['time']
		)

		# Fetch all reminders
		reminders: list = list(map(dict, get_db(dict).execute("""
			SELECT
				id,
				title, text,
				time,
				repeat_quantity,
				repeat_interval,
				color
			FROM reminders
			WHERE user_id = ?;
			""",
			(self.user_id,)
		)))

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
		notification_services: List[int],
		text: str = '',
		repeat_quantity: Literal["years", "months", "weeks", "days", "hours", "minutes"] = None,
		repeat_interval: int = None,
		color: str = None
	) -> Reminder:
		"""Add a reminder

		Args:
			title (str): The title of the entry
			time (int): The UTC epoch timestamp the the reminder should be send.
			notification_services (List[int]): The id's of the notification services to use to send the reminder.
			text (str, optional): The body of the reminder. Defaults to ''.
			repeat_quantity (Literal["years", "months", "weeks", "days", "hours", "minutes"], optional): The quantity of the repeat specified for the reminder. Defaults to None.
			repeat_interval (int, optional): The amount of repeat_quantity, like "5" (hours). Defaults to None.
			color (str, optional): The hex code of the color of the reminder, which is shown in the web-ui. Defaults to None.

		Raises:
			NotificationServiceNotFound: One of the notification services was not found

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

		cursor = get_db()
		if repeat_quantity is None and repeat_interval is None:
			id = cursor.execute("""
				INSERT INTO reminders(user_id, title, text, time, color)
				VALUES (?, ?, ?, ?, ?);
			""", (self.user_id, title, text, time, color)
			).lastrowid
		else:
			id = cursor.execute("""
				INSERT INTO reminders(user_id, title, text, time, repeat_quantity, repeat_interval, original_time, color)
				VALUES (?, ?, ?, ?, ?, ?, ?, ?);
			""", (self.user_id, title, text, time, repeat_quantity, repeat_interval, time, color)
			).lastrowid
			
		try:
			cursor.executemany(
				"INSERT INTO reminder_services(reminder_id, notification_service_id) VALUES (?, ?);",
				((id, service) for service in notification_services)
			)
		except IntegrityError:
			raise NotificationServiceNotFound
		
		reminder_handler.find_next_reminder(time)

		# Return info
		return self.fetchone(id)

def test_reminder(
	title: str,
	notification_services: List[int],
	text: str = ''
) -> None:
	"""Test send a reminder draft

	Args:
		title (str): Title title of the entry
		notification_service (int): The id of the notification service to use to send the reminder
		text (str, optional): The body of the reminder. Defaults to ''.
	"""
	a = Apprise()
	cursor = get_db(dict)
	for service in notification_services:
		url = cursor.execute(
			"SELECT url FROM notification_services WHERE id = ? LIMIT 1;",
			(service,)
		).fetchone()
		if not url:
			raise NotificationServiceNotFound
		a.add(url[0])
	a.notify(title=title, body=text)
	return
