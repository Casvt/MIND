# -*- coding: utf-8 -*-

import logging
import logging.config
from io import StringIO
from os.path import exists, isdir, join
from typing import Any, Union

from backend.base.definitions import Constants


class UpToInfoFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= logging.INFO


class ErrorColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> Any:
        result = super().format(record)
        return f'\033[1;31:40m{result}\033[0m'


LOGGER = logging.getLogger(Constants.LOGGER_NAME)
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[%(asctime)s][%(levelname)s] %(message)s",
            "datefmt": "%H:%M:%S"
        },
        "simple_red": {
            "()": ErrorColorFormatter,
            "format": "[%(asctime)s][%(levelname)s] %(message)s",
            "datefmt": "%H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s | %(threadName)s | %(filename)sL%(lineno)s | %(levelname)s | %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        }
    },
    "filters": {
        "up_to_info": {
            "()": UpToInfoFilter
        },
    },
    "handlers": {
        "console_error": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "simple_red",
            "stream": "ext://sys.stderr"
        },
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "filters": ["up_to_info"],
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "",
            "maxBytes": 1_000_000,
            "backupCount": 1
        }
    },
    "loggers": {
        Constants.LOGGER_NAME: {}
    },
    "root": {
        "level": "INFO",
        "handlers": [
            "console",
            "console_error",
            "file"
        ]
    }
}


def setup_logging(log_folder: Union[str, None]) -> None:
    """Setup the basic config of the logging module.

    Args:
        log_folder (Union[str, None]): The folder to put the log file in.
            If `None`, the log file will be in the same folder as the
            application folder.

    Raises:
        ValueError: The given log folder is not a folder.
    """
    from backend.base.helpers import create_folder, folder_path

    if log_folder:
        if exists(log_folder) and not isdir(log_folder):
            raise ValueError("Logging folder is not a folder")

        create_folder(log_folder)

    if log_folder is None:
        LOGGING_CONFIG["handlers"]["file"]["filename"] = folder_path(
            Constants.LOGGER_FILENAME
        )
    else:
        LOGGING_CONFIG["handlers"]["file"]["filename"] = join(
            log_folder,
            Constants.LOGGER_FILENAME
        )

    logging.config.dictConfig(LOGGING_CONFIG)

    # Log uncaught exceptions using the logger instead of printing the stderr
    # Logger goes to stderr anyway, so still visible in console but also logs
    # to file, so that downloaded log file also contains any errors.
    import sys
    import threading
    from traceback import format_exception

    def log_uncaught_exceptions(e_type, value, tb):
        LOGGER.error(
            "UNCAUGHT EXCEPTION:\n" +
            ''.join(format_exception(e_type, value, tb))
        )
        return

    def log_uncaught_threading_exceptions(args):
        LOGGER.exception(
            f"UNCAUGHT EXCEPTION IN THREAD: {args.exc_value}"
        )
        return

    sys.excepthook = log_uncaught_exceptions
    threading.excepthook = log_uncaught_threading_exceptions

    return


def get_log_filepath() -> str:
    """Get the filepath to the logging file.

    Returns:
        str: The filepath.
    """
    return LOGGING_CONFIG["handlers"]["file"]["filename"]


def get_log_file_contents() -> StringIO:
    """Get all the logs from the log file(s).

    Raises:
        LogFileNotFound: The log file does not exist.

    Returns:
        StringIO: The contents of the log file(s).
    """
    from backend.base.custom_exceptions import LogFileNotFound

    file = get_log_filepath()
    if not exists(file):
        raise LogFileNotFound(file)

    sio = StringIO()
    for ext in ('.1', ''):
        lf = file + ext
        if not exists(lf):
            continue
        with open(lf, 'r') as f:
            sio.writelines(f)

    return sio


def set_log_level(
    level: Union[int, str],
) -> None:
    """Change the logging level.

    Args:
        level (Union[int, str]): The level to set the logging to.
            Should be a logging level, like `logging.INFO` or `"DEBUG"`.
    """
    if isinstance(level, str):
        level = logging._nameToLevel[level.upper()]

    root_logger = logging.getLogger()
    if root_logger.level == level:
        return

    LOGGER.debug(f'Setting logging level: {level}')
    root_logger.setLevel(level)

    return
