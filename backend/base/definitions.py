# -*- coding: utf-8 -*-

"""
Definitions of basic types, abstract classes, enums, etc.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import (TYPE_CHECKING, Any, Dict, List, Literal,
                    Tuple, Type, TypedDict, TypeVar, Union, cast)

if TYPE_CHECKING:
    from backend.implementations.users import User


# region Types
T = TypeVar('T')
U = TypeVar('U')
WEEKDAY_NUMBER = Literal[0, 1, 2, 3, 4, 5, 6]
BaseSerialisable = Union[
    int, float, bool, str, None
]
Serialisable = Union[
    List[Union[
        BaseSerialisable,
        List[BaseSerialisable],
        Dict[str, BaseSerialisable]
    ]],
    Dict[str, Union[
        BaseSerialisable,
        List[BaseSerialisable],
        Dict[str, BaseSerialisable]
    ]],
]


# region Constants
class Constants:
    SUB_PROCESS_TIMEOUT = 20.0 # seconds

    HOSTING_THREADS = 10
    HOSTING_REVERT_TIME = 60.0 # seconds

    DB_FOLDER = ("db",)
    DB_NAME = "MIND.db"
    DB_ORIGINAL_NAME = 'MIND_original.db'
    DB_TIMEOUT = 10.0 # seconds
    DB_REVERT_TIME = 60.0 # seconds

    LOGGER_NAME = "MIND"
    LOGGER_FILENAME = "MIND.log"

    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin"
    INVALID_USERNAMES = ("reminders", "api")
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


# region Dataclasses
@dataclass
class ApiKeyEntry:
    exp: int
    user_data: User


def _return_exceptions() -> List[Type[MindException]]:
    from backend.base.custom_exceptions import InvalidKeyValue, KeyNotFound
    return [KeyNotFound, InvalidKeyValue]


@dataclass
class InputVariable(ABC):
    value: Any
    name: str
    description: str
    required: bool = True
    default: Any = None
    data_type: List[DataType] = field(default_factory=lambda: [DataType.STR])
    source: DataSource = DataSource.DATA
    related_exceptions: List[Type[MindException]] = field(
        default_factory=_return_exceptions
    )

    def validate(self) -> bool:
        return isinstance(self.value, str) and bool(self.value)


@dataclass(frozen=True)
class Method:
    description: str = ''
    vars: List[Type[InputVariable]] = field(default_factory=list)


@dataclass(frozen=True)
class Methods:
    get: Union[Method, None] = None
    post: Union[Method, None] = None
    put: Union[Method, None] = None
    delete: Union[Method, None] = None

    def __getitem__(self, key: str) -> Union[Method, None]:
        return getattr(self, key.lower())

    def used_methods(self) -> List[str]:
        result = []
        for method in ('get', 'post', 'put', 'delete'):
            if getattr(self, method) is not None:
                result.append(method)
        return result


@dataclass(frozen=True)
class ApiDocEntry:
    endpoint: str
    description: str
    methods: Methods
    requires_auth: bool


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

    def todict(self) -> Dict[str, Any]:
        return {
            k: v
            for k, v in self.__dict__.items()
            if k in ('id', 'username', 'admin')
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
