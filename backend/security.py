#-*- coding: utf-8 -*-

from base64 import urlsafe_b64encode
from hashlib import pbkdf2_hmac
from secrets import token_bytes
from typing import Tuple

def get_hash(salt: bytes, data: str) -> bytes:
	"""Hash a string using the supplied salt

	Args:
		salt (bytes): The salt to use when hashing
		data (str): The data to hash

	Returns:
		bytes: The b64 encoded hash of the supplied string
	"""
	return urlsafe_b64encode(
		pbkdf2_hmac('sha256', data.encode(), salt, 100_000)
	)

def generate_salt_hash(password: str) -> Tuple[bytes, bytes]:
	"""Generate a salt and get the hash of the password

	Args:
		password (str): The password to generate for

	Returns:
		Tuple[bytes, bytes]: The salt (1) and hashed_password (2)
	"""
	# Hash the password
	salt = token_bytes()
	hashed_password = get_hash(salt, password)
	del password

	return salt, hashed_password
