# -*- coding: utf-8 -*-

from typing import List, Union

from backend.base.custom_exceptions import (AccessUnauthorized,
                                            NewAccountsNotAllowed,
                                            OperationNotAllowed,
                                            UsernameInvalid, UsernameTaken,
                                            UserNotFound)
from backend.base.definitions import Constants, InvalidUsernameReason, UserData
from backend.base.helpers import generate_salt_hash, get_hash
from backend.base.logging import LOGGER
from backend.internals.db_models import UsersDB
from backend.internals.settings import Settings


def is_valid_username(username: str) -> Union[None, InvalidUsernameReason]:
    """Check if username is valid.

    Args:
        username (str): The username to check.

    Returns:
        Union[None, InvalidUsernameReason]: `None` if username is valid,
            `InvalidUsernameReason` if it is invalid.
    """
    if username in Constants.INVALID_USERNAMES:
        return InvalidUsernameReason.NOT_ALLOWED

    if username.isdigit():
        return InvalidUsernameReason.ONLY_NUMBERS

    if any(
        c not in Constants.USERNAME_CHARACTERS
        for c in username
    ):
        return InvalidUsernameReason.INVALID_CHARACTER

    return None


class User:
    def __init__(self, user_id: int) -> None:
        """Create an instance.

        Args:
            user_id (int): The ID of the user.

        Raises:
            UserNotFound: The user does not exist.
        """
        self.user_db = UsersDB()
        self.user_id = user_id

        if not self.user_db.exists(self.user_id):
            raise UserNotFound(None, user_id)

        return

    def get(self) -> UserData:
        """Get the info about the user.

        Returns:
            UserData: The info about the user.
        """
        return self.user_db.fetch(self.user_id)[0]

    def update_username(self, new_username: str) -> None:
        """Change the username of the account.

        Args:
            new_username (str): The new username.

        Raises:
            UsernameInvalid: The new username is not valid.
            UsernameTaken: The new username is already taken.
        """
        reason = is_valid_username(new_username)
        if reason is not None:
            raise UsernameInvalid(new_username, reason)

        if self.user_db.taken(new_username):
            raise UsernameTaken(new_username)

        user_data = self.get()

        self.user_db.update(
            self.user_id,
            new_username,
            user_data.hash,
            user_data.mfa_apprise_url
        )

        LOGGER.info(
            f"The user with ID {self.user_id} has a new username: {new_username}"
        )
        return

    def update_password(self, new_password: str) -> None:
        """Change the password of the account.

        Args:
            new_password (str): The new password.
        """
        user_data = self.get()

        hash_password = get_hash(user_data.salt, new_password)

        self.user_db.update(
            self.user_id,
            user_data.username,
            hash_password,
            user_data.mfa_apprise_url
        )

        LOGGER.info(
            f'The user with ID {self.user_id} changed their password'
        )
        return

    def update_mfa_apprise_url(
        self,
        new_mfa_apprise_url: Union[str, None]
    ) -> None:
        """Change the MFA Apprise URL of the account.

        Args:
            new_mfa_apprise_url (Union[str, None]): The new MFA Apprise URL.
        """
        user_data = self.get()

        self.user_db.update(
            self.user_id,
            user_data.username,
            user_data.hash,
            new_mfa_apprise_url
        )

        return

    def delete(self) -> None:
        """Delete the user. The instance should not be used after calling this
        method.

        Raises:
            OperationNotAllowed: The admin account cannot be deleted.
        """
        user_data = self.get()
        if user_data.admin:
            raise OperationNotAllowed(
                "The admin account cannot be deleted"
            )

        LOGGER.info(f'Deleting the user with ID {self.user_id}')

        self.user_db.delete(self.user_id)

        return


class Users:
    def __init__(self) -> None:
        self.user_db = UsersDB()
        return

    def get_all(self) -> List[UserData]:
        """Get all user info for the admin.

        Returns:
            List[UserData]: The info about all users.
        """
        return self.user_db.fetch()

    def get_one(self, user_id: int) -> User:
        """Get a user instance based on the ID.

        Args:
            user_id (int): The ID of the user.

        Returns:
            User: The user instance.
        """
        return User(user_id)

    def __contains__(self, username_or_id: Union[str, int]) -> bool:
        if isinstance(username_or_id, str):
            return self.username_taken(username_or_id)
        else:
            return self.id_taken(username_or_id)

    def username_taken(self, username: str) -> bool:
        """Check if a username is taken.

        Args:
            username (str): The username to check.

        Returns:
            bool: Whether the username is already taken.
        """
        return self.user_db.taken(username)

    def id_taken(self, user_id: int) -> bool:
        """Check if a user ID is taken.

        Args:
            user_id (int): The user ID to check.

        Returns:
            bool: Whether the user ID is already taken.
        """
        return self.user_db.exists(user_id)

    def login(
        self,
        username: str,
        password: str
    ) -> User:
        """Login into an user account.

        Args:
            username (str): The username of the user.
            password (str): The password of the user.

        Raises:
            UserNotFound: There is no user with the given username.
            AccessUnauthorized: The password is incorrect.

        Returns:
            User: The user that was logged into.
        """
        if not self.username_taken(username):
            raise UserNotFound(username, None)

        user_data = self.user_db.fetch(
            self.user_db.username_to_id(username)
        )[0]

        hash_password = get_hash(user_data.salt, password)
        # Comparing hashes, not password strings, so no need for
        # constant time comparison
        if not hash_password == user_data.hash:
            raise AccessUnauthorized

        return User(user_data.id)

    def add(
        self,
        username: str,
        password: str,
        force: bool = False,
        is_admin: bool = False
    ) -> int:
        """Add a user.

        Args:
            username (str): The username of the new user.

            password (str): The password of the new user.

            force (bool, optional): Skip check for whether new accounts are
                allowed.
                Defaults to False.

            is_admin (bool, optional): The account is the admin account.
                Defaults to False.

        Raises:
            UsernameInvalid: Username not allowed or contains invalid characters.
            UsernameTaken: Username is already taken; usernames must be unique.
            NewAccountsNotAllowed: In the admin panel, new accounts are set to be
                not allowed.

        Returns:
            int: The ID of the new user. User registered successfully.
        """
        LOGGER.info(f'Registering user with username {username}')

        if not force and not Settings().sv.allow_new_accounts:
            raise NewAccountsNotAllowed

        reason = is_valid_username(username)
        if reason is not None:
            raise UsernameInvalid(username, reason)

        if self.user_db.taken(username):
            raise UsernameTaken(username)

        if is_admin and self.user_db.admin_id() is not None:
            # Attempted to add admin account (only done internally),
            # but admin account already exists
            raise RuntimeError("Admin account already exists")

        # Generate salt and key exclusive for user
        salt, hashed_password = generate_salt_hash(password)

        # Add user to database
        user_id = self.user_db.add(
            username,
            salt,
            hashed_password,
            is_admin
        )

        LOGGER.debug(f'Newly registered user has id {user_id}')
        return user_id
