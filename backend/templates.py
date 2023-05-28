#-*- coding: utf-8 -*-

from sqlite3 import IntegrityError
from typing import List

from backend.custom_exceptions import (NotificationServiceNotFound,
                                       TemplateNotFound)
from backend.db import get_db


class Template:
	"""Represents a template
	"""	
	def __init__(self, template_id: int):
		self.id = template_id
		
		exists = get_db().execute(
			"SELECT 1 FROM templates WHERE id = ? LIMIT 1;",
			(self.id,)
		).fetchone()
		if not exists:
			raise TemplateNotFound
			
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
		
		template['notification_services'] = list(map(lambda r: r[0], get_db().execute("""
			SELECT notification_service_id
			FROM reminder_services
			WHERE template_id = ?;
		""", (self.id,))))
		
		return template

	def update(self,
		title: str = None,
		notification_services: List[int] = None,
		text: str = None,
		color: str = None
	) -> dict:
		"""Edit the template

		Args:
			title (str): The new title of the entry. Defaults to None.
			notification_services (List[int]): The new id's of the notification services to use to send the reminder. Defaults to None.
			text (str, optional): The new body of the template. Defaults to None.
			color (str, optional): The new hex code of the color of the template, which is shown in the web-ui. Defaults to None.

		Returns:
			dict: The new template info
		"""
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
			cursor.execute("DELETE FROM reminder_services WHERE template_id = ?", (self.id,))
			try:
				cursor.executemany(
					"INSERT INTO reminder_services(template_id, notification_service_id) VALUES (?,?)",
					((self.id, s) for s in notification_services)
				)
				cursor.execute("COMMIT;")
			except IntegrityError:
				raise NotificationServiceNotFound
			cursor.connection.isolation_level = ""
		
		return self.get()
		
	def delete(self) -> None:
		"""Delete the template
		"""
		get_db().execute("DELETE FROM templates WHERE id = ?;", (self.id,))
		return

class Templates:
	"""Represents the template library of the user account
	"""	
	def __init__(self, user_id: int):
		self.user_id = user_id
		
	def fetchall(self) -> List[dict]:
		"""Get all templates

		Returns:
			List[dict]: The id, title, text and color
		"""
		templates: list = list(map(dict, get_db(dict).execute("""
			SELECT
				id,
				title, text,
				color
			FROM templates
			WHERE user_id = ?
			ORDER BY title, id;
			""",
			(self.user_id,)
		)))

		return templates

	def fetchone(self, id: int) -> Template:
		"""Get one template

		Args:
			id (int): The id of the template to fetch

		Returns:
			Template: A Template instance
		"""		
		return Template(id)
		
	def add(
		self,
		title: str,
		notification_services: List[int],
		text: str = '',
		color: str = None
	) -> Template:
		"""Add a template

		Args:
			title (str): The title of the entry
			notification_services (List[int]): The id's of the notification services to use to send the reminder.
			text (str, optional): The body of the reminder. Defaults to ''.
			color (str, optional): The hex code of the color of the template, which is shown in the web-ui. Defaults to None.

		Returns:
			Template: The info about the template
		"""	
		cursor = get_db()
		id = cursor.execute("""
			INSERT INTO templates(user_id, title, text, color)
			VALUES (?,?,?,?);
			""",
			(self.user_id, title, text, color)
		).lastrowid
		
		try:
			cursor.executemany(
				"INSERT INTO reminder_services(template_id, notification_service_id) VALUES (?, ?);",
				((id, service) for service in notification_services)
			)
		except IntegrityError:
			raise NotificationServiceNotFound

		return self.fetchone(id)
