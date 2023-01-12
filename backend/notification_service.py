#-*- coding: utf-8 -*-

from typing import List

from apprise import Apprise

from backend.custom_exceptions import (InvalidURL, NotificationServiceInUse,
                                       NotificationServiceNotFound)
from backend.db import get_db

class NotificationService:
	def __init__(self, notification_service_id: int) -> None:
		self.id = notification_service_id
		
		if not get_db().execute(
			"SELECT 1 FROM notification_services WHERE id = ? LIMIT 1",
			(self.id,)
		).fetchone():
			raise NotificationServiceNotFound
			
	def get(self) -> dict:
		"""Get the info about the notification service

		Returns:
			dict: The info about the notification service
		"""		
		result = dict(get_db(dict).execute(
			"SELECT id, title, url FROM notification_services WHERE id = ? LIMIT 1",
			(self.id,)
		).fetchone())
	
		return result
		
	def update(
		self,
		title: str = None,
		url: str = None
	) -> dict:
		"""Edit the notification service

		Args:
			title (str, optional): The new title of the service. Defaults to None.
			url (str, optional): The new url of the service. Defaults to None.

		Returns:
			dict: The new info about the service
		"""	
		if not Apprise().add(url):
			raise InvalidURL
		
		# Get current data and update it with new values
		data = self.get()
		new_values = {
			'title': title,
			'url': url
		}
		for k, v in new_values.items():
			if v is not None:
				data[k] = v

		# Update database
		get_db().execute("""
			UPDATE notification_services
			SET title=?, url=?
			WHERE id = ?;
			""", (
				data["title"],
				data["url"],
				self.id
		))

		return self.get()
		
	def delete(self) -> None:
		"""Delete the service

		Raises:
			NotificationServiceInUse: The service is still used by a reminder
		"""		
		# Check if no reminders exist with this service
		cursor = get_db()
		cursor.execute(
			"SELECT id FROM reminders WHERE notification_service = ? LIMIT 1",
			(self.id,)
		)
		if cursor.fetchone():
			raise NotificationServiceInUse
		
		cursor.execute(
			"DELETE FROM notification_services WHERE id = ?",
			(self.id,)
		)
		return

class NotificationServices:
	def __init__(self, user_id: int) -> None:
		self.user_id = user_id
	
	def fetchall(self) -> List[dict]:
		"""Get a list of all notification services

		Returns:
			List[dict]: The list of all notification services
		"""		
		result = list(map(dict, get_db(dict).execute(
			"SELECT id, title, url FROM notification_services WHERE user_id = ? ORDER BY title, id",
			(self.user_id,)
		).fetchall()))

		return result
		
	def fetchone(self, notification_service_id: int) -> NotificationService:
		"""Get one notification service based on it's id

		Args:
			notification_service_id (int): The id of the desired service

		Returns:
			NotificationService: Instance of NotificationService
		"""		
		return NotificationService(notification_service_id)
		
	def add(self, title: str, url: str) -> NotificationService:
		"""Add a notification service

		Args:
			title (str): The title of the service
			url (str): The apprise url of the service

		Raises:
			InvalidURL: The apprise url is invalid

		Returns:
			dict: The info about the new service
		"""		
		if not Apprise().add(url):
			raise InvalidURL
		
		new_id = get_db().execute("""
			INSERT INTO notification_services(user_id, title, url)
			VALUES (?,?,?)
			""",
			(self.user_id, title, url)
		).lastrowid

		return self.fetchone(new_id)
		