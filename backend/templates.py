#-*- coding: utf-8 -*-

from sqlite3 import IntegrityError
from typing import List, Optional, Union

from backend.custom_exceptions import (NotificationServiceNotFound,
                                       TemplateNotFound)
from backend.db import get_db
from backend.helpers import TimelessSortingMethod, search_filter
from backend.logging import LOGGER


class Template:
	"""Represents a template
	"""	
	def __init__(self, user_id: int, template_id: int) -> None:
		"""Create instance of class.

		Args:
			user_id (int): The ID of the user.
			template_id (int): The ID of the template.

		Raises:
			TemplateNotFound: Template with given ID does not exist or is not
			owned by user.
		"""
		self.id = template_id
		
		exists = get_db().execute(
			"SELECT 1 FROM templates WHERE id = ? AND user_id = ? LIMIT 1;",
			(self.id, user_id)
		).fetchone()
		if not exists:
			raise TemplateNotFound
		return

	def _get_notification_services(self) -> List[int]:
		"""Get ID's of notification services linked to the template.

		Returns:
			List[int]: The list with ID's.
		"""
		result = [
			r[0]
			for r in get_db().execute("""
				SELECT notification_service_id
				FROM reminder_services
				WHERE template_id = ?;
				""",
				(self.id,)
			)
		]
		return result

	def get(self) -> dict:
		"""Get info about the template

		Returns:
			dict: The info about the template
		"""	
		template = get_db(dict).execute("""
			SELECT
				id,
				title, text,
				color
			FROM templates
			WHERE id = ?
			LIMIT 1;
			""",
			(self.id,)
		).fetchone()
		template = dict(template)
		
		template['notification_services'] = self._get_notification_services()
		
		return template

	def update(self,
		title: Union[str, None] = None,
		notification_services: Union[List[int], None] = None,
		text: Union[str, None] = None,
		color: Union[str, None] = None
	) -> dict:
		"""Edit the template

		Args:
			title (Union[str, None]): The new title of the entry.
				Defaults to None.

			notification_services (Union[List[int], None]): The new id's of the
			notification services to use to send the reminder.
				Defaults to None.

			text (Union[str, None], optional): The new body of the template.
				Defaults to None.

			color (Union[str, None], optional): The new hex code of the color of the template,
			which is shown in the web-ui.
				Defaults to None.

		Raises:
			NotificationServiceNotFound: One of the notification services was not found

		Returns:
			dict: The new template info
		"""
		LOGGER.info(
			f'Updating template {self.id}: '
			+ f'{title=}, {notification_services=}, {text=}, {color=}'
		)

		cursor = get_db()
		
		data = self.get()
		new_values = {
			'title': title,
			'text': text,
			'color': color
		}
		for k, v in new_values.items():
			if k in ('color',) or v is not None:
				data[k] = v
				
		cursor.execute("""
			UPDATE templates
			SET title=?, text=?, color=?
			WHERE id = ?;
			""", (
				data['title'],
				data['text'],
				data['color'],
				self.id
		))
		
		if notification_services:
			cursor.connection.isolation_level = None
			cursor.execute("BEGIN TRANSACTION;")
			cursor.execute(
				"DELETE FROM reminder_services WHERE template_id = ?",
				(self.id,)
			)
			try:
				cursor.executemany("""
					INSERT INTO reminder_services(
						template_id,
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
		"""Delete the template
		"""
		LOGGER.info(f'Deleting template {self.id}')
		get_db().execute("DELETE FROM templates WHERE id = ?;", (self.id,))
		return

class Templates:
	"""Represents the template library of the user account
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
		"""Get all templates of the user.

		Args:
			sort_by (TimelessSortingMethod, optional): The sorting method of
			the resulting list.
				Defaults to TimelessSortingMethod.TITLE.

		Returns:
			List[dict]: The id, title, text and color of each template.
		"""
		templates = [
			dict(r)
			for r in get_db(dict).execute("""
				SELECT
					id,
					title, text,
					color
				FROM templates
				WHERE user_id = ?
				ORDER BY title, id;
				""",
				(self.user_id,)
			)
		]

		# Sort result
		templates.sort(key=sort_by.value[0], reverse=sort_by.value[1])

		return templates

	def search(
		self,
		query: str,
		sort_by: TimelessSortingMethod = TimelessSortingMethod.TITLE
	) -> List[dict]:
		"""Search for templates

		Args:
			query (str): The term to search for.

			sort_by (TimelessSortingMethod, optional): The sorting method of
			the resulting list.
				Defaults to TimelessSortingMethod.TITLE.

		Returns:
			List[dict]: All templates that match. Similar output to `self.fetchall`
		"""		
		templates = [
			r for r in self.fetchall(sort_by)
			if search_filter(query, r)
		]
		return templates

	def fetchone(self, id: int) -> Template:
		"""Get one template

		Args:
			id (int): The id of the template to fetch

		Returns:
			Template: A Template instance
		"""		
		return Template(self.user_id, id)
		
	def add(
		self,
		title: str,
		notification_services: List[int],
		text: str = '',
		color: Optional[str] = None
	) -> Template:
		"""Add a template

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
			Template: The info about the template
		"""
		LOGGER.info(
			f'Adding template with {title=}, {notification_services=}, {text=}, {color=}'
		)

		cursor = get_db()
		cursor.connection.isolation_level = None
		cursor.execute("BEGIN TRANSACTION;")

		id = cursor.execute("""
			INSERT INTO templates(user_id, title, text, color)
			VALUES (?,?,?,?);
			""",
			(self.user_id, title, text, color)
		).lastrowid

		try:
			cursor.executemany("""
				INSERT INTO reminder_services(
					template_id,
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
