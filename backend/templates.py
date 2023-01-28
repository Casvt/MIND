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
		
		exists = get_db().execute("SELECT 1 FROM templates WHERE id = ? LIMIT 1;", (self.id,)).fetchone()
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
				notification_service,
				color
			FROM templates
			WHERE id = ?;
			""",
			(self.id,)
		).fetchone()
		
		return dict(template)

	def update(self,
		title: str = None,
		notification_service: int = None,
		text: str = None,
		color: str = None
	) -> dict:
		"""Edit the template

		Args:
			title (str): The new title of the entry. Defaults to None.
			notification_service (int): The new id of the notification service to use to send the reminder. Defaults to None.
			text (str, optional): The new body of the template. Defaults to None.
			color (str, optional): The new hex code of the color of the template, which is shown in the web-ui. Defaults to None.

		Returns:
			dict: The new template info
		"""
		cursor = get_db()
		
		data = self.get()
		new_values = {
			'title': title,
			'notification_service': notification_service,
			'text': text,
			'color': color
		}
		for k, v in new_values.items():
			if k in ('color',) or v is not None:
				data[k] = v
				
		try:
			cursor.execute("""
				UPDATE templates
				SET title=?, notification_service=?, text=?, color=?
				WHERE id = ?;
				""", (
					data['title'],
					data['notification_service'],
					data['text'],
					data['color'],
					self.id
			))
		except IntegrityError:
			raise NotificationServiceNotFound
		
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
			List[dict]: The id, title, text, notification_service and color
		"""
		templates: list = list(map(dict, get_db(dict).execute("""
			SELECT
				id,
				title, text,
				notification_service,
				color
			FROM templates
			WHERE user_id = ?
			ORDER BY title, id;
			""",
			(self.user_id,)
		).fetchall()))

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
		notification_service: int,
		text: str = '',
		color: str = None
	) -> Template:
		"""Add a template

		Args:
			title (str): The title of the entry
			notification_service (int): The id of the notification service to use to send the reminder.
			text (str, optional): The body of the reminder. Defaults to ''.
			color (str, optional): The hex code of the color of the template, which is shown in the web-ui. Defaults to None.

		Returns:
			Template: The info about the template
		"""	
		try:
			id = get_db().execute("""
				INSERT INTO templates(user_id, title, text, notification_service, color)
				VALUES (?,?,?,?,?);
				""",
				(self.user_id, title, text, notification_service, color)
			).lastrowid
		except IntegrityError:
			raise NotificationServiceNotFound

		return self.fetchone(id)
