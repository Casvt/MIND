# -*- coding: utf-8 -*-

from typing import Any, Union

from backend.base.definitions import (ApiResponse, InvalidUsernameReason,
                                      MindException, SendResult)
from backend.base.logging import LOGGER


class LogUnauthMindException(MindException):
    """
    MindExceptions that inherit from this one will trigger a log of the
    requester's IP address once raised.
    """


# region REST responses
class NotFound(MindException):
    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 404,
            'error': self.__class__.__name__,
            'result': {}
        }


class BadRequest(MindException):
    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 400,
            'error': self.__class__.__name__,
            'result': {}
        }


class MethodNotAllowed(MindException):
    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 405,
            'error': self.__class__.__name__,
            'result': {}
        }


class InternalError(MindException):
    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 500,
            'error': self.__class__.__name__,
            'result': {}
        }


# region Input/Output
class KeyNotFound(MindException):
    "A key was not found in the input that is required to be given"

    def __init__(self, key: str) -> None:
        self.key = key
        LOGGER.warning(
            "This key was not found in the API request,"
            " eventhough it's required: %s",
            key
        )
        return

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 400,
            'error': self.__class__.__name__,
            'result': {
                'key': self.key
            }
        }


class InvalidKeyValue(MindException):
    "The value of a key is invalid"

    def __init__(self, key: str, value: Any) -> None:
        self.key = key
        self.value = value
        LOGGER.warning(
            "This key in the API request has an invalid value: "
            "%s = %s",
            key, value
        )

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 400,
            'error': self.__class__.__name__,
            'result': {
                'key': self.key,
                'value': self.value
            }
        }


# region Auth
class AccessUnauthorized(LogUnauthMindException):
    "The password given is not correct"

    def __init__(self) -> None:
        LOGGER.warning(
            "The password given is not correct"
        )
        return

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 401,
            'error': self.__class__.__name__,
            'result': {}
        }


class APIKeyInvalid(LogUnauthMindException):
    "The API key is not correct"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        return

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 401,
            'error': self.__class__.__name__,
            'result': {
                'api_key': self.api_key
            }
        }


class APIKeyExpired(LogUnauthMindException):
    "The API key has expired"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        return

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 401,
            'error': self.__class__.__name__,
            'result': {
                'api_key': self.api_key
            }
        }


# region Admin Operations
class OperationNotAllowed(MindException):
    "What was requested to be done is not allowed"

    def __init__(self, operation: str) -> None:
        LOGGER.warning(
            "Operation not allowed: %s",
            operation
        )

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 403,
            'error': self.__class__.__name__,
            'result': {}
        }


class NewAccountsNotAllowed(LogUnauthMindException):
    "It's not allowed to create a new account except for the admin"

    def __init__(self) -> None:
        LOGGER.warning(
            "The creation of a new account was attempted but it's disabled by the admin"
        )
        return

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 403,
            'error': self.__class__.__name__,
            'result': {}
        }


class InvalidDatabaseFile(MindException):
    "The uploaded database file is invalid or not supported"

    def __init__(self, filepath_db: str, reason: str) -> None:
        self.filepath_db = filepath_db
        self.reason = reason
        LOGGER.warning(
            "The given database file is invalid: %s (reason=%s)",
            filepath_db, reason
        )
        return

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 400,
            'error': self.__class__.__name__,
            'result': {
                'filepath_db': self.filepath_db,
                'reason': self.reason
            }
        }


class DatabaseFileNotFound(MindException):
    "The index of the database backup is invalid"

    def __init__(self, backup_index: int) -> None:
        self.backup_index = backup_index
        LOGGER.warning(
            "The given database backup index is invalid: %d",
            backup_index
        )
        return

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 400,
            'error': self.__class__.__name__,
            'result': {
                'index': self.backup_index
            }
        }


class LogFileNotFound(MindException):
    "The log file was not found"

    def __init__(self, log_file: str) -> None:
        self.log_file = log_file
        LOGGER.warning(
            "The log file was not found: %s",
            log_file
        )
        return

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 404,
            'error': self.__class__.__name__,
            'result': {
                'log_file': self.log_file
            }
        }


# region Users
class UsernameTaken(MindException):
    "The username is already taken"

    def __init__(self, username: str) -> None:
        self.username = username
        LOGGER.warning(
            "The username is already taken: %s",
            username
        )
        return

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 400,
            'error': self.__class__.__name__,
            'result': {
                'username': self.username
            }
        }


class UsernameInvalid(MindException):
    "The username contains invalid characters or is not allowed"

    def __init__(
        self,
        username: str,
        reason: InvalidUsernameReason
    ) -> None:
        self.username = username
        self.reason = reason
        LOGGER.warning(
            "The username '%s' is invalid for the following reason: %s",
            username, reason.value
        )
        return

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 400,
            'error': self.__class__.__name__,
            'result': {
                'username': self.username,
                'reason': self.reason.value
            }
        }


class UserNotFound(LogUnauthMindException):
    "The user requested can not be found"

    def __init__(
        self,
        username: Union[str, None],
        user_id: Union[int, None]
    ) -> None:
        self.username = username
        self.user_id = user_id
        if username:
            LOGGER.warning(
                "The user can not be found: %s",
                username
            )

        elif user_id:
            LOGGER.warning(
                "The user can not be found: ID %d",
                user_id
            )

        else:
            LOGGER.warning(
                "The user can not be found"
            )

        return

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 404,
            'error': self.__class__.__name__,
            'result': {
                'username': self.username,
                'user_id': self.user_id
            }
        }


# region Notification Services
class NotificationServiceNotFound(MindException):
    "The notification service was not found"

    def __init__(self, notification_service_id: int) -> None:
        self.notification_service_id = notification_service_id
        LOGGER.warning(
            "The notification service with the given ID cannot be found: %d",
            notification_service_id
        )
        return

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 404,
            'error': self.__class__.__name__,
            'result': {
                'notification_service_id': self.notification_service_id
            }
        }


class NotificationServiceInUse(MindException):
    """
    The notification service is wished to be deleted
    but a reminder is still using it
    """

    def __init__(
        self,
        notification_service_id: int,
        reminder_type: str
    ) -> None:
        self.notification_service_id = notification_service_id
        self.reminder_type = reminder_type
        LOGGER.warning(
            "The notification service with ID %d is wished to be deleted "
            "but a reminder of type %s is still using it",
            notification_service_id,
            reminder_type
        )
        return

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 404,
            'error': self.__class__.__name__,
            'result': {
                'notification_service_id': self.notification_service_id,
                'reminder_type': self.reminder_type
            }
        }


class URLInvalid(MindException):
    "The Apprise URL is invalid"

    def __init__(self, url: str, reason: SendResult) -> None:
        self.url = url
        self.reason = reason
        LOGGER.warning(
            "The Apprise URL given is invalid: %s (reason=%s)",
            url, reason.value
        )
        return

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 400,
            'error': self.__class__.__name__,
            'result': {
                'url': self.url,
                'reason': self.reason.value
            }
        }


# region Templates
class TemplateNotFound(MindException):
    "The template was not found"

    def __init__(self, template_id: int) -> None:
        self.template_id = template_id
        LOGGER.warning(
            "The template with the given ID cannot be found: %d",
            template_id
        )
        return

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 404,
            'error': self.__class__.__name__,
            'result': {
                'template_id': self.template_id
            }
        }


# region Reminders
class ReminderNotFound(MindException):
    "The reminder was not found"

    def __init__(self, reminder_id: int) -> None:
        self.reminder_id = reminder_id
        LOGGER.warning(
            "The reminder with the given ID cannot be found: %d",
            reminder_id
        )
        return

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 404,
            'error': self.__class__.__name__,
            'result': {
                'reminder_id': self.reminder_id
            }
        }


class InvalidTime(MindException):
    "The time given is in the past"

    def __init__(self, time: int) -> None:
        self.time = time
        LOGGER.warning(
            "The given time is invalid: %d",
            time
        )
        return

    @property
    def api_response(self) -> ApiResponse:
        return {
            'code': 400,
            'error': self.__class__.__name__,
            'result': {
                'time': self.time
            }
        }
