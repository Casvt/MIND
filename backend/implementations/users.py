# -*- coding: utf-8 -*-

from typing import List, Union

from backend.base.custom_exceptions import (AccessUnauthorized,
                                            NewAccountsNotAllowed,
                                            OperationNotAllowed,
                                            UsernameInvalid, UsernameTaken,
                                            UserNotFound)
from backend.base.definitions import Constants, InvalidUsernameReason, UserData
from backend.base.helpers import Singleton, generate_salt_hash, get_hash
from backend.base.logging import LOGGER
from backend.internals.db_models import UsersDB
from backend.internals.settings import Settings


def is_valid_username(username: str) -> None:
    """Check if username is valid.

    Args:
        username (str): The username to check.

    Raises:
        UsernameInvalid: The username is not valid.
    """
    if username in Constants.INVALID_USERNAMES:
        raise UsernameInvalid(username, InvalidUsernameReason.NOT_ALLOWED)

    if username.isdigit():
        raise UsernameInvalid(username, InvalidUsernameReason.ONLY_NUMBERS)

    if any(
        c not in Constants.USERNAME_CHARACTERS
        for c in username
    ):
        raise UsernameInvalid(
            username,
            InvalidUsernameReason.INVALID_CHARACTER
        )

    return


class User:
    def __init__(self, id: int) -> None:
        """Create a representation of a user.

        Args:
            id (int): The ID of the user.

        Raises:
            UserNotFound: The user does not exist.
        """
        self.user_db = UsersDB()
        self.user_id = id

        if not self.user_db.exists(self.user_id):
            raise UserNotFound(None, id)

        return

    def get(self) -> UserData:
        """Get the info about the user.

        Returns:
            UserData: The info about the user.
        """
        return self.user_db.fetch(self.user_id)[0]

    def update(
        self,
        new_username: Union[str, None],
        new_password: Union[str, None]
    ) -> None:
        """Change the username and/or password of the account.

        Args:
            new_username (Union[str, None]): The new username, or None if it
            should not be changed.
            new_password (Union[str, None]): The new password, or None if it
            should not be changed.

        Raises:
            OperationNotAllowed: The user is an admin and is trying to change
            the username.
            UsernameInvalid: The new username is not valid.
            UsernameTaken: The new username is already taken.
        """
        user_data = self.get()

        if new_username is not None:
            if user_data.admin:
                raise OperationNotAllowed(
                    "Changing the username of an admin account"
                )

            is_valid_username(new_username)

            if self.user_db.taken(new_username):
                raise UsernameTaken(new_username)

            self.user_db.update(
                self.user_id,
                new_username,
                user_data.hash
            )

            LOGGER.info(
                f"The user with ID {self.user_id} has a changed username: {new_username}"
            )

        user_data = self.get()

        if new_password is not None:
            hash_password = get_hash(user_data.salt, new_password)

            self.user_db.update(
                self.user_id,
                user_data.username,
                hash_password
            )

            LOGGER.info(
                f'The user with ID {self.user_id} changed their password'
            )

        return

    def delete(self) -> None:
        """Delete the user.

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


class Users(metaclass=Singleton):
    def __init__(self) -> None:
        self.user_db = UsersDB()
        return

    def get_all(self) -> List[UserData]:
        """Get all user info for the admin

        Returns:
            List[UserData]: The info about all users
        """
        result = self.user_db.fetch()
        return result

    def get_one(self, id: int) -> User:
        """Get a user instance based on the ID.

        Args:
            id (int): The ID of the user.

        Returns:
            User: The user instance.
        """
        return User(id)

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
            bool: True if the username is taken, False otherwise.
        """
        return self.user_db.taken(username)

    def id_taken(self, id: int) -> bool:
        """Check if a user ID is taken.

        Args:
            id (int): The user ID to check.

        Returns:
            bool: True if the user ID is taken, False otherwise.
        """
        return self.user_db.exists(id)

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
        if not self.user_db.taken(username):
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

        if not force and not Settings().get_settings().allow_new_accounts:
            raise NewAccountsNotAllowed

        is_valid_username(username)

        if self.user_db.taken(username):
            raise UsernameTaken(username)

        if is_admin:
            if self.user_db.taken(Constants.ADMIN_USERNAME):
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
