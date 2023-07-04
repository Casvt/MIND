#-*- coding: utf-8 -*-

import logging
from sqlite3 import IntegrityError
from typing import List, Literal

from backend.custom_exceptions import (NotificationServiceNotFound,
                                       TemplateNotFound)
from backend.db import get_db

filter_function = lambda query, p: (
	query in p["title"].lower()
	or query in p["text"].lower()
)

class Template:
	"""Represents a template
	"""	
	def __init__(self, user_id: int, template_id: int):
		self.id = template_id
		
		exists = get_db().execute(
			"SELECT 1 FROM templates WHERE id = ? AND user_id = ? LIMIT 1;",
			(self.id, user_id)
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
		logging.info(
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
		logging.info(f'Deleting template {self.id}')
		get_db().execute("DELETE FROM templates WHERE id = ?;", (self.id,))
		return

class Templates:
	"""Represents the template library of the user account
	"""	
	sort_functions = {
		'title': (lambda r: (r['title'], r['text'], r['color']), False),
		'title_reversed': (lambda r: (r['title'], r['text'], r['color']), True),
		'date_added': (lambda r: r['id'], False),
		'date_added_reversed': (lambda r: r['id'], True)
	}

	def __init__(self, user_id: int):
		self.user_id = user_id
		
	def fetchall(self, sort_by: Literal["title", "title_reversed", "date_added", "date_added_reversed"] = "title") -> List[dict]:
		"""Get all templates

		Args:
			sort_by (Literal["title", "title_reversed", "date_added", "date_added_reversed"], optional): How to sort the result. Defaults to "title".

		Returns:
			List[dict]: The id, title, text and color
		"""
		sort_function = self.sort_functions.get(
			sort_by,
			self.sort_functions['title']
		)

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

		# Sort result
		templates.sort(key=sort_function[0], reverse=sort_function[1])

		return templates

	def search(self, query: str, sort_by: Literal["title", "title_reversed", "date_added", "date_added_reversed"] = "title") -> List[dict]:
		"""Search for templates

		Args:
			query (str): The term to search for
			sort_by (Literal["title", "title_reversed", "date_added", "date_added_reversed"], optional): How to sort the result. Defaults to "title".

		Returns:
			List[dict]: All templates that match. Similar output to self.fetchall
		"""		
		query = query.lower()
		reminders = list(filter(
			lambda p: filter_function(query, p),
			self.fetchall(sort_by)
		))
		return reminders

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
		logging.info(
			f'Adding template with {title=}, {notification_services=}, {text=}, {color=}'
		)

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
