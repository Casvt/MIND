# -*- coding: utf-8 -*-

"""
Input validation for the API
"""

from __future__ import annotations

from dataclasses import dataclass, field
from logging import DEBUG, INFO
from os.path import splitext
from re import compile
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Type

from apprise import Apprise
from flask import Blueprint, request

from backend.base.custom_exceptions import (AccessUnauthorized,
                                            InvalidDatabaseFile,
                                            InvalidKeyValue, InvalidTime,
                                            KeyNotFound, NewAccountsNotAllowed,
                                            NotificationServiceNotFound,
                                            UsernameInvalid, UsernameTaken)
from backend.base.definitions import (ApiDocEntry, DataSource, DataType,
                                      InputVariable, Methods, MindException,
                                      SortingMethod, T, TimelessSortingMethod)
from backend.base.helpers import RepeatQuantity, folder_path
from backend.internals.server import Server

if TYPE_CHECKING:
    from flask import Request
    from flask.sansio.scaffold import T_route


color_regex = compile(r'#[0-9a-f]{6}')
api_docs: Dict[str, ApiDocEntry] = {}


def request_data(request: Request) -> Dict[DataSource, Dict[str, Any]]:
    """Returns the request data in a dictionary.

    Args:
        request (Request): The request object.

    Returns:
        Dict[DataSource, Dict[str, Any]]: The request data.
    """
    return {
        DataSource.DATA: request.get_json() if request.data else {},
        DataSource.VALUES: request.values,
        DataSource.FILES: request.files
    }


def get_api_docs(request: Request) -> ApiDocEntry:
    """Returns the API documentation for the given request.

    Args:
        request (Request): The request object.

    Returns:
        ApiDocEntry: The API documentation for the used endpoint.
    """
    assert (request.url_rule is not None)

    if request.path.startswith(Server.admin_prefix):
        url = (
            Server.admin_api_extension +
            request.url_rule.rule.split(Server.admin_prefix)[1]
        )
    else:
        url = request.url_rule.rule.split(Server.api_prefix)[1]

    return api_docs[url]


def dl(*args: T) -> List[T]:
    return field(default_factory=lambda: list(args))


@dataclass
class NonRequiredVersion(InputVariable):
    required: bool = False
    related_exceptions: List[Type[MindException]] = dl(InvalidKeyValue)

    def __post_init__(self) -> None:
        if self.value is None:
            self.value = self.default
        return

    def validate(self) -> bool:
        return self.value is None or super().validate()


# ===================
# region Variables
# ===================
@dataclass
class UsernameVariable(InputVariable):
    name: str = 'username'
    description: str = 'The username of the user account'
    related_exceptions: List[Type[MindException]] = dl(
        KeyNotFound, UsernameInvalid
    )


@dataclass
class PasswordCreateVariable(InputVariable):
    name: str = 'password'
    description: str = 'The password of the user account'
    related_exceptions: List[Type[MindException]] = dl(KeyNotFound)


@dataclass
class PasswordVariable(PasswordCreateVariable):
    related_exceptions: List[Type[MindException]] = dl(
        KeyNotFound, AccessUnauthorized)


@dataclass
class UsernameCreateVariable(UsernameVariable):
    related_exceptions: List[Type[MindException]] = dl(
        KeyNotFound,
        UsernameInvalid, UsernameTaken,
        NewAccountsNotAllowed
    )


@dataclass
class NewPasswordVariable(InputVariable):
    name: str = 'new_password'
    description: str = 'The new password of the user account'
    related_exceptions: List[Type[MindException]] = dl(KeyNotFound)


@dataclass
class TitleVariable(InputVariable):
    name: str = 'title'
    description: str = 'The title of the entry'


@dataclass
class URLVariable(InputVariable):
    name: str = 'url'
    description: str = 'The Apprise URL of the notification service'

    def validate(self) -> bool:
        return super().validate() and Apprise().add(self.value)


@dataclass
class EditTitleVariable(NonRequiredVersion, TitleVariable):
    pass


@dataclass
class EditURLVariable(NonRequiredVersion, URLVariable):
    pass


@dataclass
class SortByVariable(NonRequiredVersion, InputVariable):
    name: str = 'sort_by'
    description: str = 'How to sort the result'
    source: DataSource = DataSource.VALUES
    _options: List[str] = dl(*(k.lower() for k in SortingMethod._member_names_))
    default: Any = SortingMethod.TIME

    def validate(self) -> bool:
        if self.value not in self._options:
            return False

        self.value = SortingMethod[self.value.upper()]
        return True

    def __repr__(self) -> str:
        return '| {n} | {r} | {t} | {d} | {v} |'.format(
            n=self.name,
            r="Yes" if self.required else "No",
            t=",".join(d.value for d in self.data_type),
            d=self.description,
            v=", ".join(f'`{o}`' for o in self._options)
        )


@dataclass
class TimelessSortByVariable(SortByVariable):
    _options: List[str] = dl(*(k.lower()
                             for k in TimelessSortingMethod._member_names_))
    default: Any = TimelessSortingMethod.TITLE

    def validate(self) -> bool:
        if self.value not in self._options:
            return False

        self.value = TimelessSortingMethod[self.value.upper()]
        return True


@dataclass
class TimeVariable(InputVariable):
    name: str = 'time'
    description: str = 'The UTC epoch timestamp that the reminder should be sent at'
    data_type: List[DataType] = dl(DataType.INT, DataType.FLOAT)
    related_exceptions: List[Type[MindException]] = dl(
        KeyNotFound, InvalidKeyValue, InvalidTime)

    def validate(self) -> bool:
        return isinstance(self.value, (float, int))


@dataclass
class EditTimeVariable(NonRequiredVersion, TimeVariable):
    related_exceptions: List[Type[MindException]] = dl(
        InvalidKeyValue, InvalidTime)


@dataclass
class NotificationServicesVariable(InputVariable):
    name: str = 'notification_services'
    description: str = "Array of the id's of the notification services to use to send the notification"
    data_type: List[DataType] = dl(DataType.INT_ARRAY)
    related_exceptions: List[Type[MindException]] = dl(
        KeyNotFound, InvalidKeyValue,
        NotificationServiceNotFound
    )

    def validate(self) -> bool:
        if not isinstance(self.value, list):
            return False
        if not self.value:
            return False
        for v in self.value:
            if not isinstance(v, int):
                return False
        return True


@dataclass
class EditNotificationServicesVariable(
    NonRequiredVersion,
    NotificationServicesVariable
):
    related_exceptions: List[Type[MindException]] = dl(
        InvalidKeyValue, NotificationServiceNotFound)


@dataclass
class TextVariable(NonRequiredVersion):
    name: str = 'text'
    description: str = 'The body of the entry'
    default: Any = ''

    def validate(self) -> bool:
        return isinstance(self.value, str)


@dataclass
class RepeatQuantityVariable(NonRequiredVersion):
    name: str = 'repeat_quantity'
    description: str = 'The quantity of the repeat_interval'
    _options: List[str] = dl(*(m.lower()
                             for m in RepeatQuantity._member_names_))

    def validate(self) -> bool:
        if self.value is None:
            return True

        if self.value not in self._options:
            return False

        self.value = RepeatQuantity[self.value.upper()]
        return True

    def __repr__(self) -> str:
        return '| {n} | {r} | {t} | {d} | {v} |'.format(
                n=self.name,
                r="Yes" if self.required else "No",
                t=",".join(d.value for d in self.data_type),
                d=self.description,
                v=", ".join(f'`{o}`' for o in self._options)
        )


@dataclass
class RepeatIntervalVariable(NonRequiredVersion):
    name: str = 'repeat_interval'
    description: str = 'The number of the interval'
    data_type: List[DataType] = dl(DataType.INT)

    def validate(self) -> bool:
        return (
            self.value is None
            or (
                isinstance(self.value, int)
                and self.value > 0
            )
        )


@dataclass
class WeekDaysVariable(NonRequiredVersion):
    name: str = 'weekdays'
    description: str = 'On which days of the weeks to run the reminder'
    data_type: List[DataType] = dl(DataType.INT_ARRAY)
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
            t=",".join(d.value for d in self.data_type),
            d=self.description,
            v=", ".join(f'`{o}`' for o in self._options)
        )


@dataclass
class ColorVariable(NonRequiredVersion):
    name: str = 'color'
    description: str = 'The hex code of the color of the entry, which is shown in the web-ui'

    def validate(self) -> bool:
        return self.value is None or (
            isinstance(self.value, str)
            and color_regex.search(self.value) is not None
        )


@dataclass
class QueryVariable(InputVariable):
    name: str = 'query'
    description: str = 'The search term'
    source: DataSource = DataSource.VALUES


@dataclass
class DeleteRemindersUsingVariable(NonRequiredVersion):
    name: str = 'delete_reminders_using'
    description: str = 'Instead of throwing an error when there are still reminders using the service, delete the reminders.'
    source: DataSource = DataSource.VALUES
    default: Any = 'false'
    data_type: List[DataType] = dl(DataType.BOOL)

    def validate(self) -> bool:
        if self.value == 'true':
            self.value = True
            return True

        elif self.value == 'false':
            self.value = False
            return True

        else:
            return False


@dataclass
class AdminSettingsVariable(InputVariable):
    def validate(self) -> bool:
        # @dataclassValidation is done in
        #  the settings class
        return True


@dataclass
class AllowNewAccountsVariable(NonRequiredVersion, AdminSettingsVariable):
    name: str = 'allow_new_accounts'
    description: str = (
        'Whether or not to allow users to register a new account. ' +
        'The admin can always add a new account.')
    data_type: List[DataType] = dl(DataType.BOOL)


@dataclass
class LoginTimeVariable(NonRequiredVersion, AdminSettingsVariable):
    name: str = 'login_time'
    description: str = ('How long a user stays logged in, in seconds. '
    + 'Between 1 min and 1 month (60 <= sec <= 2592000)')
    data_type: List[DataType] = dl(DataType.INT)


@dataclass
class LoginTimeResetVariable(NonRequiredVersion, AdminSettingsVariable):
    name: str = 'login_time_reset'
    description: str = 'If the Login Time timer should reset with each API request.'
    data_type: List[DataType] = dl(DataType.BOOL)


@dataclass
class HostVariable(NonRequiredVersion, AdminSettingsVariable):
    name: str = 'host'
    description: str = 'The IP to bind to. Use 0.0.0.0 to bind to all addresses.'


@dataclass
class PortVariable(NonRequiredVersion, AdminSettingsVariable):
    name: str = 'port'
    description: str = 'The port to listen on.'
    data_type: List[DataType] = dl(DataType.INT)


@dataclass
class UrlPrefixVariable(NonRequiredVersion, AdminSettingsVariable):
    name: str = 'url_prefix'
    description: str = 'The base url to run on. Useful for reverse proxies. Empty string to disable.'


@dataclass
class LogLevelVariable(NonRequiredVersion, AdminSettingsVariable):
    name: str = 'log_level'
    description: str = 'The level to log on.'
    data_type: List[DataType] = dl(DataType.INT)
    _options = [INFO, DEBUG]

    def __repr__(self) -> str:
        return '| {n} | {r} | {t} | {d} | {v} |'.format(
            n=self.name,
            r="Yes" if self.required else "No",
            t=",".join(d.value for d in self.data_type),
            d=self.description,
            v=", ".join(f'`{o}`' for o in self._options)
        )


@dataclass
class DatabaseFileVariable(InputVariable):
    name: str = 'file'
    description: str = 'The MIND database file'
    data_type: List[DataType] = dl(DataType.NA)
    source: DataSource = DataSource.FILES
    related_exceptions: List[Type[MindException]] = dl(
        KeyNotFound, InvalidDatabaseFile)

    def validate(self) -> bool:
        if (
            self.value.filename
            and splitext(self.value.filename)[1] == '.db'
        ):
            path = folder_path('db', 'MIND_upload.db')
            self.value.save(path)
            self.value = path
            return True

        return False


@dataclass
class CopyHostingSettingsVariable(InputVariable):
    name: str = 'copy_hosting_settings'
    description: str = 'Copy the hosting settings from the current database'
    data_type: List[DataType] = dl(DataType.BOOL)
    source: DataSource = DataSource.VALUES

    def validate(self) -> bool:
        if self.value not in ('true', 'false'):
            return False

        self.value = self.value == 'true'
        return True


# ===================
# region Endpoints
# ===================
def input_validation() -> Dict[str, Any]:
    """Checks, extracts and transforms inputs.

    Raises:
        KeyNotFound: A required key was not supplied.
        InvalidKeyValue: The value of a key is not valid.

    Returns:
        Dict[str, Any]: The input variables, checked and formatted.
    """
    method = get_api_docs(request).methods[request.method]
    if not method:
        return {}

    result = {}
    noted_variables = method.vars
    given_variables = request_data(request)
    for noted_var in noted_variables:
        if noted_var.name not in given_variables[noted_var.source]:
            if noted_var.required:
                # Variable not given while required
                raise KeyNotFound(noted_var.name)
            else:
                # Variable not given while not required, so set to default
                result[noted_var.name] = noted_var.default
                continue

        input_value = given_variables[noted_var.source][noted_var.name]
        value = noted_var(input_value) # type: ignore

        if not value.validate():
            if isinstance(value, DatabaseFileVariable):
                raise InvalidDatabaseFile(value.value)
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
            processed_rule = Server.admin_api_extension + rule
        else:
            raise NotImplementedError

        api_docs[processed_rule] = ApiDocEntry(
            endpoint=processed_rule,
            description=description,
            requires_auth=requires_auth,
            methods=input_variables
        )

        if "methods" not in options:
            options["methods"] = api_docs[processed_rule].methods.used_methods()

        return super().route(rule, **options)


api = APIBlueprint('api', __name__)
admin_api = APIBlueprint('admin_api', __name__)
