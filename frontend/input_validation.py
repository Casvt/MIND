# -*- coding: utf-8 -*-

"""
Input validation for the API.
"""

from __future__ import annotations

from logging import DEBUG, INFO
from os.path import splitext
from re import compile
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Tuple, Type, Union

from apprise import Apprise
from flask import Blueprint, Request, request

from backend.base.custom_exceptions import (AccessUnauthorized,
                                            InvalidDatabaseFile,
                                            InvalidKeyValue, InvalidTime,
                                            KeyNotFound, NewAccountsNotAllowed,
                                            NotificationServiceNotFound,
                                            UsernameInvalid, UsernameTaken)
from backend.base.definitions import (DataSource, DataType, MindException,
                                      RepeatQuantity, SortingMethod,
                                      TimelessSortingMethod)
from backend.base.helpers import folder_path
from backend.internals.server import Server

if TYPE_CHECKING:
    from flask import Request
    from flask.sansio.scaffold import T_route


# ===================
# region Definitions
# ===================
color_regex = compile(r'#[0-9a-f]{6}')


class InputVariable:
    name: str
    description: str
    required: bool = True
    options: List[Any] = []
    default: Any = None
    data_type: List[DataType] = [DataType.STR]
    source: DataSource = DataSource.DATA
    related_exceptions: List[Type[MindException]] = [
        KeyNotFound, InvalidKeyValue
    ]

    def __init__(self, value: Any) -> None:
        self.value = self.converted_value = value
        return

    def validate(self) -> bool:
        return isinstance(self.value, str) and bool(self.value)


class NonRequiredInputVariable(InputVariable):
    required = False
    related_exceptions = [InvalidKeyValue]

    def validate(self) -> bool:
        if self.value is None:
            return True
        return super().validate()


class Method:
    def __init__(
        self,
        description: str,
        input_variables: List[Type[InputVariable]]
    ) -> None:
        self.description = description
        self.input_variables = input_variables
        return


class Methods:
    def __init__(
        self,
        get: Union[Tuple[str, List[Type[InputVariable]]], None] = None,
        post: Union[Tuple[str, List[Type[InputVariable]]], None] = None,
        put: Union[Tuple[str, List[Type[InputVariable]]], None] = None,
        delete: Union[Tuple[str, List[Type[InputVariable]]], None] = None
    ) -> None:
        self.get = Method(*get) if get else None
        self.post = Method(*post) if post else None
        self.put = Method(*put) if put else None
        self.delete = Method(*delete) if delete else None
        return

    def __getitem__(self, key: str) -> Union[Method, None]:
        return getattr(self, key.lower())

    def used_methods(self) -> List[str]:
        result = []
        for method in ('get', 'post', 'put', 'delete'):
            if getattr(self, method) is not None:
                result.append(method)
        return result


class EndpointData:
    description: str = ""
    requires_auth: bool = True
    methods: Methods = Methods()


# ===================
# region Variables
# ===================
class UsernameVariable(InputVariable):
    name = "username"
    description = "The username of the user account"
    related_exceptions = [KeyNotFound, UsernameInvalid]


class PasswordVariable(InputVariable):
    name = "password"
    description = "The password of the user account"
    related_exceptions = [KeyNotFound, AccessUnauthorized]


class CreatePasswordVariable(PasswordVariable):
    related_exceptions = [KeyNotFound]


class CreateUsernameVariable(UsernameVariable):
    related_exceptions = [
        KeyNotFound,
        UsernameInvalid,
        UsernameTaken,
        NewAccountsNotAllowed
    ]


class NewPasswordVariable(InputVariable):
    name = "new_password"
    description = "The new password of the user account"
    related_exceptions = [KeyNotFound]


class TitleVariable(InputVariable):
    name = "title"
    description = "The title of the entry"


class URLVariable(InputVariable):
    name = "url"
    description = "The Apprise URL of the notification service"

    def validate(self) -> bool:
        return super().validate() and Apprise().add(self.value)


class EditTitleVariable(NonRequiredInputVariable, TitleVariable):
    pass


class EditURLVariable(NonRequiredInputVariable, URLVariable):
    pass


class SortByVariable(NonRequiredInputVariable, InputVariable):
    name = "sort_by"
    description = "How to sort the result"
    source = DataSource.VALUES
    options = [k.lower() for k in SortingMethod._member_names_]
    default = SortingMethod.TIME

    def validate(self) -> bool:
        if self.value not in self.options:
            return False

        self.converted_value = SortingMethod[self.value.upper()]
        return True


class TimelessSortByVariable(SortByVariable):
    options = [k.lower() for k in TimelessSortingMethod._member_names_]
    default = TimelessSortingMethod.TITLE

    def validate(self) -> bool:
        if self.value not in self.options:
            return False

        self.converted_value = TimelessSortingMethod[self.value.upper()]
        return True


class TimeVariable(InputVariable):
    name = "time"
    description = "The UTC epoch timestamp that the reminder should be sent at"
    data_type = [DataType.INT, DataType.FLOAT]
    related_exceptions = [KeyNotFound, InvalidKeyValue, InvalidTime]

    def validate(self) -> bool:
        return isinstance(self.value, (float, int))


class EditTimeVariable(NonRequiredInputVariable, TimeVariable):
    related_exceptions = [InvalidKeyValue, InvalidTime]


class NotificationServicesVariable(InputVariable):
    name = "notification_services"
    description = "Array of the id's of the notification services to use to send the notification"
    data_type = [DataType.INT_ARRAY]
    related_exceptions = [
        KeyNotFound,
        InvalidKeyValue,
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


class EditNotificationServicesVariable(
    NonRequiredInputVariable, NotificationServicesVariable
):
    related_exceptions = [
        InvalidKeyValue,
        NotificationServiceNotFound
    ]


class TextVariable(NonRequiredInputVariable):
    name = "text"
    description = "The body of the entry"
    default = ""

    def validate(self) -> bool:
        return isinstance(self.value, str)


class RepeatQuantityVariable(NonRequiredInputVariable):
    name = "repeat_quantity"
    description = "The quantity of the repeat_interval"
    options = [m.lower() for m in RepeatQuantity._member_names_]

    def validate(self) -> bool:
        if self.value is None:
            return True

        if self.value not in self.options:
            return False

        self.converted_value = RepeatQuantity[self.value.upper()]
        return True


class RepeatIntervalVariable(NonRequiredInputVariable):
    name = "repeat_interval"
    description = "The number of the interval"
    data_type = [DataType.INT]

    def validate(self) -> bool:
        return (
            self.value is None
            or (
                isinstance(self.value, int)
                and self.value > 0
            )
        )


class WeekDaysVariable(NonRequiredInputVariable):
    name = "weekdays"
    description = "On which days of the week to run the reminder"
    data_type = [DataType.INT_ARRAY]
    options = [0, 1, 2, 3, 4, 5, 6]

    def validate(self) -> bool:
        return self.value is None or (
            isinstance(self.value, list)
            and len(self.value) > 0
            and all(v in self.options for v in self.value)
        )


class ColorVariable(NonRequiredInputVariable):
    name = "color"
    description = "The hex code of the color of the entry, which is shown in the web-UI"

    def validate(self) -> bool:
        return self.value is None or (
            isinstance(self.value, str)
            and color_regex.search(self.value) is not None
        )


class QueryVariable(InputVariable):
    name = "query"
    description = "The search term"
    source = DataSource.VALUES


class DeleteRemindersUsingVariable(NonRequiredInputVariable):
    name = "delete_reminders_using"
    description = "Instead of throwing an error when there are still reminders using the service, delete the reminders"
    source = DataSource.VALUES
    default = False

    def validate(self) -> bool:
        if self.value == 'true':
            self.converted_value = True
            return True

        elif self.value == 'false':
            self.converted_value = False
            return True

        else:
            return False


class AllowNewAccountsVariable(NonRequiredInputVariable):
    name = "allow_new_accounts"
    description = (
        "Whether to allow users to register a new account. "
        "The admin can always add a new account."
    )
    data_type = [DataType.BOOL]

    def validate(self) -> bool:
        return self.value is None or (
            isinstance(self.value, bool)
        )


class LoginTimeVariable(NonRequiredInputVariable):
    name = "login_time"
    description = (
        "How long a user stays logged in, in seconds. "
        "Between 1 minute and 1 month (60 <= sec <= 2592000)."
    )
    data_type = [DataType.INT]

    def validate(self) -> bool:
        return (
            self.value is None
            or isinstance(self.value, int)
        )


class LoginTimeResetVariable(NonRequiredInputVariable):
    name = "login_time_reset"
    description = "Whether the Login Time timer should reset with each API request"
    data_type = [DataType.BOOL]

    def validate(self) -> bool:
        return self.value is None or (
            isinstance(self.value, bool)
        )


class HostVariable(NonRequiredInputVariable):
    name = "host"
    description = "The IP to bind to. Use 0.0.0.0 to bind to all addresses"


class PortVariable(NonRequiredInputVariable):
    name = "port"
    description = "The port to listen on"
    data_type = [DataType.INT]

    def validate(self) -> bool:
        return self.value is None or (
            isinstance(self.value, int)
        )


class UrlPrefixVariable(NonRequiredInputVariable):
    name = "url_prefix"
    description = "The base URL to run on. Useful for reverse proxies. Empty string to disable."


class LogLevelVariable(NonRequiredInputVariable):
    name = "log_level"
    description = "The level to log on"
    data_type = [DataType.INT]
    options = [INFO, DEBUG]

    def validate(self) -> bool:
        return self.value is None or (
            self.value in self.options
        )


class DatabaseFileVariable(InputVariable):
    name = "file"
    description = "The MIND database file"
    data_type = [DataType.NA]
    source = DataSource.FILES
    related_exceptions = [KeyNotFound, InvalidDatabaseFile]

    def validate(self) -> bool:
        if (
            self.value.filename
            and splitext(self.value.filename)[1] == ".db"
        ):
            path = folder_path("db", "MIND_upload.db")
            self.value.save(path)
            self.converted_value = path
            return True
        return False


class CopyHostingSettingsVariable(InputVariable):
    name = "copy_hosting_settings"
    description = "Copy the hosting settings from the current database"
    data_type = [DataType.BOOL]
    source = DataSource.VALUES

    def validate(self) -> bool:
        if self.value not in ("true", "false"):
            return False

        self.converted_value = self.value == "true"
        return True


# ===================
# region Endpoint Datas
# ===================
class AuthLoginData(EndpointData):
    description = "Login to a user account"
    requires_auth = False
    methods = Methods(
        post=("", [UsernameVariable, PasswordVariable])
    )


class AuthLogoutData(EndpointData):
    description = "Logout of a user account"
    methods = Methods(post=("", []))


class AuthStatusData(EndpointData):
    description = "Get current status of login"
    methods = Methods(get=("", []))


class UsersAddData(EndpointData):
    description = "Create a new user account"
    requires_auth = False
    methods = Methods(
        post=("", [CreateUsernameVariable, CreatePasswordVariable])
    )


class UsersData(EndpointData):
    description = "Manage a user account"
    methods = Methods(
        put=(
            "Change the password of the user account",
            [NewPasswordVariable]
        ),
        delete=(
            "Delete the user account",
            []
        )
    )


class NotificationServicesData(EndpointData):
    description = "Manage the notification services"
    methods = Methods(
        get=("Get a list of all notification services", []),
        post=(
            "Add a notification service",
            [TitleVariable, URLVariable]
        )
    )


class AvailableNotificationServicesData(EndpointData):
    description = "Get all available notification services and their URL layout"
    methods = Methods(get=("", []))


class TestNotificationServiceURLData(EndpointData):
    description = "Send a test notification using the supplied Apprise URL"
    methods = Methods(post=("", [URLVariable]))


class NotificationServiceData(EndpointData):
    description = "Manage a specific notification service"
    methods = Methods(
        get=("Get info of the notification service", []),
        put=(
            "Edit the notification service",
            [EditTitleVariable, EditURLVariable]
        ),
        delete=(
            "Delete the notification service",
            [DeleteRemindersUsingVariable]
        )
    )


class RemindersData(EndpointData):
    description = "Manage the reminders"
    methods = Methods(
        get=(
            "Get a list of reminders",
            [SortByVariable]
        ),
        post=(
            "Add a reminder",
            [
                TitleVariable,
                TimeVariable,
                NotificationServicesVariable,
                TextVariable,
                RepeatQuantityVariable,
                RepeatIntervalVariable,
                WeekDaysVariable,
                ColorVariable
            ]
        )
    )


class SearchRemindersData(EndpointData):
    description = "Search for reminders"
    methods = Methods(get=("", [QueryVariable, SortByVariable]))


class TestRemindersData(EndpointData):
    description = "Test send a reminder draft"
    methods = Methods(
        post=("", [TitleVariable, NotificationServicesVariable, TextVariable])
    )


class ReminderData(EndpointData):
    description = "Manage a specific reminder"
    methods = Methods(
        get=("Get info of the reminder", []),
        put=(
            "Edit the reminder",
            [
                EditTitleVariable,
                EditTimeVariable,
                EditNotificationServicesVariable,
                TextVariable,
                RepeatQuantityVariable,
                RepeatIntervalVariable,
                WeekDaysVariable,
                ColorVariable
            ]
        ),
        delete=(
            "Delete the reminder",
            []
        )
    )


class TemplatesData(EndpointData):
    description = "Manage the templates"
    methods = Methods(
        get=(
            "Get a list of all templates",
            [TimelessSortByVariable]
        ),
        post=(
            "Add a template",
            [
                TitleVariable,
                NotificationServicesVariable,
                TextVariable,
                ColorVariable
            ]
        )
    )


class SearchTemplatesData(EndpointData):
    description = "Search for templates"
    methods = Methods(get=("", [QueryVariable, TimelessSortByVariable]))


class TemplateData(EndpointData):
    description = "Manage a specific template"
    methods = Methods(
        get=("Get info of the template", []),
        put=(
            "Edit the template",
            [
                EditTitleVariable,
                EditNotificationServicesVariable,
                TextVariable,
                ColorVariable
            ]
        ),
        delete=(
            "Delete the template",
            []
        )
    )


class StaticRemindersData(EndpointData):
    description = "Manage the static reminders"
    methods = Methods(
        get=(
            "Get a list of all static reminders",
            [TimelessSortByVariable]
        ),
        post=(
            "Add a static reminder",
            [
                TitleVariable,
                NotificationServicesVariable,
                TextVariable,
                ColorVariable
            ]
        )
    )


class SearchStaticRemindersData(EndpointData):
    description = "Search for static reminders"
    methods = Methods(get=("", [QueryVariable, TimelessSortByVariable]))


class StaticReminderData(EndpointData):
    description = "Manage a specific static reminder"
    methods = Methods(
        get=("Get info of the static reminder", []),
        post=("Trigger the static reminder", []),
        put=(
            "Edit the static reminder",
            [
                EditTitleVariable,
                EditNotificationServicesVariable,
                TextVariable,
                ColorVariable
            ]
        ),
        delete=(
            "Delete the static reminder",
            []
        )
    )


class ShutdownData(EndpointData):
    description = "Shut down the application"
    methods = Methods(post=("", []))


class RestartData(EndpointData):
    description = "Restart the application"
    methods = Methods(post=("", []))


class PublicSettingsData(EndpointData):
    description = "Get the admin settings"
    requires_auth = False
    methods = Methods(get=("", []))


class AboutData(EndpointData):
    description = "Get data about the application and it's environment"
    requires_auth = False
    methods = Methods(get=("", []))


class SettingsData(EndpointData):
    desription = "Interact with the admin settings"
    methods = Methods(
        get=("Get the admin settings", []),
        put=(
            ("Edit the admin settings. "
             "Supplying a hosting setting will automatically restart MIND."),
            [
                AllowNewAccountsVariable,
                LoginTimeVariable,
                LoginTimeResetVariable,
                HostVariable,
                PortVariable,
                UrlPrefixVariable,
                LogLevelVariable
            ]
        )
    )


class LogfileData(EndpointData):
    description = "Get the logfile"
    methods = Methods(get=("", []))


class UsersManagementData(EndpointData):
    description = "Manage the users"
    methods = Methods(
        get=(
            "Get a list of all users",
            []
        ),
        post=(
            "Add a user",
            [
                CreateUsernameVariable,
                CreatePasswordVariable
            ]
        )
    )


class UserManagementData(EndpointData):
    description = "Manage a specific user"
    methods = Methods(
        put=(
            "Change the password of the user account",
            [NewPasswordVariable]
        ),
        delete=(
            "Delete the user account",
            []
        )
    )


class DatabaseData(EndpointData):
    description = "Download and upload the database"
    methods = Methods(
        get=(
            "Download the database",
            []
        ),
        post=(
            "Upload and apply a database file. Will automatically restart MIND.",
            [DatabaseFileVariable, CopyHostingSettingsVariable]
        )
    )


# ===================
# region Integration
# ===================
API_DOCS: Dict[str, Type[EndpointData]] = {}


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


def get_api_docs(request: Request) -> Type[EndpointData]:
    """Returns the API documentation for the given request.

    Args:
        request (Request): The request object.

    Returns:
        Type[EndpointData]: The API documentation for the used endpoint.
    """
    assert request.url_rule is not None

    if request.path.startswith(Server.admin_prefix):
        url = (
            Server.admin_api_extension +
            request.url_rule.rule.split(Server.admin_prefix)[1]
        )
    else:
        url = request.url_rule.rule.split(Server.api_prefix)[1]

    return API_DOCS[url]


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
    noted_variables = method.input_variables
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
        value = noted_var(input_value)

        if not value.validate():
            if isinstance(value, DatabaseFileVariable):
                raise InvalidDatabaseFile(value.value)
            elif noted_var.source == DataSource.FILES:
                raise InvalidKeyValue(noted_var.name, input_value.filename)
            else:
                raise InvalidKeyValue(noted_var.name, input_value)

        result[noted_var.name] = value.converted_value

    return result


class APIBlueprint(Blueprint):
    def route( # type: ignore
        self,
        rule: str,
        endpoint_data: Type[EndpointData],
        **options: Any
    ) -> Callable[[T_route], T_route]:

        if self == api:
            processed_rule = rule
        elif self == admin_api:
            processed_rule = Server.admin_api_extension + rule
        else:
            raise NotImplementedError

        API_DOCS[processed_rule] = endpoint_data

        if "methods" not in options:
            options["methods"] = API_DOCS[processed_rule].methods.used_methods()

        return super().route(rule, **options)


api = APIBlueprint('api', __name__)
admin_api = APIBlueprint('admin_api', __name__)
