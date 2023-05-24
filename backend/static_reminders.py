#-*- coding: utf-8 -*-

from sqlite3 import IntegrityError
from typing import List

from apprise import Apprise

from backend.custom_exceptions import NotificationServiceNotFound, ReminderNotFound
from backend.db import get_db


class StaticReminder:
	"""Represents a static reminder
	"""
	def __init__(self, reminder_id: int) -> None:
		self.id = reminder_id
		
		# Check if reminder exists
		if not get_db().execute(
			"SELECT 1 FROM static_reminders WHERE id = ? LIMIT 1;",
			(self.id,)
		).fetchone():
			raise ReminderNotFound
		
	def get(self) -> dict:
		"""Get info about the static reminder

		Returns:
			dict: The info about the reminder
		"""
		reminder = get_db(dict).execute("""
			SELECT
				r.id,
				r.title, r.text,
				r.notification_service,
				ns.title AS notification_service_title,
				r.color
			FROM static_reminders r
			INNER JOIN notification_services ns
			ON r.notification_service = ns.id
			WHERE r.id = ?
			LIMIT 1;
			""",
			(self.id,)
		).fetchone()
		
		return dict(reminder)
	
	def update(
		self,
		title: str = None,
		notification_service: int = None,
		text: str = None,
		color: str = None
	) -> dict:
		"""Edit the static reminder

		Args:
			title (str, optional): The new title of the entry. Defaults to None.
			notification_service (int, optional): The new id of the notification service to use to send the reminder. Defaults to None.
			text (str, optional): The new body of the reminder. Defaults to None.
			color (str, optional): The new hex code of the color of the reminder, which is shown in the web-ui. Defaults to None.

		Raises:
			NotificationServiceNotFound: The notification service with the given id was not found

		Returns:
			dict: The new static reminder info
		"""		
		# Get current data and update it with new values
		data = self.get()
		new_values = {
			'title': title,
			'notification_service': notification_service,
			'text': text,
			'color': color
		}
		for k, v in new_values.items():
			if k == 'color' or v is not None:
				data[k] = v
				
		# Update database
		try:
			get_db().execute("""
				UPDATE static_reminders
				SET
					title = ?, text = ?,
					notification_service = ?,
					color = ?
				WHERE id = ?;
				""",
				(data['title'], data['text'],
     			data['notification_service'],
				data['color'],
				self.id)
			)
		except IntegrityError:
			raise NotificationServiceNotFound

		return self.get()

	def delete(self) -> None:
		"""Delete the static reminder
		"""
		get_db().execute("DELETE FROM static_reminders WHERE id = ?", (self.id,))
		return

class StaticReminders:
	"""Represents the static reminder library of the user account
	"""
	
	def __init__(self, user_id: int) -> None:
		self.user_id = user_id
		
	def fetchall(self) -> List[dict]:
		"""Get all static reminders

		Returns:
			List[dict]: The id, title, text, notification_service, notification_service_title and color of each static reminder
		"""		
		reminders: list = list(map(
			dict,
			get_db(dict).execute("""
				SELECT
					r.id,
					r.title, r.text,
					r.notification_service,
					ns.title AS notification_service_title,
					r.color
				FROM static_reminders r
				INNER JOIN notification_services ns
				ON r.notification_service = ns.id
				WHERE r.user_id = ?
				ORDER BY r.title, r.id;
				""",
				(self.user_id,)
			)
		))
		
		return reminders
	
	def fetchone(self, id: int) -> StaticReminder:
		"""Get one static reminder

		Args:
			id (int): The id of the static reminder to fetch

		Returns:
			StaticReminder: A StaticReminder instance
		"""
		return StaticReminder(id)
	
	def add(
		self,
		title: str,
		notification_service: int,
		text: str = '',
		color: str = None
	) -> StaticReminder:
		"""Add a static reminder

		Args:
			title (str): The title of the entry
			notification_service (int): The id of the notification service to use to send the reminder.
			text (str, optional): The body of the reminder. Defaults to ''.
			color (str, optional): The hex code of the color of the reminder, which is shown in the web-ui. Defaults to None.

		Raises:
			NotificationServiceNotFound: The notification service with the given id was not found

		Returns:
			StaticReminder: A StaticReminder instance representing the newly created static reminder
		"""
		try:
			id = get_db().execute("""
				INSERT INTO static_reminders(user_id, title, text, notification_service, color)
				VALUES (?,?,?,?,?);
				""",
				(self.user_id, title, text, notification_service, color)
			).lastrowid
		except IntegrityError:
			raise NotificationServiceNotFound
		
		return self.fetchone(id)

	def trigger_reminder(self, id: int) -> None:
		"""Trigger a static reminder to send it's reminder

		Args:
			id (int): The id of the static reminder to trigger

		Raises:
			ReminderNotFound: The static reminder with the given id was not found
		"""
		reminder = get_db(dict).execute("""
			SELECT r.title, r.text, ns.url
			FROM static_reminders r
			INNER JOIN notification_services ns
			ON r.notification_service = ns.id
			WHERE r.id = ?;
		""", (id,)).fetchone()
		if not reminder:
			raise ReminderNotFound
		reminder = dict(reminder)

		a = Apprise()
		a.add(reminder['url'])
		a.notify(title=reminder['title'], body=reminder['text'])
		return
