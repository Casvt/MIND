#-*- coding: utf-8 -*-

import logging
from backend.custom_exceptions import (AccessUnauthorized, UsernameInvalid,
                                       UsernameTaken, UserNotFound)
from backend.db import get_db
from backend.notification_service import NotificationServices
from backend.reminders import Reminders
from backend.security import generate_salt_hash, get_hash
from backend.static_reminders import StaticReminders
from backend.templates import Templates

ONEPASS_USERNAME_CHARACTERS = 'abcedfghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.!@$'
ONEPASS_INVALID_USERNAMES = ['reminders', 'api']

class User:
	"""Represents an user account
	"""	
	def __init__(self, username: str, password: str):
		# Fetch data of user to check if user exists and to check if password is correct
		result = get_db(dict).execute(
			"SELECT id, salt, hash, admin FROM users WHERE username = ? LIMIT 1;", 
			(username,)
		).fetchone()
		if not result:
			raise UserNotFound
		self.username = username
		self.salt = result['salt']
		self.user_id = result['id']
		self.admin = result['admin'] == 1

		# Check password
		hash_password = get_hash(result['salt'], password)
		if not hash_password == result['hash']:
			raise AccessUnauthorized
			
	@property
	def reminders(self) -> Reminders:
		"""Get access to the reminders of the user account

		Returns:
			Reminders: Reminders instance that can be used to access the reminders of the user account
		"""		
		if not hasattr(self, 'reminders_instance'):
			self.reminders_instance = Reminders(self.user_id)
		return self.reminders_instance

	@property
	def notification_services(self) -> NotificationServices:
		"""Get access to the notification services of the user account

		Returns:
			NotificationServices: NotificationServices instance that can be used to access the notification services of the user account
		"""		
		if not hasattr(self, 'notification_services_instance'):
			self.notification_services_instance = NotificationServices(self.user_id)
		return self.notification_services_instance

	@property
	def templates(self) -> Templates:
		"""Get access to the templates of the user account

		Returns:
			Templates: Templates instance that can be used to access the templates of the user account
		"""	
		if not hasattr(self, 'templates_instance'):
			self.templates_instance = Templates(self.user_id)
		return self.templates_instance

	@property
	def static_reminders(self) -> StaticReminders:
		"""Get access to the static reminders of the user account

		Returns:
			StaticReminders: StaticReminders instance that can be used to access the static reminders of the user account
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
		logging.info(f'Deleting the user {self.username} ({self.user_id})')
		
		cursor = get_db()
		cursor.execute("DELETE FROM reminders WHERE user_id = ?", (self.user_id,))
		cursor.execute("DELETE FROM templates WHERE user_id = ?", (self.user_id,))
		cursor.execute("DELETE FROM static_reminders WHERE user_id = ?", (self.user_id,))
		cursor.execute("DELETE FROM notification_services WHERE user_id = ?", (self.user_id,))
		cursor.execute("DELETE FROM users WHERE id = ?", (self.user_id,))
		return

def _check_username(username: str) -> None:
	"""Check if username is valid

	Args:
		username (str): The username to check

	Raises:
		UsernameInvalid: The username is not valid
	"""
	logging.debug(f'Checking the username {username}')
	if username in ONEPASS_INVALID_USERNAMES or username.isdigit():
		raise UsernameInvalid
	if list(filter(lambda c: not c in ONEPASS_USERNAME_CHARACTERS, username)):
		raise UsernameInvalid
	return

def register_user(username: str, password: str) -> int:
	"""Add a user

	Args:
		username (str): The username of the new user
		password (str): The password of the new user

	Raises:
		UsernameInvalid: Username not allowed or contains invalid characters
		UsernameTaken: Username is already taken; usernames must be unique

	Returns:
		user_id (int): The id of the new user. User registered successful
	"""
	logging.info(f'Registering user with username {username}')
	
	# Check if username is valid
	_check_username(username)

	cursor = get_db()

	# Check if username isn't already taken
	if cursor.execute(
		"SELECT 1 FROM users WHERE username = ? LIMIT 1", (username,)
	).fetchone():
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
