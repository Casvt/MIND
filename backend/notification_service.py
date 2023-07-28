#-*- coding: utf-8 -*-

import logging
from typing import Dict, List, Union

from apprise import Apprise

from backend.custom_exceptions import (NotificationServiceInUse,
                                       NotificationServiceNotFound)
from backend.db import get_db


def _sort_tokens(t: dict) -> int:
	result = [
		int(not t['required'])
	]

	if t['type'] == 'choice':
		result.append(0)
	elif t['type'] != 'list':
		result.append(1)
	else:
		result.append(2)
	
	return result

def get_apprise_services() -> List[Dict[str, Union[str, Dict[str, list]]]]:
	apprise_services = []
	raw = Apprise().details()
	for entry in raw['schemas']:
		entry: Dict[str, Union[str, dict]]
		result: Dict[str, Union[str, Dict[str, list]]] = {
			'name': str(entry['service_name']),
			'doc_url': entry['setup_url'],
			'details': {
				'templates': entry['details']['templates'],
				'tokens': [],
				'args': []
			}
		}

		schema = entry['details']['tokens']['schema']
		result['details']['tokens'].append({
			'name': schema['name'],
			'map_to': 'schema',
			'required': schema['required'],
			'type': 'choice',
			'options': schema['values'],
			'default': schema.get('default')
		})

		handled_tokens = {'schema'}
		result['details']['tokens'] += [
			{
				'name': v['name'],
				'map_to': k,
				'required': v['required'],
				'type': 'list',
				'delim': v['delim'][0],
				'content': [
					{
						'name': content['name'],
						'required': content['required'],
						'type': content['type'],
						'prefix': content.get('prefix'),
						'regex': content.get('regex')
					}
					for content, _ in ((entry['details']['tokens'][e], handled_tokens.add(e)) for e in v['group'])
				]
			}
			for k, v in 
				filter(
					lambda t: t[1]['type'].startswith('list:'), 
	   				entry['details']['tokens'].items()
				)
		]
		handled_tokens.update(
			set(map(lambda e: e[0],
	   			filter(lambda e: e[1]['type'].startswith('list:'),
	      				entry['details']['tokens'].items())
			))
		)

		result['details']['tokens'] += [
			{
				'name': v['name'],
				'map_to': k,
				'required': v['required'],
				'type': v['type'].split(':')[0],
				**({
					'options': v.get('values'),
					'default': v.get('default')
				} if v['type'].startswith('choice') else {
					'prefix': v.get('prefix'),
					'min': v.get('min'),
					'max': v.get('max'),
					'regex': v.get('regex')
				})
			}
			for k, v in
				filter(
					lambda t: not t[0] in handled_tokens,
					entry['details']['tokens'].items()
				)
		]

		result['details']['tokens'].sort(key=_sort_tokens)

		result['details']['args'] += [
			{
				'name': v.get('name', k),
				'map_to': k,
				'required': v.get('required', False),
				'type': v['type'].split(':')[0],
				**({
					'delim': v['delim'][0],
					'content': []
				} if v['type'].startswith('list') else {
					'options': v['values'],
					'default': v.get('default')
				} if v['type'].startswith('choice') else {
					'default': v['default']
				} if v['type'] == 'bool' else {
					'min': v.get('min'),
					'max': v.get('max'),
					'regex': v.get('regex')
				})
			}
			for k, v in
				filter(
					lambda a: (
						a[1].get('alias_of') is None
						and not a[0] in ('cto', 'format', 'overflow', 'rto', 'verify')
					),
					entry['details']['args'].items()
				)
		]
		result['details']['args'].sort(key=_sort_tokens)

		apprise_services.append(result)

	apprise_services.sort(key=lambda s: s['name'].lower())

	apprise_services.insert(0, {
		'name': 'Custom URL',
		'doc_url': 'https://github.com/caronc/apprise#supported-notifications',
		'details': {
			'templates': ['{url}'],
			'tokens': [{
				'name': 'Apprise URL',
				'map_to': 'url',
				'required': True,
				'type': 'string',
				'prefix': None,
				'min': None,
				'max': None,
				'regex': None
			}],
			'args': []
		}
	})

	return apprise_services

class NotificationService:
	def __init__(self, user_id: int, notification_service_id: int) -> None:
		self.id = notification_service_id
		
		if not get_db().execute(
			"SELECT 1 FROM notification_services WHERE id = ? AND user_id = ? LIMIT 1;",
			(self.id, user_id)
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
		logging.info(f'Updating notification service {self.id}: {title=}, {url=}')

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
			SET title = ?, url = ?
			WHERE id = ?;
			""",
			(
				data["title"],
				data["url"],
				self.id
			)
		)

		return self.get()
		
	def delete(self) -> None:
		"""Delete the service

		Raises:
			NotificationServiceInUse: The service is still used by a reminder
		"""	
		logging.info(f'Deleting notification service {self.id}')
		
		# Check if no reminders exist with this service
		cursor = get_db()
		cursor.execute("""
			SELECT 1
			FROM reminder_services
			WHERE notification_service_id = ?
				AND reminder_id IS NOT NULL
			LIMIT 1;
			""",
			(self.id,)
		)
		if cursor.fetchone():
			raise NotificationServiceInUse('reminder')
			
		# Check if no templates exist with this service
		cursor.execute("""
			SELECT 1
			FROM reminder_services
			WHERE notification_service_id = ?
				AND template_id IS NOT NULL
			LIMIT 1;
			""",
			(self.id,)
		)
		if cursor.fetchone():
			raise NotificationServiceInUse('template')

		# Check if no static reminders exist with this service
		cursor.execute("""
			SELECT 1
			FROM reminder_services
			WHERE notification_service_id = ?
				AND static_reminder_id IS NOT NULL
			LIMIT 1;
			""",
			(self.id,)
		)
		if cursor.fetchone():
			raise NotificationServiceInUse('static reminder')

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
		result = list(map(dict, get_db(dict).execute("""
			SELECT
				id, title, url
			FROM notification_services
			WHERE user_id = ?
			ORDER BY title, id;
			""",
			(self.user_id,)
		)))

		return result
		
	def fetchone(self, notification_service_id: int) -> NotificationService:
		"""Get one notification service based on it's id

		Args:
			notification_service_id (int): The id of the desired service

		Returns:
			NotificationService: Instance of NotificationService
		"""		
		return NotificationService(self.user_id, notification_service_id)
		
	def add(self, title: str, url: str) -> NotificationService:
		"""Add a notification service

		Args:
			title (str): The title of the service
			url (str): The apprise url of the service

		Returns:
			dict: The info about the new service
		"""	
		logging.info(f'Adding notification service with {title=}, {url=}')

		new_id = get_db().execute("""
			INSERT INTO notification_services(user_id, title, url)
			VALUES (?,?,?)
			""",
			(self.user_id, title, url)
		).lastrowid

		return self.fetchone(new_id)
		