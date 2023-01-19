#-*- coding: utf-8 -*-

from typing import Any, Dict

class UsernameTaken(Exception):
	"""The username is already taken"""
	api_response = {'error': 'UsernameTaken', 'result': {}, 'code': 400}

class UsernameInvalid(Exception):
	"""The username contains invalid characters"""
	api_response = {'error': 'UsernameInvalid', 'result': {}, 'code': 400}

class UserNotFound(Exception):
	"""The user requested by id or username can not be found"""
	api_response = {'error': 'UserNotFound', 'result': {}, 'code': 404}

class AccessUnauthorized(Exception):
	"""The password given is not correct"""
	api_response = {'error': 'AccessUnauthorized', 'result': {}, 'code': 401}

class ReminderNotFound(Exception):
	"""The reminder with the id can not be found"""
	api_response = {'error': 'ReminderNotFound', 'result': {}, 'code': 404}

class NotificationServiceNotFound(Exception):
	"""The notification service was not found"""
	api_response = {'error': 'NotificationServiceNotFound', 'result': {}, 'code': 404}

class NotificationServiceInUse(Exception):
	"""The notification service is wished to be deleted but a reminder is still using it"""
	def __init__(self, type: str=''):
		self.type = type
		super().__init__(self.type)

	@property
	def api_response(self) -> Dict[str, Any]:
		return {'error': 'NotificationServiceInUse', 'result': {'type': self.type}, 'code': 400}

class InvalidTime(Exception):
	"""The time given is in the past"""
	api_response = {'error': 'InvalidTime', 'result': {}, 'code': 400}

class InvalidURL(Exception):
	"""The apprise url is invalid"""
	api_response = {'error': 'InvalidURL', 'result': {}, 'code': 400}

class KeyNotFound(Exception):
	"""A key was not found in the input that is required to be given"""	
	def __init__(self, key: str=''):
		self.key = key
		super().__init__(self.key)

	@property
	def api_response(self) -> Dict[str, Any]:
		return {'error': 'KeyNotFound', 'result': {'key': self.key}, 'code': 400}

class InvalidKeyValue(Exception):
	"""The value of a key is invalid"""	
	def __init__(self, key: str='', value: str=''):
		self.key = key
		self.value = value
		super().__init__(self.key)

	@property
	def api_response(self) -> Dict[str, Any]:
		return {'error': 'InvalidKeyValue', 'result': {'key': self.key, 'value': self.value}, 'code': 400}

class TemplateNotFound(Exception):
	"""The template was not found"""
	api_response = {'error': 'TemplateNotFound', 'result': {}, 'code': 404}
