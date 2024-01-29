#-*- coding: utf-8 -*-

import logging
from typing import Any, Dict

class CustomException(Exception):
	def __init__(self, e=None) -> None:
		logging.warning(self.__doc__)
		super().__init__(e)
		return

class UsernameTaken(CustomException):
	"""The username is already taken"""
	api_response = {'error': 'UsernameTaken', 'result': {}, 'code': 400}

class UsernameInvalid(CustomException):
	"""The username contains invalid characters"""
	api_response = {'error': 'UsernameInvalid', 'result': {}, 'code': 400}

class UserNotFound(CustomException):
	"""The user requested can not be found"""
	api_response = {'error': 'UserNotFound', 'result': {}, 'code': 404}

class AccessUnauthorized(CustomException):
	"""The password given is not correct"""
	api_response = {'error': 'AccessUnauthorized', 'result': {}, 'code': 401}

class ReminderNotFound(CustomException):
	"""The reminder with the id can not be found"""
	api_response = {'error': 'ReminderNotFound', 'result': {}, 'code': 404}

class NotificationServiceNotFound(CustomException):
	"""The notification service was not found"""
	api_response = {'error': 'NotificationServiceNotFound', 'result': {}, 'code': 404}

class NotificationServiceInUse(CustomException):
	"""The notification service is wished to be deleted but a reminder is still using it"""
	def __init__(self, type: str=''):
		self.type = type
		super().__init__(self.type)

	@property
	def api_response(self) -> Dict[str, Any]:
		return {'error': 'NotificationServiceInUse', 'result': {'type': self.type}, 'code': 400}

class InvalidTime(CustomException):
	"""The time given is in the past"""
	api_response = {'error': 'InvalidTime', 'result': {}, 'code': 400}

class KeyNotFound(CustomException):
	"""A key was not found in the input that is required to be given"""	
	def __init__(self, key: str=''):
		self.key = key
		super().__init__(self.key)

	@property
	def api_response(self) -> Dict[str, Any]:
		return {'error': 'KeyNotFound', 'result': {'key': self.key}, 'code': 400}

class InvalidKeyValue(CustomException):
	"""The value of a key is invalid"""	
	def __init__(self, key: str='', value: str=''):
		self.key = key
		self.value = value
		super().__init__(self.key)

	@property
	def api_response(self) -> Dict[str, Any]:
		return {'error': 'InvalidKeyValue', 'result': {'key': self.key, 'value': self.value}, 'code': 400}

class TemplateNotFound(CustomException):
	"""The template was not found"""
	api_response = {'error': 'TemplateNotFound', 'result': {}, 'code': 404}

class APIKeyInvalid(CustomException):
	"""The API key is not correct"""
	api_response = {'error': 'APIKeyInvalid', 'result': {}, 'code': 401}
	
	def __init__(self, e=None) -> None:
		return

class APIKeyExpired(CustomException):
	"""The API key has expired"""
	api_response = {'error': 'APIKeyExpired', 'result': {}, 'code': 401}

	def __init__(self, e=None) -> None:
		return

class NewAccountsNotAllowed(CustomException):
	"""It's not allowed to create a new account"""
	api_response = {'error': 'NewAccountsNotAllowed', 'result': {}, 'code': 403}
