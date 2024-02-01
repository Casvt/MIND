#-*- coding: utf-8 -*-

"""
Input validation for the API
"""

from abc import ABC, abstractmethod
from re import compile
from typing import Any, Callable, Dict, List, Union

from apprise import Apprise
from flask import Blueprint, request
from flask.sansio.scaffold import T_route

from backend.custom_exceptions import (AccessUnauthorized, InvalidKeyValue,
                                       InvalidTime, KeyNotFound,
                                       NewAccountsNotAllowed,
                                       NotificationServiceNotFound,
                                       UsernameInvalid, UsernameTaken,
                                       UserNotFound)
from backend.helpers import (RepeatQuantity, SortingMethod,
                             TimelessSortingMethod)
from backend.settings import _format_setting

api_prefix = "/api"
_admin_api_prefix = '/admin'
admin_api_prefix = api_prefix + _admin_api_prefix

color_regex = compile(r'#[0-9a-f]{6}')

class DataSource:
	DATA = 1
	VALUES = 2


class InputVariable(ABC):
	value: Any
	
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
	_options = [k.lower() for k in SortingMethod._member_names_]
	default = SortingMethod._member_names_[0].lower()
	related_exceptions = [InvalidKeyValue]

	def __init__(self, value: str) -> None:
		self.value = value

	def validate(self) -> bool:
		if not self.value in self._options:
			return False

		self.value = SortingMethod[self.value.upper()]
		return True

	def __repr__(self) -> str:
		return '| {n} | {r} | {d} | {v} |'.format(
			n=self.name,
			r="Yes" if self.required else "No",
			d=self.description,
			v=", ".join(f'`{o}`' for o in self._options)
		)


class TemplateSortByVariable(SortByVariable):
	_options = [k.lower() for k in TimelessSortingMethod._member_names_]
	default = TimelessSortingMethod._member_names_[0].lower()

	def validate(self) -> bool:
		if not self.value in self._options:
			return False

		self.value = TimelessSortingMethod[self.value.upper()]
		return True

class StaticReminderSortByVariable(TemplateSortByVariable):
	pass


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
	_options = [m.lower() for m in RepeatQuantity._member_names_]
	default = None
	related_exceptions = [InvalidKeyValue]

	def validate(self) -> bool:
		if self.value is None:
			return True

		if not self.value in self._options:
			return False

		self.value = RepeatQuantity[self.value.upper()]
		return True

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
		return (
			self.value is None
			or (
				isinstance(self.value, int)
				and self.value > 0
			)
		)


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
		value: InputVariable = input_variable(input_value)

		if not value.validate():
			raise InvalidKeyValue(input_variable.name, input_value)

		inputs[input_variable.name] = value.value
	return inputs


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

api = APIBlueprint('api', __name__)
admin_api = APIBlueprint('admin_api', __name__)
