#-*- coding: utf-8 -*-

import logging
from typing import List

from backend.custom_exceptions import (AccessUnauthorized,
                                       NewAccountsNotAllowed, UsernameInvalid,
                                       UsernameTaken, UserNotFound)
from backend.db import get_db
from backend.notification_service import NotificationServices
from backend.reminders import Reminders
from backend.security import generate_salt_hash, get_hash
from backend.settings import get_setting
from backend.static_reminders import StaticReminders
from backend.templates import Templates

ONEPASS_USERNAME_CHARACTERS = 'abcedfghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.!@$'
ONEPASS_INVALID_USERNAMES = ['reminders', 'api']

class User:
	"""Represents an user account
	"""

	def __init__(self, id: int) -> None:
		result = get_db(dict).execute(
			"SELECT username, admin, salt FROM users WHERE id = ? LIMIT 1;", 
			(id,)
		).fetchone()
		if not result:
			raise UserNotFound

		self.username: str = result['username']
		self.user_id = id
		self.admin: bool = result['admin'] == 1
		self.salt: bytes = result['salt']
		return

	@property
	def reminders(self) -> Reminders:
		"""Get access to the reminders of the user account

		Returns:
			Reminders: Reminders instance that can be used to access the 
			reminders of the user account
		"""		
		if not hasattr(self, 'reminders_instance'):
			self.reminders_instance = Reminders(self.user_id)
		return self.reminders_instance

	@property
	def notification_services(self) -> NotificationServices:
		"""Get access to the notification services of the user account

		Returns:
			NotificationServices: NotificationServices instance that can be used 
			to access the notification services of the user account
		"""		
		if not hasattr(self, 'notification_services_instance'):
			self.notification_services_instance = NotificationServices(self.user_id)
		return self.notification_services_instance

	@property
	def templates(self) -> Templates:
		"""Get access to the templates of the user account

		Returns:
			Templates: Templates instance that can be used to access the 
			templates of the user account
		"""	
		if not hasattr(self, 'templates_instance'):
			self.templates_instance = Templates(self.user_id)
		return self.templates_instance

	@property
	def static_reminders(self) -> StaticReminders:
		"""Get access to the static reminders of the user account

		Returns:
			StaticReminders: StaticReminders instance that can be used to 
			access the static reminders of the user account
		"""	
		if not hasattr(self, 'static_reminders_instance'):
			self.static_reminders_instance = StaticReminders(self.user_id)
		return self.static_reminders_instance

	def edit_password(self, new_password: str) -> None:
		"""Change the password of the account

		Args:
			new_password (str): The new password
		"""		
		# Encrypt raw key with new password
		hash_password = get_hash(self.salt, new_password)

		# Update database
		get_db().execute(
			"UPDATE users SET hash = ? WHERE id = ?",
			(hash_password, self.user_id)
		)
		logging.info(f'The user {self.username} ({self.user_id}) changed their password')
		return

	def delete(self) -> None:
		"""Delete the user account
		"""
		if self.username == 'admin':
			raise UserNotFound

		logging.info(f'Deleting the user {self.username} ({self.user_id})')
		
		cursor = get_db()
		cursor.execute(
			"DELETE FROM reminders WHERE user_id = ?", 
			(self.user_id,)
		)
		cursor.execute(
			"DELETE FROM templates WHERE user_id = ?",
			(self.user_id,)
		)
		cursor.execute(
			"DELETE FROM static_reminders WHERE user_id = ?",
			(self.user_id,)
		)
		cursor.execute(
			"DELETE FROM notification_services WHERE user_id = ?",
			(self.user_id,)
		)
		cursor.execute(
			"DELETE FROM users WHERE id = ?",
			(self.user_id,)
		)
		return

class Users:
	def _check_username(self, username: str) -> None:
		"""Check if username is valid

		Args:
			username (str): The username to check

		Raises:
			UsernameInvalid: The username is not valid
		"""
		logging.debug(f'Checking the username {username}')
		if username in ONEPASS_INVALID_USERNAMES or username.isdigit():
			raise UsernameInvalid(username)
		if list(filter(lambda c: not c in ONEPASS_USERNAME_CHARACTERS, username)):
			raise UsernameInvalid(username)
		return

	def __contains__(self, username: str) -> bool:
		result = get_db().execute(
			"SELECT 1 FROM users WHERE username = ? LIMIT 1;",
			(username,)
		).fetchone()
		return result is not None

	def add(self, username: str, password: str, from_admin: bool=False) -> int:
		"""Add a user

		Args:
			username (str): The username of the new user
			password (str): The password of the new user
			from_admin (bool, optional): Skip check if new accounts are allowed.
				Defaults to False.

		Raises:
			UsernameInvalid: Username not allowed or contains invalid characters
			UsernameTaken: Username is already taken; usernames must be unique
			NewAccountsNotAllowed: In the admin panel, new accounts are set to be
			not allowed.

		Returns:
			int: The id of the new user. User registered successful
		"""
		logging.info(f'Registering user with username {username}')
		
		if not from_admin and not get_setting('allow_new_accounts'):
			raise NewAccountsNotAllowed
		
		# Check if username is valid
		self._check_username(username)

		cursor = get_db()

		# Check if username isn't already taken
		if username in self:
			raise UsernameTaken

		# Generate salt and key exclusive for user
		salt, hashed_password = generate_salt_hash(password)
		del password

		# Add user to userlist
		user_id = cursor.execute(
			"""
			INSERT INTO users(username, salt, hash)
			VALUES (?,?,?);
			""",
			(username, salt, hashed_password)
		).lastrowid

		logging.debug(f'Newly registered user has id {user_id}')
		return user_id

	def get_all(self) -> List[dict]:
		"""Get all user info for the admin

		Returns:
			List[dict]: The info about all users
		"""
		result = [
			dict(u)
			for u in get_db(dict).execute(
				"SELECT id, username, admin FROM users ORDER BY username;"
			)
		]
		return result

	def login(self, username: str, password: str) -> User:
		result = get_db(dict).execute(
			"SELECT id, salt, hash FROM users WHERE username = ? LIMIT 1;", 
			(username,)
		).fetchone()
		if not result:
			raise UserNotFound

		hash_password = get_hash(result['salt'], password)
		if not hash_password == result['hash']:
			raise AccessUnauthorized

		return User(result['id'])

	def get_one(self, id: int) -> User:
		return User(id)
