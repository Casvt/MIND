#-*- coding: utf-8 -*-

from sqlite3 import IntegrityError
from typing import List, Optional, Union

from apprise import Apprise

from backend.custom_exceptions import (NotificationServiceNotFound,
                                       ReminderNotFound)
from backend.db import get_db
from backend.helpers import TimelessSortingMethod, search_filter
from backend.logging import LOGGER


class StaticReminder:
	"""Represents a static reminder
	"""
	def __init__(self, user_id: int, reminder_id: int) -> None:
		"""Create an instance.

		Args:
			user_id (int): The ID of the user.
			reminder_id (int): The ID of the reminder.

		Raises:
			ReminderNotFound: Reminder with given ID does not exist or is not
			owned by user.
		"""
		self.id = reminder_id
		
		# Check if reminder exists
		if not get_db().execute(
			"SELECT 1 FROM static_reminders WHERE id = ? AND user_id = ? LIMIT 1;",
			(self.id, user_id)
		).fetchone():
			raise ReminderNotFound

		return

	def _get_notification_services(self) -> List[int]:
		"""Get ID's of notification services linked to the static reminder.

		Returns:
			List[int]: The list with ID's.
		"""
		result = [
			r[0]
			for r in get_db().execute("""
				SELECT notification_service_id
				FROM reminder_services
				WHERE static_reminder_id = ?;
				""",
				(self.id,)
			)
		]
		return result

	def get(self) -> dict:
		"""Get info about the static reminder

		Returns:
			dict: The info about the static reminder
		"""
		reminder = get_db(dict).execute("""
			SELECT
				id,
				title, text,
				color
			FROM static_reminders
			WHERE id = ?
			LIMIT 1;
			""",
			(self.id,)
		).fetchone()
		reminder = dict(reminder)
		
		reminder['notification_services'] = self._get_notification_services()

		return reminder
	
	def update(
		self,
		title: Union[str, None] = None,
		notification_services: Union[List[int], None] = None,
		text: Union[str, None] = None,
		color: Union[str, None] = None
	) -> dict:
		"""Edit the static reminder.

		Args:
			title (Union[str, None], optional): The new title of the entry.
				Defaults to None.

			notification_services (Union[List[int], None], optional):
			The new id's of the notification services to use to send the reminder.
				Defaults to None.

			text (Union[str, None], optional): The new body of the reminder.
				Defaults to None.

			color (Union[str, None], optional): The new hex code of the color
			of the reminder, which is shown in the web-ui.
				Defaults to None.

		Raises:
			NotificationServiceNotFound: One of the notification services was not found

		Returns:
			dict: The new static reminder info
		"""
		LOGGER.info(
			f'Updating static reminder {self.id}: '
			+ f'{title=}, {notification_services=}, {text=}, {color=}'
		)

		# Get current data and update it with new values
		data = self.get()
		new_values = {
			'title': title,
			'text': text,
			'color': color
		}
		for k, v in new_values.items():
			if k == 'color' or v is not None:
				data[k] = v
				
		# Update database
		cursor = get_db()
		cursor.execute("""
			UPDATE static_reminders
			SET
				title = ?, text = ?,
				color = ?
			WHERE id = ?;
			""",
			(data['title'], data['text'],
			data['color'],
			self.id)
		)
		
		if notification_services:
			cursor.connection.isolation_level = None
			cursor.execute("BEGIN TRANSACTION;")
			cursor.execute(
				"DELETE FROM reminder_services WHERE static_reminder_id = ?",
				(self.id,)
			)
			try:
				cursor.executemany("""
					INSERT INTO reminder_services(
						static_reminder_id,
						notification_service_id
					)
					VALUES (?,?);
					""",
					((self.id, s) for s in notification_services)
				)
				cursor.execute("COMMIT;")

			except IntegrityError:
				raise NotificationServiceNotFound

			finally:
				cursor.connection.isolation_level = ""

		return self.get()

	def delete(self) -> None:
		"""Delete the static reminder
		"""
		LOGGER.info(f'Deleting static reminder {self.id}')
		get_db().execute("DELETE FROM static_reminders WHERE id = ?", (self.id,))
		return

class StaticReminders:
	"""Represents the static reminder library of the user account
	"""

	def __init__(self, user_id: int) -> None:
		"""Create an instance.

		Args:
			user_id (int): The ID of the user.
		"""
		self.user_id = user_id
		return
		
	def fetchall(
		self,
		sort_by: TimelessSortingMethod = TimelessSortingMethod.TITLE
	) -> List[dict]:
		"""Get all static reminders

		Args:
			sort_by (TimelessSortingMethod, optional): How to sort the result.
				Defaults to TimelessSortingMethod.TITLE.

		Returns:
			List[dict]: The id, title, text and color of each static reminder.
		"""
		reminders = [
			dict(r)
			for r in get_db(dict).execute("""
				SELECT
					id,
					title, text,
					color
				FROM static_reminders
				WHERE user_id = ?
				ORDER BY title, id;
				""",
				(self.user_id,)
			)
		]

		# Sort result
		reminders.sort(key=sort_by.value[0], reverse=sort_by.value[1])

		return reminders

	def search(
		self,
		query: str,
		sort_by: TimelessSortingMethod = TimelessSortingMethod.TITLE
	) -> List[dict]:
		"""Search for static reminders

		Args:
			query (str): The term to search for.

			sort_by (TimelessSortingMethod, optional): The sorting method of
			the resulting list.
				Defaults to TimelessSortingMethod.TITLE.

		Returns:
			List[dict]: All static reminders that match.
			Similar output to `self.fetchall`
		"""
		static_reminders = [
			r for r in self.fetchall(sort_by)
			if search_filter(query, r)
		]
		return static_reminders

	def fetchone(self, id: int) -> StaticReminder:
		"""Get one static reminder

		Args:
			id (int): The id of the static reminder to fetch

		Returns:
			StaticReminder: A StaticReminder instance
		"""
		return StaticReminder(self.user_id, id)
	
	def add(
		self,
		title: str,
		notification_services: List[int],
		text: str = '',
		color: Optional[str] = None
	) -> StaticReminder:
		"""Add a static reminder

		Args:
			title (str): The title of the entry.

			notification_services (List[int]): The id's of the
			notification services to use to send the reminder.

			text (str, optional): The body of the reminder.
				Defaults to ''.

			color (Optional[str], optional): The hex code of the color of the template,
			which is shown in the web-ui.
				Defaults to None.

		Raises:
			NotificationServiceNotFound: One of the notification services was not found

		Returns:
			StaticReminder: The info about the static reminder
		"""
		LOGGER.info(
			f'Adding static reminder with {title=}, {notification_services=}, {text=}, {color=}'
		)

		cursor = get_db()
		cursor.connection.isolation_level = None
		cursor.execute("BEGIN TRANSACTION;")

		id = cursor.execute("""
			INSERT INTO static_reminders(user_id, title, text, color)
			VALUES (?,?,?,?);
			""",
			(self.user_id, title, text, color)
		).lastrowid
		
		try:
			cursor.executemany("""
				INSERT INTO reminder_services(
					static_reminder_id,
					notification_service_id
				)
				VALUES (?, ?);
				""",
				((id, service) for service in notification_services)
			)
			cursor.execute("COMMIT;")

		except IntegrityError:
			raise NotificationServiceNotFound
		finally:
			cursor.connection.isolation_level = ""

		return self.fetchone(id)

	def trigger_reminder(self, id: int) -> None:
		"""Trigger a static reminder to send it's reminder

		Args:
			id (int): The id of the static reminder to trigger

		Raises:
			ReminderNotFound: The static reminder with the given id was not found
		"""
		LOGGER.info(f'Triggering static reminder {id}')
		cursor = get_db(dict)
		reminder = cursor.execute("""
			SELECT title, text
			FROM static_reminders
			WHERE
				id = ?
				AND user_id = ?
			LIMIT 1;
			""",
			(id, self.user_id)
		).fetchone()
		if not reminder:
			raise ReminderNotFound
		reminder = dict(reminder)

		a = Apprise()
		cursor.execute("""
			SELECT url
			FROM reminder_services rs
			INNER JOIN notification_services ns
			ON rs.notification_service_id = ns.id
			WHERE rs.static_reminder_id = ?;
			""",
			(id,)
		)
		for url in cursor:
			a.add(url['url'])
		a.notify(title=reminder['title'], body=reminder['text'] or '\u200B')
		return
