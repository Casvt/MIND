#-*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from os import urandom
from re import compile
from time import time as epoch_time
from typing import Any, Dict, List, Tuple

from apprise import Apprise
from flask import Blueprint, g, request

from backend.custom_exceptions import (AccessUnauthorized, InvalidKeyValue,
                                       InvalidTime, KeyNotFound,
                                       NotificationServiceInUse,
                                       NotificationServiceNotFound,
                                       ReminderNotFound, UsernameInvalid,
                                       UsernameTaken, UserNotFound)
from backend.notification_service import (NotificationService,
                                          NotificationServices)
from backend.reminders import Reminders, reminder_handler
from backend.static_reminders import StaticReminders
from backend.templates import Template, Templates
from backend.users import User, register_user

api_prefix = "/api"
api = Blueprint('api', __name__)
api_key_map = {}
color_regex = compile(r'#[0-9a-f]{6}')

"""
AUTHENTICATION:
	After making a POST /auth/login request, you'll receive an api_key in the output.
	From then on, make all requests with the url parameter api_key, where the value is the string you received.
	One hour after logging in, the api key expires and you are required to login again to get a new api_key.

	If no api key is supplied or it is invalid, 401 'ApiKeyInvalid' is returned.
	If the api key supplied has expired, 401 'ApiKeyExpired' is returned.
"""

def return_api(result: Any, error: str=None, code: int=200) -> Tuple[dict, int]:
	return {'error': error, 'result': result}, code

def auth(method):
	"""Used as decorator and, if applied to route, restricts the route to authorized users and supplies user specific info
	"""
	def wrapper(*args,**kwargs):
		hashed_api_key = hash(request.values.get('api_key',''))
		if not hashed_api_key in api_key_map:
			return return_api({}, 'ApiKeyInvalid', 401)
		
		exp = api_key_map[hashed_api_key]['exp']
		if exp <= epoch_time():
			return return_api({}, 'ApiKeyExpired', 401)
		
		# Api key valid
		g.hashed_api_key = hashed_api_key
		g.exp = exp
		g.user_data = api_key_map[hashed_api_key]['user_data']
		return method(*args, **kwargs)

	wrapper.__name__ = method.__name__
	return wrapper

def error_handler(method):
	"""Catches the errors that can occur in the endpoint and returns the correct api error
	"""
	def wrapper(*args, **kwargs):
		try:
			return method(*args, **kwargs)
		except (UsernameTaken, UsernameInvalid, UserNotFound,
				AccessUnauthorized,
				ReminderNotFound, NotificationServiceNotFound,
				NotificationServiceInUse, InvalidTime,
				KeyNotFound, InvalidKeyValue) as e:
			return return_api(**e.api_response)

	wrapper.__name__ = method.__name__
	return wrapper

#===================
# Input validation
#===================

class DataSource:
	DATA = 1
	VALUES = 2

class InputVariable(ABC):
	@abstractmethod
	def __init__(self, value: Any) -> None:
		pass
	
	@property
	@abstractmethod
	def name() -> str:
		pass
	
	@abstractmethod
	def validate(self) -> bool:
		pass

	@property
	@abstractmethod
	def required() -> bool:
		pass

	@property
	@abstractmethod
	def default() -> Any:
		pass

	@property
	@abstractmethod
	def source() -> int:
		pass

	@property
	@abstractmethod
	def description() -> str:
		pass

class DefaultInputVariable(InputVariable):
	source = DataSource.DATA
	required = True
	default = None
	
	def __init__(self, value: Any) -> None:
		self.value = value

	def validate(self) -> bool:
		return isinstance(self.value, str) and self.value

class NonRequiredVersion(InputVariable):
	required = False
	
	def validate(self) -> bool:
		return self.value is None or super().validate()

class UsernameVariable(DefaultInputVariable):
	name = 'username'
	description = 'The username of the user account'

class PasswordVariable(DefaultInputVariable):
	name = 'password'
	description = 'The password of the user account'

class NewPasswordVariable(PasswordVariable):
	name = 'new_password'
	description = 'The new password of the user account'

class TitleVariable(DefaultInputVariable):
	name = 'title'
	description = 'The title of the entry'

class URLVariable(DefaultInputVariable):
	name = 'url'
	description = 'The Apprise URL of the notification service'
	
	def validate(self) -> bool:
		return Apprise().add(self.value)

class EditTitleVariable(NonRequiredVersion, TitleVariable):
	pass
	
class EditURLVariable(NonRequiredVersion, URLVariable):
	pass

class SortByVariable(DefaultInputVariable):
	name = 'sort_by'
	description = "How to sort the result. Allowed values are 'title', 'title_reversed', 'time', 'time_reversed', 'date_added' and 'date_added_reversed'"
	required = False
	source = DataSource.VALUES
	_options = Reminders.sort_functions
	default = next(iter(Reminders.sort_functions))

	def __init__(self, value: str) -> None:
		self.value = value

	def validate(self) -> bool:
		return self.value in self._options

class TemplateSortByVariable(SortByVariable):
	description = "How to sort the result. Allowed values are 'title', 'title_reversed', 'date_added' and 'date_added_reversed'"
	_options = Templates.sort_functions
	default = next(iter(Templates.sort_functions))

class StaticReminderSortByVariable(TemplateSortByVariable):
	_options = StaticReminders.sort_functions
	default = next(iter(StaticReminders.sort_functions))

class TimeVariable(DefaultInputVariable):
	name = 'time'
	description = 'The UTC epoch timestamp that the reminder should be sent at'
	
	def validate(self) -> bool:
		return isinstance(self.value, (float, int))

class EditTimeVariable(NonRequiredVersion, TimeVariable):
	pass

class NotificationServicesVariable(DefaultInputVariable):
	name = 'notification_services'
	description = "Array of the id's of the notification services to use to send the notification"
	
	def validate(self) -> bool:
		if not isinstance(self.value, list):
			return False
		if not self.value:
			return False
		for v in self.value:
			if not isinstance(v, int):
				return False
		return True

class EditNotificationServicesVariable(NonRequiredVersion, NotificationServicesVariable):
	pass

class TextVariable(NonRequiredVersion, DefaultInputVariable):
	name = 'text'
	description = 'The body of the entry'
	default = ''
	
	def validate(self) -> bool:
		return isinstance(self.value, str)

class RepeatQuantityVariable(DefaultInputVariable):
	name = 'repeat_quantity'
	description = 'The quantity of the repeat_interval'
	required = False
	_options = ("years", "months", "weeks", "days", "hours", "minutes")
	default = None
	
	def validate(self) -> bool:
		return self.value is None or self.value in self._options

class RepeatIntervalVariable(DefaultInputVariable):
	name = 'repeat_interval'
	description = 'The number of the interval'
	required = False
	default = None
	
	def validate(self) -> bool:
		return self.value is None or isinstance(self.value, int)

class ColorVariable(DefaultInputVariable):
	name = 'color'
	description = 'The hex code of the color of the entry, which is shown in the web-ui'
	required = False
	default = None
	
	def validate(self) -> None:
		return self.value is None or color_regex.search(self.value)

class QueryVariable(DefaultInputVariable):
	name = 'query'
	description = 'The search term'
	source = DataSource.VALUES

endpoint_variables: Dict[str, Dict[str, List[InputVariable]]] = {
	'/auth/login': {
		'POST': [UsernameVariable, PasswordVariable]
	},
	'/user/add': {
		'POST': [UsernameVariable, PasswordVariable]
	},
	'/user': {
		'PUT': [NewPasswordVariable]
	},
	'/notificationservices': {
		'POST': [TitleVariable, URLVariable]
	},
	'/notificationservices/<int:n_id>': {
		'PUT': [EditTitleVariable, EditURLVariable]
	},
	'/reminders': {
		'GET': [SortByVariable],
		'POST': [TitleVariable, TimeVariable,
			NotificationServicesVariable, TextVariable,
			RepeatQuantityVariable, RepeatIntervalVariable,
			ColorVariable]
	},
	'/reminders/search': {
		'GET': [SortByVariable, QueryVariable]
	},
	'/reminders/test': {
		'POST': [TitleVariable, NotificationServicesVariable,
	   			TextVariable]
	},
	'/reminders/<int:r_id>': {
		'PUT': [EditTitleVariable, EditTimeVariable,
	  			EditNotificationServicesVariable, TextVariable,
				RepeatQuantityVariable, RepeatIntervalVariable,
				ColorVariable]
	},
	'/templates': {
		'GET': [TemplateSortByVariable],
		'POST': [TitleVariable, NotificationServicesVariable,
	   			TextVariable, ColorVariable]
	},
	'/templates/search': {
		'GET': [TemplateSortByVariable, QueryVariable]
	},
	'/templates/<int:t_id>': {
		'PUT': [EditTitleVariable, EditNotificationServicesVariable,
	  			TextVariable, ColorVariable]
	},
	'/staticreminders': {
		'GET': [StaticReminderSortByVariable],
		'POST': [TitleVariable, NotificationServicesVariable,
	   			TextVariable, ColorVariable]
	},
	'/staticreminders/search': {
		'GET': [StaticReminderSortByVariable, QueryVariable]
	},
	'/staticreminders/<int:r_id>': {
		'PUT': [EditTitleVariable, EditNotificationServicesVariable,
	  			TextVariable, ColorVariable]
	}
}

def input_validation(method):
	"""Checks, extracts and transforms inputs
	"""
	def wrapper(*args, **kwargs):
		inputs = {}
		endpoint = request.url_rule.rule.split(api_prefix)[1]
		input_variables = endpoint_variables.get(endpoint, {}).get(request.method)
		if input_variables is not None:
			given_variables = {}
			given_variables[DataSource.DATA] = request.get_json() if request.data else {}
			given_variables[DataSource.VALUES] = request.values

			for input_variable in input_variables:
				if (
					input_variable.required and
					not input_variable.name in given_variables[input_variable.source]
				):
					raise KeyNotFound(input_variable.name)

				input_value = given_variables[input_variable.source].get(input_variable.name, input_variable.default)
				
				if not input_variable(input_value).validate():
					raise InvalidKeyValue(input_variable.name, input_value)
				
				inputs[input_variable.name] = input_value
		
		return method(inputs, *args, **kwargs)

	wrapper.__name__ = method.__name__
	return wrapper

#===================
# Authentication endpoints
#===================

@api.route('/auth/login', methods=['POST'])
@error_handler
@input_validation
def api_login(inputs: Dict[str, str]):
	"""
	Endpoint: /auth/login
	Description: Login to a user account
	Requires being logged in: No
	Methods:
		POST:
			Parameters (body):
				username (required): the username of the user account
				password (required): the password of the user account
			Returns:
				200:
					The apikey to use for further requests and expiration time (epoch)
				400:
					KeyNotFound: One of the required parameters was not given
				401:
					PasswordInvalid: The password given is not correct for the user account
				404:
					UsernameNotFound: The username was not found
	"""

	user = User(inputs['username'], inputs['password'])

	# Generate an API key until one
	# is generated that isn't used already
	while True:
		api_key = urandom(16).hex() # <- length api key / 2
		hashed_api_key = hash(api_key)
		if not hashed_api_key in api_key_map:
			break

	exp = epoch_time() + 3600
	api_key_map.update({
		hashed_api_key: {
			'exp': exp,
			'user_data': user
		}
	})

	result = {'api_key': api_key, 'expires': exp}
	return return_api(result)

@api.route('/auth/logout', methods=['POST'])
@error_handler
@auth
def api_logout():
	"""
	Endpoint: /auth/logout
	Description: Logout of a user account
	Requires being logged in: Yes
	Methods:
		POST:
			Returns:
				200:
					Logout successful
	"""
	api_key_map.pop(g.hashed_api_key)
	return return_api({})

@api.route('/auth/status', methods=['GET'])
@error_handler
@auth
def api_status():
	"""
	Endpoint: /auth/status
	Description: Get current status of login
	Requires being logged in: Yes
	Methods:
		GET:
			Returns:
				200:
					The username of the logged in account and the expiration time of the api key (epoch)
	"""
	result = {
		'expires': api_key_map[g.hashed_api_key]['exp'],
		'username': api_key_map[g.hashed_api_key]['user_data'].username
	}
	return return_api(result)

#===================
# User endpoints
#===================

@api.route('/user/add', methods=['POST'])
@error_handler
@input_validation
def api_add_user(inputs: Dict[str, str]):
	"""
	Endpoint: /user/add
	Description: Create a new user account
	Requires being logged in: No
	Methods:
		POST:
			Parameters (body):
				username (required): the username of the new user account
				password (required): the password of the new user account
			Returns:
				201:
					The user id of the new user account
				400:
					KeyNotFound: One of the required parameters was not given
					UsernameInvalid: The username given is not allowed
					UsernameTaken: The username given is already in use
	"""
	user_id = register_user(inputs['username'], inputs['password'])
	return return_api({'user_id': user_id}, code=201)
		
@api.route('/user', methods=['PUT', 'DELETE'])
@error_handler
@auth
@input_validation
def api_manage_user(inputs: Dict[str, str]):
	"""
	Endpoint: /user
	Description: Manage a user account
	Requires being logged in: Yes
	Methods:
		PUT:
			Description: Change the password of the user account
			Parameters (body):
				new_password (required): the new password of the user account
			Returns:
				200:
					Password updated successfully
				400:
					KeyNotFound: One of the required parameters was not given
		DELETE:
			Description: Delete the user account
			Returns:
				200:
					Account deleted successfully
	"""
	if request.method == 'PUT':
		g.user_data.edit_password(inputs['new_password'])
		return return_api({})
	
	elif request.method == 'DELETE':
		g.user_data.delete()
		api_key_map.pop(g.hashed_api_key)
		return return_api({})

#===================
# Notification service endpoints
#===================

@api.route('/notificationservices', methods=['GET', 'POST'])
@error_handler
@auth
@input_validation
def api_notification_services_list(inputs: Dict[str, str]):
	"""
	Endpoint: /notificationservices
	Description: Manage the notification services
	Requires being logged in: Yes
	Methods:
		GET:
			Description: Get a list of all notification services
			Returns:
				200:
					The id, title and url of every notification service
		POST:
			Description: Add a notification service
			Parameters (body):
				title (required): the title of the notification service
				url (required): the apprise url of the notification service
			Returns:
				200:
					The id of the new notification service
				400:
					KeyNotFound: One of the required parameters was not given
	"""
	services: NotificationServices = g.user_data.notification_services

	if request.method == 'GET':
		result = services.fetchall()
		return return_api(result)
		
	elif request.method == 'POST':
		result = services.add(title=inputs['title'],
							url=inputs['url']).get()
		return return_api(result, code=201)

@api.route('/notificationservices/<int:n_id>', methods=['GET', 'PUT', 'DELETE'])
@error_handler
@auth
@input_validation
def api_notification_service(inputs: Dict[str, str], n_id: int):
	"""
	Endpoint: /notificationservices/<n_id>
	Description: Manage a specific notification service
	Requires being logged in: Yes
	URL Parameters:
		<n_id>:
			The id of the notification service
	Methods:
		GET:
			Returns:
				200:
					All info about the notification service
				404:
					No notification service found with the given id
		PUT:
			Description: Edit the notification service
			Parameters (body):
				title: The new title of the entry.
				url: The new apprise url of the entry.
			Returns:
				200:
					Notification service updated successfully
				400:
					The apprise url is invalid
				404:
					No notification service found with the given id
		DELETE:
			Description: Delete the notification service
			Returns:
				200:
					Notification service deleted successfully
				404:
					No notification service found with the given id
	"""
	service: NotificationService = g.user_data.notification_services.fetchone(n_id)
	
	if request.method == 'GET':
		result = service.get()
		return return_api(result)
		
	elif request.method == 'PUT':
		result = service.update(title=inputs['title'],
						url=inputs['url'])
		return return_api(result)
		
	elif request.method == 'DELETE':
		service.delete()
		return return_api({})

#===================
# Library endpoints
#===================

@api.route('/reminders', methods=['GET', 'POST'])
@error_handler
@auth
@input_validation
def api_reminders_list(inputs: Dict[str, Any]):
	"""
	Endpoint: /reminders
	Description: Manage the reminders
	Requires being logged in: Yes
	Methods:
		GET:
			Description: Get a list of all reminders
			Parameters (url):
				sort_by: How to sort the result. Allowed values are 'title', 'title_reversed', 'time', 'time_reversed', 'date_added' and 'date_added_reversed'
			Returns:
				200:
					The id, title, text, time, repeat_quantity, repeat_interval and color of each reminder
		POST:
			Description: Add a reminder
			Parameters (body):
				title (required): the title of the reminder
				time (required): the UTC epoch timestamp that the reminder should be sent at
				notification_services (required): array of the id's of the notification services to use to send the notification
				text: the body of the reminder
				repeat_quantity ('years', 'months', 'weeks', 'days', 'hours', 'minutes'): The quantity of the repeat_interval
				repeat_interval: The number of the interval
				color: The hex code of the color of the reminder, which is shown in the web-ui
			Returns:
				200:
					The info about the new reminder entry
				400:
					KeyNotFound: One of the required parameters was not given
				404:
					NotificationServiceNotFound: One of the notification services was not found
	"""
	reminders: Reminders = g.user_data.reminders
	
	if request.method == 'GET':
		result = reminders.fetchall(inputs['sort_by'])
		return return_api(result)

	elif request.method == 'POST':
		result = reminders.add(title=inputs['title'],
								time=inputs['time'],
								notification_services=inputs['notification_services'],
								text=inputs['text'],
								repeat_quantity=inputs['repeat_quantity'],
								repeat_interval=inputs['repeat_interval'],
								color=inputs['color'])
		return return_api(result.get(), code=201)

@api.route('/reminders/search', methods=['GET'])
@error_handler
@auth
@input_validation
def api_reminders_query(inputs: Dict[str, str]):
	"""
	Endpoint: /reminders/search
	Description: Search through the list of reminders
	Requires being logged in: Yes
	Methods:
		GET:
			Parameters (url):
				query (required): The search term
				sort_by: How to sort the result. Allowed values are 'title', 'title_reversed', 'time', 'time_reversed', 'date_added' and 'date_added_reversed'
			Returns:
				200:
					The search results, listed like GET /reminders
				400:
					KeyNotFound: One of the required parameters was not given
	"""
	result = g.user_data.reminders.search(inputs['query'], inputs['sort_by'])
	return return_api(result)

@api.route('/reminders/test', methods=['POST'])
@error_handler
@auth
@input_validation
def api_test_reminder(inputs: Dict[str, Any]):
	"""
	Endpoint: /reminders/test
	Description: Test send a reminder draft
	Requires being logged in: Yes
	Methods:
		GET:
			Parameters (body):
				title (required): The title of the entry.
				notification_service (required): The new id of the notification service to use to send the reminder.
				text: The body of the reminder.
			Returns:
				201:
					The reminder is sent (doesn't mean it works, just that it was sent)
				400:
					KeyNotFound: One of the required parameters was not given
				404:
					NotificationServiceNotFound: The notification service given was not found
	"""
	g.user_data.reminders.test_reminder(inputs['title'], inputs['notification_services'], inputs['text'])
	return return_api({}, code=201)

@api.route('/reminders/<int:r_id>', methods=['GET', 'PUT', 'DELETE'])
@error_handler
@auth
@input_validation
def api_get_reminder(inputs: Dict[str, Any], r_id: int):
	"""
	Endpoint: /reminders/<r_id>
	Description: Manage a specific reminder
	Requires being logged in: Yes
	URL Parameters:
		<r_id>:
			The id of the reminder
	Methods:
		GET:
			Returns:
				200:
					All info about the reminder
				404:
					No reminder found with the given id
		PUT:
			Description: Edit the reminder
			Parameters (body):
				title: The new title of the entry.
				time: The new UTC epoch timestamp the the reminder should be send.
				notification_services: Array of the new id's of the notification services to use to send the reminder.
				text: The new body of the reminder.
				repeat_quantity ('years', 'months', 'weeks', 'days', 'hours', 'minutes'): The new quantity of the repeat_interval.
				repeat_interval: The new number of the interval.
				color: The new hex code of the color of the reminder, which is shown in the web-ui.
			Returns:
				200:
					Reminder updated successfully
				404:
					ReminderNotFound: No reminder found with the given id
					NotificationServiceNotFound: One of the notification services was not found
		DELETE:
			Description: Delete the reminder
			Returns:
				200:
					Reminder deleted successfully
				404:
					No reminder found with the given id
	"""
	reminders: Reminders = g.user_data.reminders
	if request.method == 'GET':
		result = reminders.fetchone(r_id).get()
		return return_api(result)

	elif request.method == 'PUT':
		result = reminders.fetchone(r_id).update(title=inputs['title'],
												time=inputs['time'],
												notification_services=inputs['notification_services'],
												text=inputs['text'],
												repeat_quantity=inputs['repeat_quantity'],
												repeat_interval=inputs['repeat_interval'],
												color=inputs['color'])
		return return_api(result)

	elif request.method == 'DELETE':
		reminders.fetchone(r_id).delete()
		return return_api({})

#===================
# Template endpoints
#===================

@api.route('/templates', methods=['GET', 'POST'])
@error_handler
@auth
@input_validation
def api_get_templates(inputs: Dict[str, Any]):
	"""
	Endpoint: /templates
	Description: Manage the templates
	Requires being logged in: Yes
	Methods:
		GET:
			Description: Get a list of all templates
			Parameters (url):
				sort_by: How to sort the result. Allowed values are 'title', 'title_reversed', 'date_added' and 'date_added_reversed'
			Returns:
				200:
					The id, title, text and color of every template
		POST:
			Description: Add a template
			Parameters (body):
				title (required): the title of the template
				notification_services (required): array of the id's of the notification services to use to send the notification
				text: the body of the template
				color: the hex code of the color of the template, which is shown in the web-ui
			Returns:
				200:
					The info about the new template entry
				400:
					KeyNotFound: One of the required parameters was not given
				404:
					NotificationServiceNotFound: One of the notification services was not found
	"""
	templates: Templates = g.user_data.templates
	
	if request.method == 'GET':
		result = templates.fetchall(inputs['sort_by'])
		return return_api(result)
	
	elif request.method == 'POST':
		result = templates.add(title=inputs['title'],
								notification_services=inputs['notification_services'],
								text=inputs['text'],
								color=inputs['color'])
		return return_api(result.get(), code=201)

@api.route('/templates/search', methods=['GET'])
@error_handler
@auth
@input_validation
def api_templates_query(inputs: Dict[str, str]):
	"""
	Endpoint: /templates/search
	Description: Search through the list of templates
	Requires being logged in: Yes
	Methods:
		GET:
			Parameters (url):
				query (required): The search term
				sort_by: How to sort the result. Allowed values are 'title', 'title_reversed', 'date_added' and 'date_added_reversed'
			Returns:
				200:
					The search results, listed like GET /templates
				400:
					KeyNotFound: One of the required parameters was not given
	"""
	result = g.user_data.templates.search(inputs['query'], inputs['sort_by'])
	return return_api(result)

@api.route('/templates/<int:t_id>', methods=['GET', 'PUT', 'DELETE'])
@error_handler
@auth
@input_validation
def api_get_template(inputs: Dict[str, Any], t_id: int):
	"""
	Endpoint: /templates/<t_id>
	Description: Manage a specific template
	Requires being logged in: Yes
	URL Parameters:
		<t_id>:
			The id of the template
	Methods:
		GET:
			Returns:
				200:
					All info about the template
				404:
					No template found with the given id
		PUT:
			Description: Edit the template
			Parameters (body):
				title: The new title of the entry.
				notification_services: The new array of id's of the notification services to use to send the reminder.
				text: The new body of the template.
				color: The new hex code of the color of the template.
			Returns:
				200:
					Template updated successfully
				404:
					TemplateNotFound: No template found with the given id
					NotificationServiceNotFound: One of the notification services was not found
		DELETE:
			Description: Delete the template
			Returns:
				200:
					Template deleted successfully
				404:
					No template found with the given id
	"""
	template: Template = g.user_data.templates.fetchone(t_id)
	
	if request.method == 'GET':
		result = template.get()
		return return_api(result)
		
	elif request.method == 'PUT':
		result = template.update(title=inputs['title'],
								notification_services=inputs['notification_services'],
								text=inputs['text'],
								color=inputs['color'])
		return return_api(result)

	elif request.method == 'DELETE':
		template.delete()
		return return_api({})

#===================
# Static reminder endpoints
#===================

@api.route('/staticreminders', methods=['GET', 'POST'])
@error_handler
@auth
@input_validation
def api_static_reminders_list(inputs: Dict[str, Any]):
	"""
	Endpoint: /staticreminders
	Description: Manage the static reminders
	Requires being logged in: Yes
	Methods:
		GET:
			Description: Get a list of all static reminders
			Parameters (url):
				sort_by: How to sort the result. Allowed values are 'title', 'title_reversed', 'date_added' and 'date_added_reversed'
			Returns:
				200:
					The id, title, text and color of each static reminder
		POST:
			Description: Add a static reminder
			Parameters (body):
				title (required): the title of the static reminder
				notification_services (required): array of the id's of the notification services to use to send the notification
				text: the body of the static reminder
				color: The hex code of the color of the static reminder, which is shown in the web-ui
			Returns:
				200:
					The info about the new static reminder entry
				400:
					KeyNotFound: One of the required parameters was not given
				404:
					NotificationServiceNotFound: One of the notification services was not found
	"""	
	reminders: StaticReminders = g.user_data.static_reminders
	
	if request.method == 'GET':
		result = reminders.fetchall(inputs['sort_by'])
		return return_api(result)
	
	elif request.method == 'POST':
		result = reminders.add(title=inputs['title'],
			 					notification_services=inputs['notification_services'],
								text=inputs['text'],
								color=inputs['color'])
		return return_api(result.get(), code=201)

@api.route('/staticreminders/search', methods=['GET'])
@error_handler
@auth
@input_validation
def api_static_reminders_query(inputs: Dict[str, str]):
	"""
	Endpoint: /staticreminders/search
	Description: Search through the list of staticreminders
	Requires being logged in: Yes
	Methods:
		GET:
			Parameters (url):
				query (required): The search term
				sort_by: How to sort the result. Allowed values are 'title', 'title_reversed', 'date_added' and 'date_added_reversed'
			Returns:
				200:
					The search results, listed like GET /staticreminders
				400:
					KeyNotFound: One of the required parameters was not given
	"""
	result = g.user_data.static_reminders.search(inputs['query'], inputs['sort_by'])
	return return_api(result)

@api.route('/staticreminders/<int:r_id>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@error_handler
@auth
@input_validation
def api_get_static_reminder(inputs: Dict[str, Any], r_id: int):
	"""
	Endpoint: /staticreminders/<r_id>
	Description: Manage a specific static reminder
	Requires being logged in: Yes
	URL Parameters:
		<r_id>:
			The id of the static reminder
	Methods:
		GET:
			Returns:
				200:
					All info about the static reminder
				404:
					No static reminder found with the given id
		POST:
			Description: Trigger the static reminder
			Returns:
				200:
					Static reminder triggered successfully
		PUT:
			Description: Edit the static reminder
			Parameters (body):
				title: The new title of the static reminder.
				notification_services: The new array of id's of the notification services to use to send the reminder.
				text: The new body of the static reminder.
				color: The new hex code of the color of the static reminder, which is shown in the web-ui.
			Returns:
				200:
					Static reminder updated successfully
				404:
					ReminderNotFound: No static reminder found with the given id
					NotificationServiceNotFound: One of the notification services was not found
		DELETE:
			Description: Delete the static reminder
			Returns:
				200:
					Static reminder deleted successfully
				404:
					No static reminder found with the given id
	"""
	reminders: StaticReminders = g.user_data.static_reminders
	if request.method == 'GET':
		result = reminders.fetchone(r_id).get()
		return return_api(result)

	elif request.method == 'POST':
		reminders.trigger_reminder(r_id)
		return return_api({})

	elif request.method == 'PUT':
		result = reminders.fetchone(r_id).update(title=inputs['title'],
												notification_services=inputs['notification_services'],
												text=inputs['text'],
												color=inputs['color'])
		return return_api(result)

	elif request.method == 'DELETE':
		reminders.fetchone(r_id).delete()
		return return_api({})
