#-*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from os import remove, urandom
from os.path import basename, exists
from time import time as epoch_time
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple

from flask import g, request, send_file

from backend.custom_exceptions import (AccessUnauthorized, APIKeyExpired,
                                       APIKeyInvalid, InvalidDatabaseFile,
                                       InvalidKeyValue, InvalidTime,
                                       KeyNotFound, LogFileNotFound,
                                       NewAccountsNotAllowed,
                                       NotificationServiceInUse,
                                       NotificationServiceNotFound,
                                       ReminderNotFound, TemplateNotFound,
                                       UsernameInvalid, UsernameTaken,
                                       UserNotFound)
from backend.db import get_db, import_db, revert_db_import
from backend.helpers import RestartVars, folder_path
from backend.logging import LOGGER, get_debug_log_filepath
from backend.notification_service import get_apprise_services
from backend.server import SERVER
from backend.settings import (backup_hosting_settings, get_admin_settings,
                              get_setting, set_setting)
from backend.users import Users
from frontend.input_validation import (AllowNewAccountsVariable, ColorVariable,
                                       CopyHostingSettingsVariable,
                                       DatabaseFileVariable,
                                       DeleteRemindersUsingVariable,
                                       EditNotificationServicesVariable,
                                       EditTimeVariable, EditTitleVariable,
                                       EditURLVariable, HostVariable,
                                       LoginTimeResetVariable,
                                       LoginTimeVariable, LogLevelVariable,
                                       Method, Methods, NewPasswordVariable,
                                       NotificationServicesVariable,
                                       PasswordCreateVariable,
                                       PasswordVariable, PortVariable,
                                       QueryVariable, RepeatIntervalVariable,
                                       RepeatQuantityVariable, SortByVariable,
                                       TextVariable, TimelessSortByVariable,
                                       TimeVariable, TitleVariable,
                                       UrlPrefixVariable, URLVariable,
                                       UsernameCreateVariable,
                                       UsernameVariable, WeekDaysVariable,
                                       admin_api, api, get_api_docs,
                                       input_validation)

if TYPE_CHECKING:
	from backend.users import User


#===================
# General variables and functions
#===================

@dataclass
class ApiKeyEntry:
	exp: int
	user_data: User

users = Users()
api_key_map: Dict[int, ApiKeyEntry] = {}

def return_api(
	result: Any,
	error: Optional[str] = None,
	code: int = 200
) -> Tuple[dict, int]:
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

	map_entry = api_key_map[hashed_api_key]

	if (
		map_entry.user_data.admin
		and
		not request.path.startswith((SERVER.admin_prefix, SERVER.api_prefix + '/auth'))
	):
		raise APIKeyInvalid
	
	if (
		not map_entry.user_data.admin
		and
		request.path.startswith(SERVER.admin_prefix)
	):
		raise APIKeyInvalid

	if map_entry.exp <= epoch_time():
		raise APIKeyExpired

	# Api key valid
	
	if get_setting('login_time_reset'):
		g.exp = map_entry.exp = (
			epoch_time() + get_setting('login_time')
		)
	else:
		g.exp = map_entry.exp

	g.hashed_api_key = hashed_api_key
	g.user_data = map_entry.user_data

	return

def endpoint_wrapper(method: Callable) -> Callable:
	def wrapper(*args, **kwargs):
		requires_auth = get_api_docs(request).requires_auth

		try:
			if requires_auth:
				auth()

			inputs = input_validation()

			if inputs is None:
				return method(*args, **kwargs)
			return method(inputs, *args, **kwargs)

		except (
			AccessUnauthorized, APIKeyExpired,
			APIKeyInvalid, InvalidDatabaseFile,
			InvalidKeyValue, InvalidTime,
			KeyNotFound, LogFileNotFound,
			NewAccountsNotAllowed,
			NotificationServiceInUse,
			NotificationServiceNotFound,
			ReminderNotFound, TemplateNotFound,
			UsernameInvalid, UsernameTaken,
			UserNotFound
		) as e:
			return return_api(**e.api_response)
	
	wrapper.__name__ = method.__name__
	return wrapper

#===================
# Authentication endpoints
#===================

@api.route(
	'/auth/login',
	'Login to a user account',
	Methods(
		post=Method(
			vars=[UsernameVariable, PasswordVariable]
		)
	),
	requires_auth=False,
	methods=['POST']
)
@endpoint_wrapper
def api_login(inputs: Dict[str, str]):
	user = users.login(inputs['username'], inputs['password'])

	# Login successful

	if user.admin and SERVER.revert_db_timer.is_alive():
		LOGGER.info('Timer for database import diffused')
		SERVER.revert_db_timer.cancel()
		revert_db_import(swap=False)

	elif user.admin and SERVER.revert_hosting_timer.is_alive():
		LOGGER.info('Timer for hosting changes diffused')
		SERVER.revert_hosting_timer.cancel()

	# Generate an API key until one
	# is generated that isn't used already
	while True:
		api_key = urandom(16).hex() # <- length api key / 2
		hashed_api_key = hash(api_key)
		if not hashed_api_key in api_key_map:
			break

	login_time = get_setting('login_time')
	exp = epoch_time() + login_time
	api_key_map[hashed_api_key] = ApiKeyEntry(exp, user)

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
	map_entry = api_key_map[g.hashed_api_key]
	result = {
		'expires': map_entry.exp,
		'username': map_entry.user_data.username,
		'admin': map_entry.user_data.admin
	}
	return return_api(result)

#===================
# User endpoints
#===================
@api.route(
	'/user/add',
	'Create a new user account',
	Methods(
		post=Method(
			vars=[UsernameCreateVariable, PasswordCreateVariable]
		)
	),
	requires_auth=False,
	methods=['POST']
)
@endpoint_wrapper
def api_add_user(inputs: Dict[str, str]):
	users.add(inputs['username'], inputs['password'])
	return return_api({}, code=201)

@api.route(
	'/user',
	'Manage a user account',
	Methods(
		put=Method(
			vars=[NewPasswordVariable],
			description="Change the password of the user account"
		),
		delete=Method(
			description='Delete the user account'
		)
	),
	methods=['PUT', 'DELETE']
)
@endpoint_wrapper
def api_manage_user(inputs: Dict[str, str]):
	user = api_key_map[g.hashed_api_key].user_data
	if request.method == 'PUT':
		user.edit_password(inputs['new_password'])
		return return_api({})
	
	elif request.method == 'DELETE':
		user.delete()
		api_key_map.pop(g.hashed_api_key)
		return return_api({})

#===================
# Notification service endpoints
#===================

@api.route(
	'/notificationservices',
	'Manage the notification services',
	Methods(
		get=Method(
			description='Get a list of all notification services'
		),
		post=Method(
			vars=[TitleVariable, URLVariable],
			description='Add a notification service'
		)
	),
	methods=['GET', 'POST']
)
@endpoint_wrapper
def api_notification_services_list(inputs: Dict[str, str]):
	services = api_key_map[g.hashed_api_key].user_data.notification_services

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
	Methods(
		post=Method(
			vars=[URLVariable]
		)
	),
	methods=['POST']
)
@endpoint_wrapper
def api_test_service(inputs: Dict[str, Any]):
	(api_key_map[g.hashed_api_key]
		.user_data
		.notification_services
		.test_service(inputs['url']))
	return return_api({}, code=201)

@api.route(
	'/notificationservices/<int:n_id>',
	'Manage a specific notification service',
	Methods(
		put=Method(
			vars=[EditTitleVariable, EditURLVariable],
			description='Edit the notification service'
		),
		delete=Method(
			vars=[DeleteRemindersUsingVariable],
			description='Delete the notification service'
		)
	),
	methods=['GET', 'PUT', 'DELETE']
)
@endpoint_wrapper
def api_notification_service(inputs: Dict[str, str], n_id: int):
	service = (api_key_map[g.hashed_api_key]
		.user_data
		.notification_services
		.fetchone(n_id))

	if request.method == 'GET':
		result = service.get()
		return return_api(result)

	elif request.method == 'PUT':
		result = service.update(title=inputs['title'],
						url=inputs['url'])
		return return_api(result)

	elif request.method == 'DELETE':
		service.delete(
			inputs['delete_reminders_using']
		)
		return return_api({})

#===================
# Library endpoints
#===================

@api.route(
	'/reminders',
	'Manage the reminders',
	Methods(
		get=Method(
			vars=[SortByVariable],
			description='Get a list of all reminders'
		),
		post=Method(
			vars=[TitleVariable, TimeVariable,
				NotificationServicesVariable, TextVariable,
				RepeatQuantityVariable, RepeatIntervalVariable,
				WeekDaysVariable,
				ColorVariable],
			description='Add a reminder'
		),
	),
	methods=['GET', 'POST']
)
@endpoint_wrapper
def api_reminders_list(inputs: Dict[str, Any]):
	reminders = api_key_map[g.hashed_api_key].user_data.reminders
	
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
	Methods(
		get=Method(
			vars=[SortByVariable, QueryVariable]
		)
	),
	methods=['GET']
)
@endpoint_wrapper
def api_reminders_query(inputs: Dict[str, str]):
	result = (api_key_map[g.hashed_api_key]
		.user_data
		.reminders
		.search(inputs['query'], inputs['sort_by']))
	return return_api(result)

@api.route(
	'/reminders/test',
	'Test send a reminder draft',
	Methods(
		post=Method(
			vars=[TitleVariable, NotificationServicesVariable,
			TextVariable]
		)
	),
	methods=['POST']
)
@endpoint_wrapper
def api_test_reminder(inputs: Dict[str, Any]):
	api_key_map[g.hashed_api_key].user_data.reminders.test_reminder(
		inputs['title'],
		inputs['notification_services'],
		inputs['text']
	)
	return return_api({}, code=201)

@api.route(
	'/reminders/<int:r_id>',
	'Manage a specific reminder',
	Methods(
		put=Method(
			vars=[EditTitleVariable, EditTimeVariable,
				EditNotificationServicesVariable, TextVariable,
				RepeatQuantityVariable, RepeatIntervalVariable,
				WeekDaysVariable,
				ColorVariable],
			description='Edit the reminder'
		),
		delete=Method(
			description='Delete the reminder'
		)
	),
	methods=['GET', 'PUT', 'DELETE']
)
@endpoint_wrapper
def api_get_reminder(inputs: Dict[str, Any], r_id: int):
	reminders = api_key_map[g.hashed_api_key].user_data.reminders

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
	Methods(
		get=Method(
			vars=[TimelessSortByVariable],
			description='Get a list of all templates'
		),
		post=Method(
			vars=[TitleVariable, NotificationServicesVariable,
				TextVariable, ColorVariable],
			description='Add a template'
		)
	),
	methods=['GET', 'POST']
)
@endpoint_wrapper
def api_get_templates(inputs: Dict[str, Any]):
	templates = api_key_map[g.hashed_api_key].user_data.templates
	
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
	Methods(
		get=Method(
			vars=[TimelessSortByVariable, QueryVariable]
		)
	),
	methods=['GET']
)
@endpoint_wrapper
def api_templates_query(inputs: Dict[str, str]):
	result = (api_key_map[g.hashed_api_key]
		.user_data
		.templates
		.search(inputs['query'], inputs['sort_by']))
	return return_api(result)

@api.route(
	'/templates/<int:t_id>',
	'Manage a specific template',
	Methods(
		put=Method(
			vars=[EditTitleVariable, EditNotificationServicesVariable,
				TextVariable, ColorVariable],
			description='Edit the template'
		),
		delete=Method(
			description='Delete the template'
		)
	),
	methods=['GET', 'PUT', 'DELETE']
)
@endpoint_wrapper
def api_get_template(inputs: Dict[str, Any], t_id: int):
	template = (api_key_map[g.hashed_api_key]
		.user_data
		.templates
		.fetchone(t_id))
	
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
	Methods(
		get=Method(
			vars=[TimelessSortByVariable],
			description='Get a list of all static reminders'
		),
		post=Method(
			vars=[TitleVariable, NotificationServicesVariable,
				TextVariable, ColorVariable],
			description='Add a static reminder'
		)
	),
	methods=['GET', 'POST']
)
@endpoint_wrapper
def api_static_reminders_list(inputs: Dict[str, Any]):
	reminders = api_key_map[g.hashed_api_key].user_data.static_reminders
	
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
	Methods(
		get=Method(
			vars=[TimelessSortByVariable, QueryVariable]
		)
	),
	methods=['GET']
)
@endpoint_wrapper
def api_static_reminders_query(inputs: Dict[str, str]):
	result = (api_key_map[g.hashed_api_key]
		.user_data
		.static_reminders
		.search(inputs['query'], inputs['sort_by']))
	return return_api(result)

@api.route(
	'/staticreminders/<int:s_id>',
	'Manage a specific static reminder',
	Methods(
		post=Method(
			description='Trigger the static reminder'
		),
		put=Method(
			vars=[EditTitleVariable, EditNotificationServicesVariable,
				TextVariable, ColorVariable],
			description='Edit the static reminder'
		),
		delete=Method(
			description='Delete the static reminder'
		)
	),
	methods=['GET', 'POST', 'PUT', 'DELETE']
)
@endpoint_wrapper
def api_get_static_reminder(inputs: Dict[str, Any], s_id: int):
	reminders = api_key_map[g.hashed_api_key].user_data.static_reminders

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

@admin_api.route(
	'/shutdown',
	'Shut down the application',
	methods=['POST']
)
@endpoint_wrapper
def api_shutdown():
	SERVER.shutdown()
	return return_api({})

@admin_api.route(
	'/restart',
	'Restart the application',
	methods=['POST']
)
@endpoint_wrapper
def api_restart():
	SERVER.restart()
	return return_api({})

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
	Methods(
		get=Method(
			description='Get the admin settings'
		),
		put=Method(
			vars=[AllowNewAccountsVariable, LoginTimeVariable,
				LoginTimeResetVariable, HostVariable, PortVariable,
				UrlPrefixVariable, LogLevelVariable],
			description='Edit the admin settings. Supplying a hosting setting will automatically restart MIND.'
		)
	),
	methods=['GET', 'PUT']
)
@endpoint_wrapper
def api_admin_settings(inputs: Dict[str, Any]):
	if request.method == 'GET':
		return return_api(get_admin_settings())

	elif request.method == 'PUT':
		LOGGER.info(f'Submitting admin settings: {inputs}')

		hosting_changes = any(
			inputs[s] is not None 
			for s in ('host', 'port', 'url_prefix')
		)

		if hosting_changes:
			backup_hosting_settings()
		
		for k, v in inputs.items():
			if v is not None:
				set_setting(k, v)

		if hosting_changes:
			SERVER.restart([RestartVars.HOST_CHANGE.value])
		
		return return_api({})

@admin_api.route(
	'/logs',
	'Get the debug logs',
	methods=['GET']
)
@endpoint_wrapper
def api_admin_logs():
	file = get_debug_log_filepath()
	if not exists(file):
		raise LogFileNotFound

	return send_file(file), 200

@admin_api.route(
	'/users',
	'Get all users or add one',
	Methods(
		get=Method(
			description='Get all users'
		),
		post=Method(
			vars=[UsernameCreateVariable, PasswordCreateVariable],
			description='Add a new user'
		)
	),
	methods=['GET', 'POST']
)
@endpoint_wrapper
def api_admin_users(inputs: Dict[str, Any]):
	if request.method == 'GET':
		result = users.get_all()
		return return_api(result)

	elif request.method == 'POST':
		users.add(inputs['username'], inputs['password'], True)
		return return_api({}, code=201)

@admin_api.route(
	'/users/<int:u_id>',
	'Manage a specific user',
	Methods(
		put=Method(
			vars=[NewPasswordVariable],
			description='Change the password of the user account'
		),
		delete=Method(
			description='Delete the user account'
		)
	),
	methods=['PUT', 'DELETE']
)
@endpoint_wrapper
def api_admin_user(inputs: Dict[str, Any], u_id: int):
	user = users.get_one(u_id)
	if request.method == 'PUT':
		user.edit_password(inputs['new_password'])
		return return_api({})
	
	elif request.method == 'DELETE':
		user.delete()
		for key, value in api_key_map.items():
			if value.user_data.user_id == u_id:
				del api_key_map[key]
				break
		return return_api({})

@admin_api.route(
	'/database',
	'Download and upload the database',
	Methods(
		get=Method(
			description="Download the database file"
		),
		post=Method(
			vars=[DatabaseFileVariable, CopyHostingSettingsVariable],
			description="Upload and apply a database file. Will automatically restart MIND."
		)
	),
	methods=['GET', 'POST']
)
@endpoint_wrapper
def api_admin_database(inputs: Dict[str, Any]):
	if request.method == "GET":
		current_date = datetime.now().strftime(r"%Y_%m_%d_%H_%M")
		filename = folder_path(
			'db', f'MIND_{current_date}.db'
		)
		get_db().execute(
			"VACUUM INTO ?;",
			(filename,)
		)

		with open(filename, 'rb') as database_file:
			bi = BytesIO(database_file.read())

		remove(filename)

		return send_file(
			bi,
			mimetype='application/x-sqlite3',
			download_name=basename(filename)
		), 200

	elif request.method == "POST":
		import_db(inputs['file'], inputs['copy_hosting_settings'])
		return return_api({})
