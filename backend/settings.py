#-*- coding: utf-8 -*-

import logging
from backend.custom_exceptions import InvalidKeyValue, KeyNotFound
from backend.db import __DATABASE_VERSION__, get_db

default_settings = {
	'allow_new_accounts': True,
	'database_version': __DATABASE_VERSION__
}

def _format_setting(key: str, value):
	"""Turn python value in to database value

	Args:
		key (str): The key of the value
		value (Any): The value itself

	Raises:
		InvalidKeyValue: The value is not valid

	Returns:
		Any: The converted value
	"""
	if key == 'database_version':
		try:
			value = int(value)
		except ValueError:
			raise InvalidKeyValue(key, value)

	elif key == 'allow_new_accounts':
		if not isinstance(value, bool):
			raise InvalidKeyValue(key, value)
		value = int(value)
	return value

def _reverse_format_setting(key: str, value):
	"""Turn database value in to python value

	Args:
		key (str): The key of the value
		value (Any): The value itself

	Returns:
		Any: The converted value
	"""
	if key == 'allow_new_accounts':
		value = value == 1
	return value

def get_setting(key: str):
	"""Get a value from the config

	Args:
		key (str): The key of which to get the value

	Raises:
		KeyNotFound: Key is not in config

	Returns:
		Any: The value of the key
	"""
	result = get_db().execute(
		"SELECT value FROM config WHERE key = ? LIMIT 1;",
		(key,)
	).fetchone()
	if result is None:
		raise KeyNotFound(key)

	result = _reverse_format_setting(key, result[0])

	return result

def get_admin_settings() -> dict:
	"""Get all admin settings

	Returns:
		dict: The admin settings
	"""
	return dict((
		(key, _reverse_format_setting(key, value))
		for (key, value) in get_db().execute("""
			SELECT key, value
			FROM config
			WHERE key = 'allow_new_accounts';
			"""
		)
	))

def set_setting(key: str, value) -> None:
	"""Set a value in the config

	Args:
		key (str): The key for which to set the value
		value (Any): The value to give to the key

	Raises:
		KeyNotFound: The key is not in the config
		InvalidKeyValue: The value is not allowed for the key
	"""
	if not key in (*default_settings, 'database_version'):
		raise KeyNotFound(key)

	value = _format_setting(key, value)

	get_db().execute(
		"UPDATE config SET value = ? WHERE key = ?;",
		(value, key)
	)
	return
