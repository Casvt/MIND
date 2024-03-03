#-*- coding: utf-8 -*-

"""
Getting and setting settings
"""

from json import dumps, loads
from typing import Any

from backend.custom_exceptions import InvalidKeyValue, KeyNotFound
from backend.db import __DATABASE_VERSION__, get_db
from backend.helpers import folder_path

default_settings = {
	'allow_new_accounts': True,
	'login_time': 3600,
	'login_time_reset': True,
	'database_version': __DATABASE_VERSION__,
	'host': '0.0.0.0',
	'port': 8080,
	'url_prefix': ''
}

def _format_setting(key: str, value):
	"""Turn python value in to database value.

	Args:
		key (str): The key of the value.
		value (Any): The value itself.

	Raises:
		InvalidKeyValue: The value is not valid.

	Returns:
		Any: The converted value.
	"""
	if key == 'database_version':
		try:
			value = int(value)
		except ValueError:
			raise InvalidKeyValue(key, value)

	elif key in ('allow_new_accounts', 'login_time_reset'):
		if not isinstance(value, bool):
			raise InvalidKeyValue(key, value)
		value = int(value)

	elif key == 'login_time':
		if not isinstance(value, int) or not 60 <= value <= 2592000:
			raise InvalidKeyValue(key, value)

	elif key == 'host':
		if not isinstance(value, str):
			raise InvalidKeyValue(key, value)

	elif key == 'port':
		if not isinstance(value, int) or not 1 <= value <= 65535:
			raise InvalidKeyValue(key, value)

	elif key == 'url_prefix':
		if not isinstance(value, str):
			raise InvalidKeyValue(key, value)

		if value:
			value = '/' + value.strip('/')

	return value

def _reverse_format_setting(key: str, value: Any) -> Any:
	"""Turn database value in to python value.

	Args:
		key (str): The key of the value.
		value (Any): The value itself.

	Returns:
		Any: The converted value.
	"""
	if key in ('allow_new_accounts', 'login_time_reset'):
		value = value == 1
	return value

def get_setting(key: str) -> Any:
	"""Get a value from the config.

	Args:
		key (str): The key of which to get the value.

	Raises:
		KeyNotFound: Key is not in config.

	Returns:
		Any: The value of the key.
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
		for key, value in get_db().execute("""
			SELECT key, value
			FROM config
			WHERE
				key = 'allow_new_accounts'
				OR key = 'login_time'
				OR key = 'login_time_reset'
				OR key = 'host'
				OR key = 'port'
				OR key = 'url_prefix';
			"""
		)
	))

def set_setting(key: str, value: Any) -> None:
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

	if key == 'url_prefix':
		update_manifest(value)

	return

def update_manifest(url_base: str) -> None:
	"""Update the url's in the manifest file.
	Needs to happen when url base changes.

	Args:
		url_base (str): The url base to use in the file.
	"""
	with open(folder_path('frontend', 'static', 'json', 'manifest.json'), 'r+') as f:
		manifest = loads(f.read())
		manifest['start_url'] = url_base + '/'
		manifest['icons'][0]['src'] = f'{url_base}/static/img/favicon.svg'
		f.seek(0)
		f.write(dumps(manifest, indent=4))
	return

def backup_hosting_settings() -> None:
	"""Copy current hosting settings to backup values.
	"""	
	cursor = get_db()
	hosting_settings = dict(cursor.execute("""
		SELECT key, value
		FROM config
		WHERE key = 'host'
			OR key = 'port'
			OR key = 'url_prefix'
		LIMIT 3;
		"""
	))
	hosting_settings = {f'{k}_backup': v for k, v in hosting_settings.items()}

	cursor.executemany("""
		INSERT INTO config(key, value)
		VALUES (?, ?)
		ON CONFLICT(key) DO
		UPDATE
		SET value = ?;
		""",
		((k, v, v) for k, v in hosting_settings.items())
	)

	return

def restore_hosting_settings() -> None:
	"""Copy the hosting settings from the backup over to the main keys.
	"""
	cursor = get_db()
	hosting_settings = dict(cursor.execute("""
		SELECT key, value
		FROM config
		WHERE key = 'host_backup'
			OR key = 'port_backup'
			OR key = 'url_prefix_backup'
		LIMIT 3;
		"""
	))
	if len(hosting_settings) < 3:
		return

	hosting_settings = {k.split('_backup')[0]: v for k, v in hosting_settings.items()}

	cursor.executemany(
		"UPDATE config SET value = ? WHERE key = ?",
		((v, k) for k, v in hosting_settings.items())
	)
	
	return
