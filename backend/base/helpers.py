# -*- coding: utf-8 -*-

"""
General "helper" functions and classes
"""

from base64 import urlsafe_b64encode
from datetime import datetime
from hashlib import pbkdf2_hmac
from logging import WARNING
from os import makedirs, scandir, symlink
from os.path import abspath, dirname, exists, isfile, join, splitext
from secrets import token_bytes
from shutil import copy2, move
from sys import base_exec_prefix, executable, platform, version_info
from typing import Callable, Iterable, List, Sequence, Set, Tuple, Union, cast

from apprise import Apprise, LogCapture
from cron_converter import Cron
from dateutil.relativedelta import relativedelta

from backend.base.definitions import (WEEKDAY_NUMBER, GeneralReminderData,
                                      RepeatQuantity, SendResult, T, U)
from backend.base.logging import LOGGER


# region Python
def get_python_version() -> str:
    """Get the Python version as a string. E.g. `"3.8.10.final.0"`.

    Returns:
        str: The Python version.
    """
    return ".".join(
        str(i) for i in list(version_info)
    )


def check_min_python_version(
    min_major: int,
    min_minor: int,
    min_micro: int
) -> bool:
    """Check whether the version of Python that is used is equal or higher than
    the version given. Will log a critical error if not.

    ```
    # On Python3.9.1
    >>> check_min_python_version(3, 8, 2)
    True
    >>> check_min_python_version(3, 10, 0)
    False
    ```

    Args:
        min_major (int): The minimum major version.
        min_minor (int): The minimum minor version.
        min_micro (int): The miminum micro version.

    Returns:
        bool: Whether it's equal or higher than the version given or below it.
    """
    min_version = (
        min_major,
        min_minor,
        min_micro
    )
    current_version = (
        version_info.major,
        version_info.minor,
        version_info.micro
    )

    if current_version < min_version:
        LOGGER.critical(
            "The minimum python version required is python"
            + ".".join(map(str, min_version))
            + " (currently " + ".".join(map(str, current_version)) + ")."
        )
        return False

    return True


def get_python_exe() -> Union[str, None]:
    """Get the absolute filepath to the python executable.

    Returns:
        Union[str, None]: The python executable path, or `None` if not found.
    """
    if platform.startswith('darwin'):
        filepath = None
        bundle_path = join(
            base_exec_prefix,
            "Resources",
            "Python.app",
            "Contents",
            "MacOS",
            "Python"
        )
        if exists(bundle_path):
            from tempfile import mkdtemp
            filepath = join(mkdtemp(), "python")
            symlink(bundle_path, filepath)
    else:
        filepath = executable or None

    if filepath and not isfile(filepath):
        filepath = None

    return filepath


# region Generic
def first_of_subarrays(
    subarrays: Iterable[Sequence[T]]
) -> List[T]:
    """Get the first element of each sub-array.

    ```
    >>> first_of_subarrays([[1, 2], [3, 4]])
    [1, 3]
    ```

    Args:
        subarrays (Iterable[Sequence[T]]): List of sub-arrays.

    Returns:
        List[T]: List with first value of each sub-array.
    """
    return [e[0] for e in subarrays]


def when_not_none(
    value: Union[T, None],
    to_run: Callable[[T], U]
) -> Union[U, None]:
    """Run `to_run` with argument `value` iff `value is not None`. Else return
    `None`.

    Args:
        value (Union[T, None]): The value to check.
        to_run (Callable[[T], U]): The function to run.

    Returns:
        Union[U, None]: Either the return value of `to_run`, or `None`.
    """
    if value is None:
        return None
    else:
        return to_run(value)


def search_filter(query: str, result: GeneralReminderData) -> bool:
    """Filter library results based on a query.

    Args:
        query (str): The query to filter with.
        result (GeneralReminderData): The library result to check.

    Returns:
        bool: Whether the result passes the filter.
    """
    query = query.lower().replace(' ', '')
    return (
        query.lower().replace(' ', '')
        in
        (result.title + (result.text or '')).lower().replace(' ', '')
    )


# region Security
def get_hash(salt: bytes, data: str) -> bytes:
    """Hash a string using the supplied salt.

    Args:
        salt (bytes): The salt to use when hashing.
        data (str): The data to hash.

    Returns:
        bytes: The b64 encoded hash of the supplied string.
    """
    return urlsafe_b64encode(
        pbkdf2_hmac('sha256', data.encode(), salt, 100_000)
    )


def generate_salt_hash(password: str) -> Tuple[bytes, bytes]:
    """Generate a salt and get the hash of the password.

    Args:
        password (str): The password to generate for.

    Returns:
        Tuple[bytes, bytes]: The salt (1) and hashed_password (2).
    """
    salt = token_bytes()
    hashed_password = get_hash(salt, password)
    return salt, hashed_password


# region Apprise
def send_apprise_notification(
    urls: List[str],
    title: str,
    text: Union[str, None] = None
) -> SendResult:
    """Send a notification to all Apprise URLs given.

    Args:
        urls (List[str]): The Apprise URLs to send the notification to.

        title (str): The title of the notification.

        text (Union[str, None], optional): The optional body of the
            notification.
            Defaults to None.

    Returns:
        SendResult: Whether Apprise was successful.
    """
    a = Apprise()

    for url in urls:
        if not a.add(url):
            return SendResult.SYNTAX_INVALID_URL

    with LogCapture(level=WARNING) as log:
        result = a.notify(
            title=title,
            body=text or '\u200B'
        )
        if not result:
            if "socket exception" in log.getvalue(): # type: ignore
                return SendResult.CONNECTION_ERROR
            else:
                return SendResult.REJECTED_URL

        return SendResult.SUCCESS


# region Time
def next_selected_day(
    allowed_weekdays: List[WEEKDAY_NUMBER],
    current_weekday: WEEKDAY_NUMBER
) -> WEEKDAY_NUMBER:
    """Find the next allowed day in the week.

    ```
    >>> next_selected_day([0, 4, 6], 4)
    6
    >>> next_selected_day([0, 4, 6], 6)
    0
    ```

    Args:
        allowed_weekdays (List[WEEKDAY_NUMBER]): The days of the week that are
            allowed. Monday is 0, Sunday is 6.
        current_weekday (WEEKDAY_NUMBER): The current weekday.

    Returns:
        WEEKDAY_NUMBER: The next allowed weekday.
    """
    for d in allowed_weekdays:
        if current_weekday < d:
            return d
    return allowed_weekdays[0]


def find_next_time(
    original_time: int,
    repeat_quantity: Union[RepeatQuantity, None],
    repeat_interval: Union[int, None],
    weekdays: Union[List[WEEKDAY_NUMBER], None],
    cron_schedule: Union[str, None]
) -> int:
    """Calculate the next timestamp based on original time and repeat/interval
    values.

    Args:
        original_time (int): The original time of the repeating timestamp.

        repeat_quantity (Union[RepeatQuantity, None]): If set, what the quantity
            is of the time interval.

        repeat_interval (Union[int, None]): If set, the value of the time
            interval.

        weekdays (Union[List[WEEKDAY_NUMBER], None]): If set, on which days the
            timestamp can be. Monday is 0, Sunday is 6.

        cron_schedule (Union[str, None]): If set, the cron schedule to follow.

    Returns:
        int: The next timestamp in the future.
    """
    if weekdays is not None:
        weekdays.sort()

    current_time = datetime.fromtimestamp(datetime.utcnow().timestamp())
    original_datetime = datetime.fromtimestamp(original_time)
    new_time = datetime.fromtimestamp(original_time)

    if cron_schedule is not None:
        cron_instance = Cron(cron_schedule)
        schedule = cron_instance.schedule(current_time)
        new_time = schedule.next()
        while new_time <= current_time:
            new_time = schedule.next()

    elif (
        repeat_quantity is not None
        and repeat_interval is not None
    ):
        # Add the interval to the original time until we are in the future.
        # We need to multiply the interval and add it to the original time
        # instead of just adding the interval once each time to the original
        # time, because otherwise date jumping could happen. Say original time
        # is a leap day with an interval of 1 year. Then next date would be the
        # day before leap day, as leap day doesn't exist in the next year. But
        # if we then keep adding 1 year to this time, we would keep getting the
        # day before leap day, a year later. So we need to multiply the interval
        # and add the whole interval to the original time in one go. This way
        # after four years we will get the leap day again.
        interval = relativedelta(
            **{repeat_quantity.value: repeat_interval} # type: ignore
        )
        multiplier = 1
        while new_time <= current_time:
            new_time = original_datetime + (interval * multiplier)
            multiplier += 1

    elif weekdays is not None:
        if (
            current_time.weekday() in weekdays
            and current_time.time() < original_datetime.time()
        ):
            # Next reminder is later today, so target weekday is current weekday
            weekday = current_time.weekday()

        else:
            # Next reminder is not today or earlier today, so target weekday
            # is next selected one
            weekday = next_selected_day(
                weekdays,
                cast(WEEKDAY_NUMBER, current_time.weekday())
            )

        new_time = current_time + relativedelta(
            # Move to upcoming weekday (possibly today)
            weekday=weekday,
            # Also move current time to set time
            hour=original_datetime.hour,
            minute=original_datetime.minute,
            second=original_datetime.second
        )

    result = int(new_time.timestamp())
    LOGGER.debug(
        f'{original_datetime=}, {current_time=} ' +
        f'and interval of {repeat_interval} {repeat_quantity} ' +
        f'and weekdays {weekdays} ' +
        f'leads to {result}'
    )
    return result


# region Files
def folder_path(*folders: str) -> str:
    """Turn filepaths relative to the project folder into absolute paths.

    Returns:
        str: The absolute filepath.
    """
    return join(
        dirname(dirname(dirname(abspath(__file__)))),
        *folders
    )


def list_files(folder: str, ext: Iterable[str] = []) -> List[str]:
    """List all files in a folder recursively with absolute paths. Hidden files
    (files starting with `.`) are ignored.

    Args:
        folder (str): The base folder to search through.

        ext (Iterable[str], optional): File extensions to only include.
            Dot-prefix not necessary. Let empty to allow all extensions.
            Defaults to [].

    Returns:
        List[str]: The paths of the files in the folder.
    """
    files: List[str] = []

    def _list_files(folder: str, ext: Set[str] = set()):
        """Internal function to add all files in a folder to the files list.

        Args:
            folder (str): The base folder to search through.
            ext (Set[str], optional): A set of lowercase, dot-prefixed,
            extensions to filter for or empty for no filter. Defaults to set().
        """
        for f in scandir(folder):
            if f.is_dir():
                _list_files(f.path, ext)

            elif (
                f.is_file()
                and not f.name.startswith('.')
                and (
                    not ext
                    or (splitext(f.name)[1].lower() in ext)
                )
            ):
                files.append(f.path)

    ext = {'.' + e.lower().lstrip('.') for e in ext}
    _list_files(folder, ext)
    return files


def create_folder(folder: str) -> None:
    """Create a folder. Also creates any parent folders if they don't exist
    already. Allows folder to already exist.

    Args:
        folder (str): The path to the folder to create.
    """
    makedirs(folder, exist_ok=True)
    return


def copy(
    src: str,
    dst: str,
    *,
    follow_symlinks: bool = True
) -> str:
    """Copy a file or folder.

    Args:
        src (str): The source file or folder.
        dst (str): The destination of the copy.
        follow_symlinks (bool, optional): Whether to follow symlinks.
            Defaults to True.

    Returns:
        str: The destination.
    """
    try:
        return copy2(src, dst, follow_symlinks=follow_symlinks)

    except PermissionError as pe:
        if pe.errno == 1:
            # NFS file system doesn't allow/support chmod.
            # This is done after the file is already copied. So just accept that
            # it isn't possible to change the permissions. Continue like normal.
            return dst

        raise

    except OSError as oe:
        if oe.errno == 524:
            # NFS file system doesn't allow/support setting extended attributes.
            # This is done after the file is already copied. So just accept that
            # it isn't possible to set them. Continue like normal.
            return dst

        raise


def rename_file(
    before: str,
    after: str
) -> None:
    """Rename a file, taking care of new folder locations and
    the possible complications with files on OS'es.

    Args:
        before (str): The current filepath of the file.
        after (str): The new desired filepath of the file.
    """
    create_folder(dirname(after))

    move(before, after, copy_function=copy)

    return


# region Classes
class Singleton(type):
    """
    Make each initialisation of a class return the same instance by setting
    this as the metaclass. Works across threads, but not spawned subprocesses.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        c_term = cls.__module__ + '.' + cls.__name__

        if c_term not in cls._instances:
            cls._instances[c_term] = super().__call__(*args, **kwargs)

        return cls._instances[c_term]
