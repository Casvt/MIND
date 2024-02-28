#-*- coding: utf-8 -*-

"""
General functions
"""

import logging
from enum import Enum
from os.path import abspath, dirname, join
from sys import version_info
from typing import Any, Callable, TypeVar, Union

T = TypeVar('T')
U = TypeVar('U')

def folder_path(*folders) -> str:
	"""Turn filepaths relative to the project folder into absolute paths

	Returns:
		str: The absolute filepath
	"""
	return join(dirname(dirname(abspath(__file__))), *folders)


def check_python_version() -> bool:
	"""Check if the python version that is used is a minimum version.

	Returns:
		bool: Whether or not the python version is version 3.8 or above or not.
	"""
	if not (version_info.major == 3 and version_info.minor >= 8):
		logging.critical(
			'The minimum python version required is python3.8 ' + 
			'(currently ' + version_info.major + '.' + version_info.minor + '.' + version_info.micro + ').'
		)
		return False
	return True


def search_filter(query: str, result: dict) -> bool:
	"""Filter library results based on a query.

	Args:
		query (str): The query to filter with.
		result (dict): The library result to check.

	Returns:
		bool: Whether or not the result passes the filter.
	"""
	query = query.lower()
	return (
		query in result["title"].lower()
		or query in result["text"].lower()
	)


def when_not_none(value: T, to_run: Callable[[T], U]) -> Union[U, None]:
	"""Run `to_run` with argument `value` iff `value is not None`. Else return
	`None`.

	Args:
		value (T): The value to check.
		to_run (Callable[[T], U]): The function to run.

	Returns:
		Union[U, None]: Either the return value of `to_run`, or `None`.
	"""
	if value is None:
		return None
	else:
		return to_run(value)


class Singleton(type):
	_instances = {}
	def __call__(cls, *args, **kwargs):
		c = str(cls)
		if c not in cls._instances:
			cls._instances[c] = super().__call__(*args, **kwargs)

		return cls._instances[c]


class BaseEnum(Enum):
	def __eq__(self, other) -> bool:
		return self.value == other


class TimelessSortingMethod(BaseEnum):
	TITLE = (lambda r: (r['title'], r['text'], r['color']), False)
	TITLE_REVERSED = (lambda r: (r['title'], r['text'], r['color']), True)
	DATE_ADDED = (lambda r: r['id'], False)
	DATE_ADDED_REVERSED = (lambda r: r['id'], True)


class SortingMethod(BaseEnum):
	TIME = (lambda r: (r['time'], r['title'], r['text'], r['color']), False)
	TIME_REVERSED = (lambda r: (r['time'], r['title'], r['text'], r['color']), True)
	TITLE = (lambda r: (r['title'], r['time'], r['text'], r['color']), False)
	TITLE_REVERSED = (lambda r: (r['title'], r['time'], r['text'], r['color']), True)
	DATE_ADDED = (lambda r: r['id'], False)
	DATE_ADDED_REVERSED = (lambda r: r['id'], True)


class RepeatQuantity(BaseEnum):
	YEARS = "years"
	MONTHS = "months"
	WEEKS = "weeks"
	DAYS = "days"
	HOURS = "hours"
	MINUTES = "minutes"

class RestartVars(BaseEnum):
	DB_IMPORT = "db_import"
