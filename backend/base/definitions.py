# -*- coding: utf-8 -*-

"""
Definitions of basic types, abstract classes, enums, etc.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import (Any, Callable, Dict, List, Literal, Sequence,
                    Tuple, TypedDict, TypeVar, Union, cast)

from flask import Response

# region Types
T = TypeVar('T')
U = TypeVar('U')
MISSING = object()
WEEKDAY_NUMBER = Literal[0, 1, 2, 3, 4, 5, 6]

BaseJSONSerialisable = Union[
    int, float, bool, str, None, TypedDict
]
JSONSerialisable = Union[
    BaseJSONSerialisable,
    TypedDict,
    Sequence["JSONSerialisable"],
    Dict[str, "JSONSerialisable"]
]
EndpointResponse = Union[
    Tuple[Dict[str, JSONSerialisable], int],
    Tuple[Response, int],
    None
]
EndpointHandler = Union[
    Callable[[], EndpointResponse],
    Callable[[int], EndpointResponse]
]


# region Constants
class Constants:
    MIN_PYTHON_VERSION = (3, 8, 0)

    SUB_PROCESS_TIMEOUT = 20.0 # seconds

    HOSTING_THREADS = 10
    HOSTING_REVERT_TIME = 60.0 # seconds
    API_PREFIX = "/api"
    ADMIN_API_EXTENSION = "/admin"
    ADMIN_PREFIX = API_PREFIX + ADMIN_API_EXTENSION
    API_KEY_LENGTH = 32 # hexadecimal characters
    API_KEY_CLEANUP_INTERVAL = 86400 # seconds
    MFA_CODE_TIMEOUT = 300 # seconds

    DB_FOLDER = ("db",)
    DB_NAME = "MIND.db"
    DB_ORIGINAL_NAME = 'MIND_original.db'
    DB_TIMEOUT = 10.0 # seconds
    DB_REVERT_TIME = 60.0 # seconds

    TZ_CHANGE_CHECK_TIME = (3, 5) # (hour, minute)

    LOGGER_NAME = "MIND"
    LOGGER_FILENAME = "MIND.log"

    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin"
    INVALID_USERNAMES = ("", "reminders", "api")
    USERNAME_CHARACTERS = 'abcedfghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.!@$'

    CONNECTION_ERROR_TIMEOUT = 120 # seconds

    APPRISE_TEST_TITLE = "MIND: Test title"
    APPRISE_TEST_BODY = "MIND: Test body"


# region Enums
class BaseEnum(Enum):
    def __eq__(self, other) -> bool:
        return self.value == other

    def __hash__(self) -> int:
        return id(self.value)


class StartType(BaseEnum):
    STARTUP = 130
    RESTART = 131
    RESTART_HOSTING_CHANGES = 132
    RESTART_DB_CHANGES = 133


class Interval(BaseEnum):
    "Time intervals where the value is in seconds"

    ONE_MINUTE = 60
    ONE_HOUR = ONE_MINUTE * 60
    ONE_DAY = ONE_HOUR * 24
    THIRTY_DAYS = ONE_DAY * 30


class InvalidUsernameReason(BaseEnum):
    ONLY_NUMBERS = "Username can not only be numbers"
    NOT_ALLOWED = "Username is not allowed"
    INVALID_CHARACTER = "Username contains an invalid character"


class SendResult(BaseEnum):
    SUCCESS = "Success"
    CONNECTION_ERROR = "Connection error"
    SYNTAX_INVALID_URL = "Syntax of URL invalid"
    REJECTED_URL = "Values in URL rejected by service (e.g. invalid API token)"


class ReminderType(BaseEnum):
    REMINDER = "Reminder"
    STATIC_REMINDER = "Static Reminder"
    TEMPLATE = "Template"


class RepeatQuantity(BaseEnum):
    YEARS = "years"
    MONTHS = "months"
    WEEKS = "weeks"
    DAYS = "days"
    HOURS = "hours"
    MINUTES = "minutes"


def sort_by_timeless_title(r: GeneralReminderData) -> Tuple[str, str, str]:
    return (r.title, r.text or '', r.color or '')


def sort_by_time(r: ReminderData) -> Tuple[int, str, str, str]:
    return (r.time, r.title, r.text or '', r.color or '')


def sort_by_timed_title(r: ReminderData) -> Tuple[str, int, str, str]:
    return (r.title, r.time, r.text or '', r.color or '')


def sort_by_id(r: GeneralReminderData) -> int:
    return r.id


class TimelessSortingMethod(BaseEnum):
    TITLE = sort_by_timeless_title, False
    TITLE_REVERSED = sort_by_timeless_title, True
    DATE_ADDED = sort_by_id, False
    DATE_ADDED_REVERSED = sort_by_id, True


class SortingMethod(BaseEnum):
    TIME = sort_by_time, False
    TIME_REVERSED = sort_by_time, True
    TITLE = sort_by_timed_title, False
    TITLE_REVERSED = sort_by_timed_title, True
    DATE_ADDED = sort_by_id, False
    DATE_ADDED_REVERSED = sort_by_id, True


class DataType(BaseEnum):
    STR = 'string'
    INT = 'number'
    FLOAT = 'decimal number'
    BOOL = 'bool'
    INT_ARRAY = 'list of numbers'
    STR_ARRAY = 'list of string'
    NA = 'N/A'


class DataSource(BaseEnum):
    DATA = 1
    VALUES = 2
    FILES = 3


# region TypedDicts
class ApiResponse(TypedDict):
    result: Any
    error: Union[str, None]
    code: int


class DatabaseBackupEntry(TypedDict):
    index: int
    creation_date: int
    filepath: str
    filename: str


# region Abstract Classes
class DBMigrator(ABC):
    start_version: int

    @abstractmethod
    def run(self) -> None:
        ...


class MindException(Exception, ABC):
    """An exception specific to MIND"""

    @property
    @abstractmethod
    def api_response(self) -> ApiResponse:
        ...


class StartTypeHandler(ABC):
    description: str
    """A short description of what the start type is for"""

    timeout: float
    """The amount of time in seconds before reverting"""

    restart_on_timeout: bool
    """"Whether the application should restart once the timeout is reached"""

    @abstractmethod
    def on_timeout(self) -> None:
        """
        Called when the timeout is reached. Generally reverts changes.
        """
        ...

    @abstractmethod
    def on_diffuse(self) -> None:
        """
        Called when the timer is diffused. Generally finalises changes.
        """
        ...


# region Dataclasses
@dataclass(frozen=True, order=True)
class NotificationServiceData:
    id: int
    title: str
    url: str

    def todict(self) -> Dict[str, Any]:
        return self.__dict__


@dataclass(frozen=True, order=True)
class UserData:
    id: int
    username: str
    admin: bool
    salt: bytes
    hash: bytes
    mfa_apprise_url: Union[str, None]

    def todict(self) -> Dict[str, Any]:
        return {
            k: v
            for k, v in self.__dict__.items()
            if k in ('id', 'username', 'admin', 'mfa_apprise_url')
        }


@dataclass(order=True)
class GeneralReminderData:
    id: int
    title: str
    text: Union[str, None]
    color: Union[str, None]
    notification_services: List[int]

    def todict(self) -> Dict[str, Any]:
        return self.__dict__


@dataclass(order=True)
class TemplateData(GeneralReminderData):
    ...


@dataclass(order=True)
class StaticReminderData(GeneralReminderData):
    ...


@dataclass(order=True)
class ReminderData(GeneralReminderData):
    time: int
    original_time: Union[int, None]
    repeat_quantity: Union[str, None]
    repeat_interval: Union[int, None]
    _weekdays: Union[str, None]
    cron_schedule: Union[str, None]
    enabled: bool

    def __post_init__(self) -> None:
        if self._weekdays is not None:
            self.weekdays: Union[List[WEEKDAY_NUMBER], None] = [
                cast(WEEKDAY_NUMBER, int(n))
                for n in self._weekdays.split(',')
                if n
            ]
        else:
            self.weekdays = None

    def todict(self) -> Dict[str, Any]:
        return {
            k: v
            for k, v in self.__dict__.items()
            if k != '_weekdays'
        }
