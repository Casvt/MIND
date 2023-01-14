#-*- coding: utf-8 -*-

from sqlite3 import Connection, Row
from threading import current_thread
from typing import Union

from flask import g

class Singleton(type):
	_instances = {}
	def __call__(cls, *args, **kwargs):
		i = f'{cls}{current_thread()}'
		if i not in cls._instances:
			cls._instances[i] = super(Singleton, cls).__call__(*args, **kwargs)

		return cls._instances[i]

class DBConnection(Connection, metaclass=Singleton):
	file = ''
	
	def __init__(self, timeout: float) -> None:
		super().__init__(self.file, timeout=timeout)
		super().cursor().execute("PRAGMA foreign_keys = ON;")
		return

def get_db(output_type: Union[dict, tuple]=tuple):
	"""Get a database cursor instance. Coupled to Flask's g.

	Args:
		output_type (Union[dict, tuple], optional): The type of output: a tuple or dictionary with the row values. Defaults to tuple.

	Returns:
		Cursor: The Cursor instance to use
	"""	
	try:
			cursor = g.cursor
	except AttributeError:
			db = DBConnection(timeout=20.0)
			cursor = g.cursor = db.cursor()

	if output_type is dict:
			cursor.row_factory = Row
	else:
			cursor.row_factory = None

	return g.cursor

def close_db(e=None) -> None:
	"""Savely closes the database connection
	"""	
	try:
		cursor = g.cursor
		db = cursor.connection
		cursor.close()
		delattr(g, 'cursor')
		db.commit()
	except AttributeError:
		pass
	return

def setup_db() -> None:
	"""Setup the database
	"""
	cursor = get_db()

	cursor.executescript("""
		CREATE TABLE IF NOT EXISTS users(
			id INTEGER PRIMARY KEY,
			username VARCHAR(255) UNIQUE NOT NULL,
			salt VARCHAR(40) NOT NULL,
			hash VARCHAR(100) NOT NULL
		);
		CREATE TABLE IF NOT EXISTS notification_services(
			id INTEGER PRIMARY KEY,
			user_id INTEGER NOT NULL,
			title VARCHAR(255),
			url TEXT,
			
			FOREIGN KEY (user_id) REFERENCES users(id)
		);
		CREATE TABLE IF NOT EXISTS reminders(
			id INTEGER PRIMARY KEY,
			user_id INTEGER NOT NULL,
			title VARCHAR(255) NOT NULL,
			text TEXT,
			time INTEGER NOT NULL,
			notification_service INTEGER NOT NULL,
			
			FOREIGN KEY (user_id) REFERENCES users(id),
			FOREIGN KEY (notification_service) REFERENCES notification_services(id)
		);
	""")

	return
