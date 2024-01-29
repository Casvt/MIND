#-*- coding: utf-8 -*-

from io import BytesIO
import logging
from abc import ABC, abstractmethod
from os import urandom
from re import compile
from time import time as epoch_time
from typing import Any, Callable, Dict, List, Tuple, Union

from apprise import Apprise
from flask import Blueprint, g, request, send_file
from flask.sansio.scaffold import T_route

from backend.custom_exceptions import (AccessUnauthorized, APIKeyExpired,
                                       APIKeyInvalid, InvalidKeyValue,
                                       InvalidTime, KeyNotFound,
                                       NewAccountsNotAllowed,
                                       NotificationServiceInUse,
                                       NotificationServiceNotFound,
                                       ReminderNotFound, TemplateNotFound,
                                       UsernameInvalid, UsernameTaken,
                                       UserNotFound)
from backend.db import DBConnection
from backend.notification_service import (NotificationService,
                                          NotificationServices,
                                          get_apprise_services)
from backend.reminders import Reminders, reminder_handler
from backend.settings import (_format_setting, get_admin_settings, get_setting,
                              set_setting)
from backend.static_reminders import StaticReminders
from backend.templates import Template, Templates
from backend.users import (User, delete_user, edit_user_password, get_users,
                           register_user)

#===================
# Input validation
#===================
color_regex = compile(r'#[0-9a-f]{6}')

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
	
	@property
	@abstractmethod
	def related_exceptions() -> List[Exception]:
		pass

class DefaultInputVariable(InputVariable):
	source = DataSource.DATA
	required = True
	default = None
	related_exceptions = []
	
	def __init__(self, value: Any) -> None:
		self.value = value

	def validate(self) -> bool:
		return isinstance(self.value, str) and self.value
	
	def __repr__(self) -> str:
		return f'| {self.name} | {"Yes" if self.required else "No"} | {self.description} | N/A |'

class NonRequiredVersion(InputVariable):
	required = False
	
	def validate(self) -> bool:
		return self.value is None or super().validate()

class UsernameVariable(DefaultInputVariable):
	name = 'username'
	description = 'The username of the user account'
	related_exceptions = [KeyNotFound, UserNotFound]

class PasswordVariable(DefaultInputVariable):
	name = 'password'
	description = 'The password of the user account'
	related_exceptions = [KeyNotFound, AccessUnauthorized]

class NewPasswordVariable(PasswordVariable):
	name = 'new_password'
	description = 'The new password of the user account'
	related_exceptions = [KeyNotFound]

class UsernameCreateVariable(UsernameVariable):
	related_exceptions = [
		KeyNotFound,
		UsernameInvalid, UsernameTaken,
		NewAccountsNotAllowed
	]

class PasswordCreateVariable(PasswordVariable):
	related_exceptions = [KeyNotFound]

class TitleVariable(DefaultInputVariable):
	name = 'title'
	description = 'The title of the entry'
	related_exceptions = [KeyNotFound]

class URLVariable(DefaultInputVariable):
	name = 'url'
	description = 'The Apprise URL of the notification service'
	related_exceptions = [KeyNotFound, InvalidKeyValue]
	
	def validate(self) -> bool:
		return Apprise().add(self.value)

class EditTitleVariable(NonRequiredVersion, TitleVariable):
	related_exceptions = []
	
class EditURLVariable(NonRequiredVersion, URLVariable):
	related_exceptions = [InvalidKeyValue]

class SortByVariable(DefaultInputVariable):
	name = 'sort_by'
	description = 'How to sort the result'
	required = False
	source = DataSource.VALUES
	_options = Reminders.sort_functions
	default = next(iter(Reminders.sort_functions))
	related_exceptions = [InvalidKeyValue]

	def __init__(self, value: str) -> None:
		self.value = value

	def validate(self) -> bool:
		return self.value in self._options
	
	def __repr__(self) -> str:
		return '| {n} | {r} | {d} | {v} |'.format(
			n=self.name,
			r="Yes" if self.required else "No",
			d=self.description,
			v=", ".join(f'`{o}`' for o in self._options)
		)

class TemplateSortByVariable(SortByVariable):
	_options = Templates.sort_functions
	default = next(iter(Templates.sort_functions))

class StaticReminderSortByVariable(TemplateSortByVariable):
	_options = StaticReminders.sort_functions
	default = next(iter(StaticReminders.sort_functions))

class TimeVariable(DefaultInputVariable):
	name = 'time'
	description = 'The UTC epoch timestamp that the reminder should be sent at'
	related_exceptions = [KeyNotFound, InvalidKeyValue, InvalidTime]
	
	def validate(self) -> bool:
		return isinstance(self.value, (float, int))

class EditTimeVariable(NonRequiredVersion, TimeVariable):
	related_exceptions = [InvalidKeyValue, InvalidTime]

class NotificationServicesVariable(DefaultInputVariable):
	name = 'notification_services'
	description = "Array of the id's of the notification services to use to send the notification"
	related_exceptions = [KeyNotFound, InvalidKeyValue, NotificationServiceNotFound]
	
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
	related_exceptions = [InvalidKeyValue, NotificationServiceNotFound]

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
	related_exceptions = [InvalidKeyValue]
	
	def validate(self) -> bool:
		return self.value is None or self.value in self._options
	
	def __repr__(self) -> str:
		return '| {n} | {r} | {d} | {v} |'.format(
			n=self.name,
			r="Yes" if self.required else "No",
			d=self.description,
			v=", ".join(f'`{o}`' for o in self._options)
		)

class RepeatIntervalVariable(DefaultInputVariable):
	name = 'repeat_interval'
	description = 'The number of the interval'
	required = False
	default = None
	related_exceptions = [InvalidKeyValue]
	
	def validate(self) -> bool:
		return self.value is None or (isinstance(self.value, int) and self.value > 0)

class WeekDaysVariable(DefaultInputVariable):
	name = 'weekdays'
	description = 'On which days of the weeks to run the reminder'
	required = False
	default = None
	related_exceptions = [InvalidKeyValue]
	_options = {0, 1, 2, 3, 4, 5, 6}
	
	def validate(self) -> bool:
		return self.value is None or (
			isinstance(self.value, list)
			and len(self.value) > 0
			and all(v in self._options for v in self.value)
		)

class ColorVariable(DefaultInputVariable):
	name = 'color'
	description = 'The hex code of the color of the entry, which is shown in the web-ui'
	required = False
	default = None
	related_exceptions = [InvalidKeyValue]
	
	def validate(self) -> bool:
		return self.value is None or color_regex.search(self.value)

class QueryVariable(DefaultInputVariable):
	name = 'query'
	description = 'The search term'
	source = DataSource.VALUES

class AdminSettingsVariable(DefaultInputVariable):
	related_exceptions = [KeyNotFound, InvalidKeyValue]
	
	def validate(self) -> bool:
		try:
			_format_setting(self.name, self.value)
		except InvalidKeyValue:
			return False
		return True

class AllowNewAccountsVariable(AdminSettingsVariable):
	name = 'allow_new_accounts'
	description = ('Whether or not to allow users to register a new account. '
	+ 'The admin can always add a new account.')

class LoginTimeVariable(AdminSettingsVariable):
	name = 'login_time'
	description = ('How long a user stays logged in, in seconds. '
	+ 'Between 1 min and 1 month (60 <= sec <= 2592000)')

class LoginTimeResetVariable(AdminSettingsVariable):
	name = 'login_time_reset'
	description = 'If the Login Time timer should reset with each API request.'

def input_validation() -> Union[None, Dict[str, Any]]:
	"""Checks, extracts and transforms inputs

	Raises:
		KeyNotFound: A required key was not supplied
		InvalidKeyValue: The value of a key is not valid

	Returns:
		Union[None, Dict[str, Any]]: `None` if the endpoint + method doesn't require input variables.
		Otherwise `Dict[str, Any]` with the input variables, checked and formatted.
	"""
	inputs = {}

	input_variables: Dict[str, List[Union[List[InputVariable], str]]]
	if request.path.startswith(admin_api_prefix):
		input_variables = api_docs[
			_admin_api_prefix + request.url_rule.rule.split(admin_api_prefix)[1]
		]['input_variables']
	else:
		input_variables = api_docs[
			request.url_rule.rule.split(api_prefix)[1]
		]['input_variables']

	if not input_variables:
		return

	if input_variables.get(request.method) is None:
		return inputs
	
	given_variables = {}
	given_variables[DataSource.DATA] = request.get_json() if request.data else {}
	given_variables[DataSource.VALUES] = request.values
	for input_variable in input_variables[request.method]:
		if (
			input_variable.required and
			not input_variable.name in given_variables[input_variable.source]
		):
			raise KeyNotFound(input_variable.name)

		input_value = given_variables[input_variable.source].get(
			input_variable.name,
			input_variable.default
		)

		if not input_variable(input_value).validate():
			raise InvalidKeyValue(input_variable.name, input_value)
		
		inputs[input_variable.name] = input_value
	return inputs

#===================
# General variables and functions
#===================

api_docs: Dict[str, Dict[str, Any]] = {}
class APIBlueprint(Blueprint):
	def route(
		self,
		rule: str,
		description: str = '',
		input_variables: Dict[str, List[Union[List[InputVariable], str]]] = {},
		requires_auth: bool = True,
		**options: Any
	) -> Callable[[T_route], T_route]:

		if self == api:
			processed_rule = rule
		elif self == admin_api:
			processed_rule = _admin_api_prefix + rule
		else:
			raise NotImplementedError

		api_docs[processed_rule] = {
			'endpoint': processed_rule,
			'description': description,
			'requires_auth': requires_auth,
			'methods': options['methods'],
			'input_variables': {
				k: v[0]
				for k, v in input_variables.items()
				if v and v[0]
			},
			'method_descriptions': {
				k: v[1]
				for k, v in input_variables.items()
				if v and len(v) == 2 and v[1]
			}
		}

		return super().route(rule, **options)

api_prefix = "/api"
_admin_api_prefix = '/admin'
admin_api_prefix = api_prefix + _admin_api_prefix
api = APIBlueprint('api', __name__)
admin_api = APIBlueprint('admin_api', __name__)
api_key_map = {}

def return_api(result: Any, error: str=None, code: int=200) -> Tuple[dict, int]:
	return {'error': error, 'result': result}, code

def auth() -> None:
	"""Checks if the client is logged in

	Raises:
		APIKeyInvalid: The api key supplied is invalid
		APIKeyExpired: The api key supplied has expired
	"""
	hashed_api_key = hash(request.values.get('api_key',''))
	if not hashed_api_key in api_key_map:
		raise APIKeyInvalid

	if not (
		(
			api_key_map[hashed_api_key]['user_data'].admin
			and request.path.startswith((admin_api_prefix, api_prefix + '/auth'))
		)
		or 
		(
			not api_key_map[hashed_api_key]['user_data'].admin
			and not request.path.startswith(admin_api_prefix)
		)
	):
		raise APIKeyInvalid

	exp = api_key_map[hashed_api_key]['exp']
	if exp <= epoch_time():
		raise APIKeyExpired

	# Api key valid
	
	if get_setting('login_time_reset'):
		api_key_map[hashed_api_key]['exp'] = exp = (
			epoch_time() + get_setting('login_time')
		)

	g.hashed_api_key = hashed_api_key
	g.exp = exp
	g.user_data = api_key_map[hashed_api_key]['user_data']
	return

def endpoint_wrapper(method: Callable) -> Callable:
	def wrapper(*args, **kwargs):
		if request.path.startswith(admin_api_prefix):
			requires_auth = api_docs[
				_admin_api_prefix + request.url_rule.rule.split(admin_api_prefix)[1]
			]['requires_auth']
		else:
			requires_auth = api_docs[
				request.url_rule.rule.split(api_prefix)[1]
			]['requires_auth']
		try:
			if requires_auth:
				auth()

			inputs = input_validation()

			if inputs is None:
				return method(*args, **kwargs)
			return method(inputs, *args, **kwargs)

		except (UsernameTaken, UsernameInvalid, UserNotFound,
				AccessUnauthorized,
				ReminderNotFound, NotificationServiceNotFound,
				NotificationServiceInUse, InvalidTime,
				KeyNotFound, InvalidKeyValue,
				APIKeyInvalid, APIKeyExpired,
				TemplateNotFound,
				NewAccountsNotAllowed) as e:
			return return_api(**e.api_response)
	
	wrapper.__name__ = method.__name__
	return wrapper

#===================
# Authentication endpoints
#===================

@api.route(
	'/auth/login',
	'Login to a user account',
	{'POST': [[UsernameVariable, PasswordVariable]]},
	False,
	methods=['POST']
)
@endpoint_wrapper
def api_login(inputs: Dict[str, str]):
	user = User(inputs['username'], inputs['password'])

	# Generate an API key until one
	# is generated that isn't used already
	while True:
		api_key = urandom(16).hex() # <- length api key / 2
		hashed_api_key = hash(api_key)
		if not hashed_api_key in api_key_map:
			break

	login_time = get_setting('login_time')
	exp = epoch_time() + login_time
	api_key_map.update({
		hashed_api_key: {
			'exp': exp,
			'user_data': user
		}
	})

	result = {'api_key': api_key, 'expires': exp, 'admin': user.admin}
	return return_api(result, code=201)

@api.route(
	'/auth/logout',
	'Logout of a user account',
	methods=['POST']
)
@endpoint_wrapper
def api_logout():
	api_key_map.pop(g.hashed_api_key)
	return return_api({}, code=201)

@api.route(
	'/auth/status',
	'Get current status of login',
	methods=['GET']
)
@endpoint_wrapper
def api_status():
	result = {
		'expires': api_key_map[g.hashed_api_key]['exp'],
		'username': api_key_map[g.hashed_api_key]['user_data'].username,
		'admin': api_key_map[g.hashed_api_key]['user_data'].admin
	}
	return return_api(result)

#===================
# User endpoints
#===================

@api.route(
	'/user/add',
	'Create a new user account',
	{'POST': [[UsernameCreateVariable, PasswordCreateVariable]]},
	False,
	methods=['POST']
)
@endpoint_wrapper
def api_add_user(inputs: Dict[str, str]):
	register_user(inputs['username'], inputs['password'])
	return return_api({}, code=201)

@api.route(
	'/user',
	'Manage a user account',
	{'PUT': [[NewPasswordVariable],
	  		'Change the password of the user account'],
	'DELETE': [[],
	    	'Delete the user account']},
	methods=['PUT', 'DELETE']
)
@endpoint_wrapper
def api_manage_user(inputs: Dict[str, str]):
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

@api.route(
	'/notificationservices',
	'Manage the notification services',
	{'GET': [[],
			'Get a list of all notification services'],
  	'POST': [[TitleVariable, URLVariable],
			'Add a notification service']},
	methods=['GET', 'POST']
)
@endpoint_wrapper
def api_notification_services_list(inputs: Dict[str, str]):
	services: NotificationServices = g.user_data.notification_services

	if request.method == 'GET':
		result = services.fetchall()
		return return_api(result)
		
	elif request.method == 'POST':
		result = services.add(title=inputs['title'],
							url=inputs['url']).get()
		return return_api(result, code=201)

@api.route(
	'/notificationservices/available',
	'Get all available notification services and their url layout',
	methods=['GET']
)
@endpoint_wrapper
def api_notification_service_available():
	result = get_apprise_services()
	return return_api(result)

@api.route(
	'/notificationservices/test',
	'Send a test notification using the supplied Apprise URL',
	{'POST': [[URLVariable]]}, 
	methods=['POST']
)
@endpoint_wrapper
def api_test_service(inputs: Dict[str, Any]):
	g.user_data.notification_services.test_service(inputs['url'])
	return return_api({}, code=201)

@api.route(
	'/notificationservices/<int:n_id>',
	'Manage a specific notification service',
	{'PUT': [[EditTitleVariable, EditURLVariable],
	  		'Edit the notification service'],
	'DELETE': [[],
	    	'Delete the notification service']},
	methods=['GET', 'PUT', 'DELETE']
)
@endpoint_wrapper
def api_notification_service(inputs: Dict[str, str], n_id: int):
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

@api.route(
	'/reminders',
	'Manage the reminders',
	{'GET': [[SortByVariable],
			'Get a list of all reminders'],
	'POST': [[TitleVariable, TimeVariable,
			NotificationServicesVariable, TextVariable,
			RepeatQuantityVariable, RepeatIntervalVariable,
			WeekDaysVariable,
			ColorVariable],
			'Add a reminder']
	},
	methods=['GET', 'POST']
)
@endpoint_wrapper
def api_reminders_list(inputs: Dict[str, Any]):
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
								weekdays=inputs['weekdays'],
								color=inputs['color'])
		return return_api(result.get(), code=201)

@api.route(
	'/reminders/search',
	'Search through the list of reminders',
	{'GET': [[SortByVariable, QueryVariable]]},
	methods=['GET']
)
@endpoint_wrapper
def api_reminders_query(inputs: Dict[str, str]):
	result = g.user_data.reminders.search(inputs['query'], inputs['sort_by'])
	return return_api(result)

@api.route(
	'/reminders/test',
	'Test send a reminder draft',
	{'POST': [[TitleVariable, NotificationServicesVariable,
			TextVariable]]}, 
	methods=['POST']
)
@endpoint_wrapper
def api_test_reminder(inputs: Dict[str, Any]):
	g.user_data.reminders.test_reminder(inputs['title'], inputs['notification_services'], inputs['text'])
	return return_api({}, code=201)

@api.route(
	'/reminders/<int:r_id>',
	'Manage a specific reminder',
	{'PUT': [[EditTitleVariable, EditTimeVariable,
			EditNotificationServicesVariable, TextVariable,
			RepeatQuantityVariable, RepeatIntervalVariable,
			WeekDaysVariable,
			ColorVariable],
			'Edit the reminder'],
	'DELETE': [[],
	    	'Delete the reminder']},
	methods=['GET', 'PUT', 'DELETE']
)
@endpoint_wrapper
def api_get_reminder(inputs: Dict[str, Any], r_id: int):
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
												weekdays=inputs['weekdays'],
												color=inputs['color'])
		return return_api(result)

	elif request.method == 'DELETE':
		reminders.fetchone(r_id).delete()
		return return_api({})

#===================
# Template endpoints
#===================

@api.route(
	'/templates',
	'Manage the templates',
	{'GET': [[TemplateSortByVariable],
	  		'Get a list of all templates'],
	'POST': [[TitleVariable, NotificationServicesVariable,
			TextVariable, ColorVariable],
			'Add a template']},
	methods=['GET', 'POST']
)
@endpoint_wrapper
def api_get_templates(inputs: Dict[str, Any]):
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

@api.route(
	'/templates/search',
	'Search through the list of templates',
	{'GET': [[TemplateSortByVariable, QueryVariable]]},
	methods=['GET']
)
@endpoint_wrapper
def api_templates_query(inputs: Dict[str, str]):
	result = g.user_data.templates.search(inputs['query'], inputs['sort_by'])
	return return_api(result)

@api.route(
	'/templates/<int:t_id>',
	'Manage a specific template',
	{'PUT': [[EditTitleVariable, EditNotificationServicesVariable,
			TextVariable, ColorVariable],
			'Edit the template'],
	'DELETE': [[],
	    	'Delete the template']},
	methods=['GET', 'PUT', 'DELETE']
)
@endpoint_wrapper
def api_get_template(inputs: Dict[str, Any], t_id: int):
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

@api.route(
	'/staticreminders',
	'Manage the static reminders',
	{'GET': [[StaticReminderSortByVariable],
	  		'Get a list of all static reminders'],
	'POST': [[TitleVariable, NotificationServicesVariable,
			TextVariable, ColorVariable],
			'Add a static reminder']},
	methods=['GET', 'POST']
)
@endpoint_wrapper
def api_static_reminders_list(inputs: Dict[str, Any]):
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

@api.route(
	'/staticreminders/search',
	'Search through the list of staticreminders',
	{'GET': [[StaticReminderSortByVariable, QueryVariable]]},
	methods=['GET']
)
@endpoint_wrapper
def api_static_reminders_query(inputs: Dict[str, str]):
	result = g.user_data.static_reminders.search(inputs['query'], inputs['sort_by'])
	return return_api(result)

@api.route(
	'/staticreminders/<int:s_id>',
	'Manage a specific static reminder',
	{'POST': [[],
	   		'Trigger the static reminder'],
	'PUT': [[EditTitleVariable, EditNotificationServicesVariable,
			TextVariable, ColorVariable],
			'Edit the static reminder'],
	'DELETE': [[],
	    	'Delete the static reminder']},
	methods=['GET', 'POST', 'PUT', 'DELETE']
)
@endpoint_wrapper
def api_get_static_reminder(inputs: Dict[str, Any], s_id: int):
	reminders: StaticReminders = g.user_data.static_reminders
	if request.method == 'GET':
		result = reminders.fetchone(s_id).get()
		return return_api(result)

	elif request.method == 'POST':
		reminders.trigger_reminder(s_id)
		return return_api({}, code=201)

	elif request.method == 'PUT':
		result = reminders.fetchone(s_id).update(title=inputs['title'],
												notification_services=inputs['notification_services'],
												text=inputs['text'],
												color=inputs['color'])
		return return_api(result)

	elif request.method == 'DELETE':
		reminders.fetchone(s_id).delete()
		return return_api({})

#===================
# Admin panel endpoints
#===================

@api.route(
	'/settings',
	'Get the admin settings',
	requires_auth=False,
	methods=['GET']
)
@endpoint_wrapper
def api_settings():
	return return_api(get_admin_settings())

@admin_api.route(
	'/settings',
	'Interact with the admin settings',
	{'GET': [[],
			'Get the admin settings'],
	'PUT': [[AllowNewAccountsVariable, LoginTimeVariable,
			LoginTimeResetVariable],
			'Edit the admin settings']},
	methods=['GET', 'PUT']
)
@endpoint_wrapper
def api_admin_settings(inputs: Dict[str, Any]):
	if request.method == 'GET':
		return return_api(get_admin_settings())

	elif request.method == 'PUT':
		values = {
			'allow_new_accounts': inputs['allow_new_accounts'],
			'login_time': inputs['login_time'],
			'login_time_reset': inputs['login_time_reset']
		}
		logging.info(f'Submitting admin settings: {values}')
		for k, v in values.items():
			set_setting(k, v)
		return return_api({})

@admin_api.route(
	'/users',
	'Get all users or add one',
	{'GET': [[],
			'Get all users'],
	'POST': [[UsernameCreateVariable, PasswordCreateVariable],
			'Add a new user']},
	methods=['GET', 'POST']
)
@endpoint_wrapper
def api_admin_users(inputs: Dict[str, Any]):
	if request.method == 'GET':
		result = get_users()
		return return_api(result)

	elif request.method == 'POST':
		register_user(inputs['username'], inputs['password'], True)
		return return_api({}, code=201)

@admin_api.route(
	'/users/<int:u_id>',
	'Manage a specific user',
	{'PUT': [[NewPasswordVariable],
			'Change the password of the user account'],
	'DELETE': [[],
			'Delete the user account']},
	methods=['PUT', 'DELETE']
)
@endpoint_wrapper
def api_admin_user(inputs: Dict[str, Any], u_id: int):
	if request.method == 'PUT':
		edit_user_password(u_id, inputs['new_password'])
		return return_api({})
	
	elif request.method == 'DELETE':
		delete_user(u_id)
		for key, value in api_key_map.items():
			if value['user_data'].user_id == u_id:
				del api_key_map[key]
				break
		return return_api({})

@admin_api.route(
	'/database',
	'Download the database',
	{'GET': [[]]},
	methods=['GET']
)
@endpoint_wrapper
def api_admin_database():
	with open(DBConnection.file, 'rb') as database_file:
		return send_file(
			BytesIO(database_file.read()),
			'application/x-sqlite3',
			download_name='MIND.db'
		), 200
	