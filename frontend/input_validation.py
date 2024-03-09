#-*- coding: utf-8 -*-

"""
Input validation for the API
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import logging
from os.path import splitext
from re import compile
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Type, Union

from apprise import Apprise
from flask import Blueprint, request
from flask.sansio.scaffold import T_route

from backend.custom_exceptions import (AccessUnauthorized, InvalidDatabaseFile,
                                       InvalidKeyValue, InvalidTime,
                                       KeyNotFound, NewAccountsNotAllowed,
                                       NotificationServiceNotFound,
                                       UsernameInvalid, UsernameTaken,
                                       UserNotFound)
from backend.helpers import (RepeatQuantity, SortingMethod,
                             TimelessSortingMethod, folder_path)
from backend.server import SERVER
from backend.settings import _format_setting

if TYPE_CHECKING:
	from flask import Request

color_regex = compile(r'#[0-9a-f]{6}')

api_docs: Dict[str, ApiDocEntry] = {}


class DataSource:
	DATA = 1
	VALUES = 2
	FILES = 3

	def __init__(self, request: Request) -> None:
		self.map: Dict[int, dict] = {
			self.DATA: request.get_json() if request.data else {},
			self.VALUES: request.values,
			self.FILES: request.files
		}
		return

	def __getitem__(self, key: int) -> dict:
		return self.map[key]


class DataType:
	STR = 'string'
	INT = 'number'
	FLOAT = 'decimal number'
	BOOL = 'bool'
	INT_ARRAY = 'list of numbers'
	NA = 'N/A'


class InputVariable(ABC):
	value: Any

	@abstractmethod
	def __init__(self, value: Any) -> None:
		pass

	@property
	@abstractmethod
	def name(self) -> str:
		pass

	@abstractmethod
	def validate(self) -> bool:
		pass

	@property
	@abstractmethod
	def required(self) -> bool:
		pass

	@property
	@abstractmethod
	def data_type(self) -> List[str]:
		pass

	@property
	@abstractmethod
	def default(self) -> Any:
		pass

	@property
	@abstractmethod
	def source(self) -> int:
		pass

	@property
	@abstractmethod
	def description(self) -> str:
		pass

	@property
	@abstractmethod
	def related_exceptions(self) -> List[Exception]:
		pass


@dataclass(frozen=True)
class Method:
	description: str = ''
	vars: List[Type[InputVariable]] = field(default_factory=list)
	
	def __bool__(self) -> bool:
		return self.vars != []


@dataclass(frozen=True)
class Methods:
	get: Method = Method()
	post: Method = Method()
	put: Method = Method()
	delete: Method = Method()

	def __getitem__(self, key: str) -> Method:
		return getattr(self, key.lower())

	def __bool__(self) -> bool:
		return bool(self.get or self.post or self.put or self.delete)


@dataclass(frozen=True)
class ApiDocEntry:
	endpoint: str
	description: str
	requires_auth: bool
	used_methods: List[str]
	methods: Methods


def get_api_docs(request: Request) -> ApiDocEntry:
	if request.path.startswith(SERVER.admin_prefix):
		url = SERVER.admin_api_extension + request.url_rule.rule.split(SERVER.admin_prefix)[1]
	else:
		url = request.url_rule.rule.split(SERVER.api_prefix)[1]
	return api_docs[url]


class BaseInputVariable(InputVariable):
	source = DataSource.DATA
	data_type = [DataType.STR]
	required = True
	default = None
	related_exceptions = [KeyNotFound, InvalidKeyValue]

	def __init__(self, value: Any) -> None:
		self.value = value

	def validate(self) -> bool:
		return isinstance(self.value, str) and self.value

	def __repr__(self) -> str:
		return f'| {self.name} | {"Yes" if self.required else "No"} | {",".join(self.data_type)} | {self.description} | N/A |'


class NonRequiredVersion(BaseInputVariable):
	required = False
	related_exceptions = [InvalidKeyValue]

	def __init__(self, value: Any) -> None:
		super().__init__(
			value
			if value is not None else
			self.default
		)
		return

	def validate(self) -> bool:
		return self.value is None or super().validate()


class UsernameVariable(BaseInputVariable):
	name = 'username'
	description = 'The username of the user account'
	related_exceptions = [KeyNotFound, UserNotFound]


class PasswordCreateVariable(BaseInputVariable):
	name = 'password'
	description = 'The password of the user account'
	related_exceptions = [KeyNotFound]


class PasswordVariable(PasswordCreateVariable):
	related_exceptions = [KeyNotFound, AccessUnauthorized]


class UsernameCreateVariable(UsernameVariable):
	related_exceptions = [
		KeyNotFound,
		UsernameInvalid, UsernameTaken,
		NewAccountsNotAllowed
	]


class NewPasswordVariable(BaseInputVariable):
	name = 'new_password'
	description = 'The new password of the user account'
	related_exceptions = [KeyNotFound]


class TitleVariable(BaseInputVariable):
	name = 'title'
	description = 'The title of the entry'


class URLVariable(BaseInputVariable):
	name = 'url'
	description = 'The Apprise URL of the notification service'

	def validate(self) -> bool:
		return super().validate() and Apprise().add(self.value)


class EditTitleVariable(NonRequiredVersion, TitleVariable):
	pass


class EditURLVariable(NonRequiredVersion, URLVariable):
	pass


class SortByVariable(NonRequiredVersion, BaseInputVariable):
	name = 'sort_by'
	description = 'How to sort the result'
	source = DataSource.VALUES
	_options = [k.lower() for k in SortingMethod._member_names_]
	default = SortingMethod._member_names_[0].lower()

	def validate(self) -> bool:
		if not self.value in self._options:
			return False

		self.value = SortingMethod[self.value.upper()]
		return True

	def __repr__(self) -> str:
		return '| {n} | {r} | {t} | {d} | {v} |'.format(
			n=self.name,
			r="Yes" if self.required else "No",
			t=",".join(self.data_type),
			d=self.description,
			v=", ".join(f'`{o}`' for o in self._options)
		)


class TimelessSortByVariable(SortByVariable):
	_options = [k.lower() for k in TimelessSortingMethod._member_names_]
	default = TimelessSortingMethod._member_names_[0].lower()

	def validate(self) -> bool:
		if not self.value in self._options:
			return False

		self.value = TimelessSortingMethod[self.value.upper()]
		return True


class TimeVariable(BaseInputVariable):
	name = 'time'
	description = 'The UTC epoch timestamp that the reminder should be sent at'
	data_type = [DataType.INT, DataType.FLOAT]
	related_exceptions = [KeyNotFound, InvalidKeyValue, InvalidTime]

	def validate(self) -> bool:
		return isinstance(self.value, (float, int))


class EditTimeVariable(NonRequiredVersion, TimeVariable):
	related_exceptions = [InvalidKeyValue, InvalidTime]


class NotificationServicesVariable(BaseInputVariable):
	name = 'notification_services'
	description = "Array of the id's of the notification services to use to send the notification"
	data_type = [DataType.INT_ARRAY]
	related_exceptions = [
		KeyNotFound, InvalidKeyValue,
		NotificationServiceNotFound
	]

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


class TextVariable(NonRequiredVersion, BaseInputVariable):
	name = 'text'
	description = 'The body of the entry'
	default = ''

	def validate(self) -> bool:
		return isinstance(self.value, str)


class RepeatQuantityVariable(NonRequiredVersion, BaseInputVariable):
	name = 'repeat_quantity'
	description = 'The quantity of the repeat_interval'
	_options = [m.lower() for m in RepeatQuantity._member_names_]

	def validate(self) -> bool:
		if self.value is None:
			return True

		if not self.value in self._options:
			return False

		self.value = RepeatQuantity[self.value.upper()]
		return True

	def __repr__(self) -> str:
		return '| {n} | {r} | {t} | {d} | {v} |'.format(
			n=self.name,
			r="Yes" if self.required else "No",
			t=",".join(self.data_type),
			d=self.description,
			v=", ".join(f'`{o}`' for o in self._options)
		)


class RepeatIntervalVariable(NonRequiredVersion, BaseInputVariable):
	name = 'repeat_interval'
	description = 'The number of the interval'
	data_type = [DataType.INT]

	def validate(self) -> bool:
		return (
			self.value is None
			or (
				isinstance(self.value, int)
				and self.value > 0
			)
		)


class WeekDaysVariable(NonRequiredVersion, BaseInputVariable):
	name = 'weekdays'
	description = 'On which days of the weeks to run the reminder'
	data_type = [DataType.INT_ARRAY]
	_options = {0, 1, 2, 3, 4, 5, 6}

	def validate(self) -> bool:
		return self.value is None or (
			isinstance(self.value, list)
			and len(self.value) > 0
			and all(v in self._options for v in self.value)
		)

	def __repr__(self) -> str:
		return '| {n} | {r} | {t} | {d} | {v} |'.format(
			n=self.name,
			r="Yes" if self.required else "No",
			t=",".join(self.data_type),
			d=self.description,
			v=", ".join(f'`{o}`' for o in self._options)
		)

class ColorVariable(NonRequiredVersion, BaseInputVariable):
	name = 'color'
	description = 'The hex code of the color of the entry, which is shown in the web-ui'

	def validate(self) -> bool:
		return self.value is None or (
			isinstance(self.value, str)
			and color_regex.search(self.value)
		)


class QueryVariable(BaseInputVariable):
	name = 'query'
	description = 'The search term'
	source = DataSource.VALUES


class DeleteRemindersUsingVariable(NonRequiredVersion, BaseInputVariable):
	name = 'delete_reminders_using'
	description = 'Instead of throwing an error when there are still reminders using the service, delete the reminders.'
	source = DataSource.VALUES
	default = 'false'
	data_type = [DataType.BOOL]

	def validate(self) -> bool:
		if self.value == 'true':
			self.value = True
			return True

		elif self.value == 'false':
			self.value = False
			return True

		else:
			return False


class AdminSettingsVariable(BaseInputVariable):
	def validate(self) -> bool:
		try:
			_format_setting(self.name, self.value)
		except InvalidKeyValue:
			return False
		return True


class AllowNewAccountsVariable(NonRequiredVersion, AdminSettingsVariable):
	name = 'allow_new_accounts'
	description = ('Whether or not to allow users to register a new account. '
	+ 'The admin can always add a new account.')
	data_type = [DataType.BOOL]


class LoginTimeVariable(NonRequiredVersion, AdminSettingsVariable):
	name = 'login_time'
	description = ('How long a user stays logged in, in seconds. '
	+ 'Between 1 min and 1 month (60 <= sec <= 2592000)')
	data_type = [DataType.INT]


class LoginTimeResetVariable(NonRequiredVersion, AdminSettingsVariable):
	name = 'login_time_reset'
	description = 'If the Login Time timer should reset with each API request.'
	data_type = [DataType.BOOL]


class HostVariable(NonRequiredVersion, AdminSettingsVariable):
	name = 'host'
	description = 'The IP to bind to. Use 0.0.0.0 to bind to all addresses.'


class PortVariable(NonRequiredVersion, AdminSettingsVariable):
	name = 'port'
	description = 'The port to listen on.'
	data_type = [DataType.INT]


class UrlPrefixVariable(NonRequiredVersion, AdminSettingsVariable):
	name = 'url_prefix'
	description = 'The base url to run on. Useful for reverse proxies. Empty string to disable.'


class LogLevelVariable(NonRequiredVersion, AdminSettingsVariable):
	name = 'log_level'
	description = 'The level to log on.'
	data_type = [DataType.INT]
	_options = [logging.INFO, logging.DEBUG]

	def __repr__(self) -> str:
		return '| {n} | {r} | {t} | {d} | {v} |'.format(
			n=self.name,
			r="Yes" if self.required else "No",
			t=",".join(self.data_type),
			d=self.description,
			v=", ".join(f'`{o}`' for o in self._options)
		)


class DatabaseFileVariable(BaseInputVariable):
	name = 'file'
	description = 'The MIND database file'
	data_type = [DataType.NA]
	source = DataSource.FILES
	related_exceptions = [KeyNotFound, InvalidDatabaseFile]

	def validate(self) -> bool:
		if (
			self.value.filename
			and splitext(self.value.filename)[1] == '.db'
		):
			path = folder_path('db', 'MIND_upload.db')
			self.value.save(path)
			self.value = path
			return True
		else:
			return False


class CopyHostingSettingsVariable(BaseInputVariable):
	name = 'copy_hosting_settings'
	description = 'Copy the hosting settings from the current database'
	data_type = [DataType.BOOL]
	source = DataSource.VALUES

	def validate(self) -> bool:
		if not self.value in ('true', 'false'):
			return False

		self.value = self.value == 'true'
		return True


def input_validation() -> Union[None, Dict[str, Any]]:
	"""Checks, extracts and transforms inputs

	Raises:
		KeyNotFound: A required key was not supplied
		InvalidKeyValue: The value of a key is not valid

	Returns:
		Union[None, Dict[str, Any]]: `None` if the endpoint + method doesn't require input variables.
		Otherwise `Dict[str, Any]` with the input variables, checked and formatted.
	"""
	result = {}

	methods = get_api_docs(request).methods
	method = methods[request.method]
	noted_variables = method.vars

	if not methods:
		return None

	if not method:
		return result

	given_variables = DataSource(request)

	for noted_var in noted_variables:
		if (
			noted_var.required and
			not noted_var.name in given_variables[noted_var.source]
		):
			raise KeyNotFound(noted_var.name)

		input_value = given_variables[noted_var.source].get(noted_var.name)
		value: InputVariable = noted_var(input_value)

		if not value.validate():
			if noted_var.__class__.__name__ == DatabaseFileVariable.__name__:
				raise InvalidDatabaseFile
			elif noted_var.source == DataSource.FILES:
				raise InvalidKeyValue(noted_var.name, input_value.filename)
			else:
				raise InvalidKeyValue(noted_var.name, input_value)

		result[noted_var.name] = value.value
	return result


class APIBlueprint(Blueprint):
	def route(
		self,
		rule: str,
		description: str = '',
		input_variables: Methods = Methods(),
		requires_auth: bool = True,
		**options: Any
	) -> Callable[[T_route], T_route]:

		if self == api:
			processed_rule = rule
		elif self == admin_api:
			processed_rule = SERVER.admin_api_extension + rule
		else:
			raise NotImplementedError

		api_docs[processed_rule] = ApiDocEntry(
			endpoint=processed_rule,
			description=description,
			requires_auth=requires_auth,
			used_methods=options['methods'],
			methods=input_variables
		)

		return super().route(rule, **options)

api = APIBlueprint('api', __name__)
admin_api = APIBlueprint('admin_api', __name__)
