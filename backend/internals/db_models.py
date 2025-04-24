# -*- coding: utf-8 -*-

from typing import List, Union

from backend.base.definitions import (NotificationServiceData, ReminderData,
                                      ReminderType, StaticReminderData,
                                      TemplateData, UserData)
from backend.base.helpers import first_of_column
from backend.internals.db import REMINDER_TO_KEY, get_db


class NotificationServicesDB:
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        return

    def exists(self, notification_service_id: int) -> bool:
        return get_db().execute("""
            SELECT 1
            FROM notification_services
            WHERE id = :id
                AND user_id = :user_id
            LIMIT 1;
            """,
            {
                'user_id': self.user_id,
                'id': notification_service_id
            }
        ).fetchone() is not None

    def fetch(
        self,
        notification_service_id: Union[int, None] = None
    ) -> List[NotificationServiceData]:
        id_filter = ""
        if notification_service_id:
            id_filter = "AND id = :ns_id"

        result = get_db().execute(f"""
            SELECT
                id, title, url
            FROM notification_services
            WHERE user_id = :user_id
                {id_filter}
            ORDER BY title, id;
            """,
            {
                "user_id": self.user_id,
                "ns_id": notification_service_id
            }
        ).fetchalldict()

        return [
            NotificationServiceData(**entry)
            for entry in result
        ]

    def add(
        self,
        title: str,
        url: str
    ) -> int:
        new_id = get_db().execute("""
            INSERT INTO notification_services(user_id, title, url)
            VALUES (?, ?, ?)
            """,
            (self.user_id, title, url)
        ).lastrowid
        return new_id

    def update(
        self,
        notification_service_id: int,
        title: str,
        url: str
    ) -> None:
        get_db().execute("""
            UPDATE notification_services
            SET title = :title, url = :url
            WHERE id = :ns_id;
            """,
            {
                "title": title,
                "url": url,
                "ns_id": notification_service_id
            }
        )
        return

    def delete(
        self,
        notification_service_id: int
    ) -> None:
        get_db().execute(
            "DELETE FROM notification_services WHERE id = ?;",
            (notification_service_id,)
        )
        return


class ReminderServicesDB:
    def __init__(self, reminder_type: ReminderType) -> None:
        self.key = REMINDER_TO_KEY[reminder_type]
        return

    def reminder_to_ns(
        self,
        reminder_id: int
    ) -> List[int]:
        """Get the ID's of the notification services that are linked to the given
        reminder, static reminder or template.

        Args:
            reminder_id (int): The ID of the reminder, static reminder or template.

        Returns:
            List[int]: A list of the notification service ID's that are linked to
            the given reminder, static reminder or template.
        """
        result = first_of_column(get_db().execute(
            f"""
            SELECT notification_service_id
            FROM reminder_services
            WHERE {self.key} = ?;
            """,
            (reminder_id,)
        ))

        return result

    def update_ns_bindings(
        self,
        reminder_id: int,
        notification_services: List[int]
    ) -> None:
        """Update the bindings of a reminder, static reminder or template to
        notification services.

        Args:
            reminder_id (int): The ID of the reminder, static reminder or template.

            notification_services (List[int]): The new list of notification services
            that should be linked to the reminder, static reminder or template.
        """
        cursor = get_db()
        cursor.connection.isolation_level = None
        cursor.execute("BEGIN TRANSACTION;")

        cursor.execute(
            f"""
            DELETE FROM reminder_services
            WHERE {self.key} = ?;
            """,
            (reminder_id,)
        )
        cursor.executemany(
            f"""
            INSERT INTO reminder_services(
                {self.key},
                notification_service_id
            )
            VALUES (?, ?);
            """,
            ((reminder_id, ns_id) for ns_id in notification_services)
        )

        cursor.execute("COMMIT;")
        cursor.connection.isolation_level = ""
        return

    def uses_ns(
        self,
        notification_service_id: int
    ) -> List[int]:
        """Get the ID's of the reminders (of given type) that use the given
        notification service.

        Args:
            notification_service_id (int): The ID of the notification service to
            check for.

        Returns:
            List[int]: The ID's of the reminders (only of the given type) that
            use the notification service.
        """
        return first_of_column(get_db().execute(
            f"""
            SELECT {self.key}
            FROM reminder_services
            WHERE notification_service_id = ?
                AND {self.key} IS NOT NULL
            LIMIT 1;
            """,
            (notification_service_id,)
        ))


class UsersDB:
    def exists(self, user_id: int) -> bool:
        return get_db().execute("""
            SELECT 1
            FROM users
            WHERE id = ?
            LIMIT 1;
            """,
            (user_id,)
        ).fetchone() is not None

    def taken(self, username: str) -> bool:
        return get_db().execute("""
            SELECT 1
            FROM users
            WHERE username = ?
            LIMIT 1;
            """,
            (username,)
        ).fetchone() is not None

    def username_to_id(self, username: str) -> int:
        return get_db().execute("""
            SELECT id
            FROM users
            WHERE username = ?
            LIMIT 1;
            """,
            (username,)
        ).fetchone()[0]

    def fetch(
        self,
        user_id: Union[int, None] = None
    ) -> List[UserData]:
        id_filter = ""
        if user_id:
            id_filter = "WHERE id = :id"

        result = get_db().execute(f"""
            SELECT
                id, username, admin, salt, hash
            FROM users
            {id_filter}
            ORDER BY username, id;
            """,
            {
                "id": user_id
            }
        ).fetchalldict()

        return [
            UserData(**entry)
            for entry in result
        ]

    def add(
        self,
        username: str,
        salt: bytes,
        hash: bytes,
        admin: bool
    ) -> int:
        user_id = get_db().execute(
            """
			INSERT INTO users(username, salt, hash, admin)
			VALUES (?, ?, ?, ?);
			""",
            (username, salt, hash, admin)
        ).lastrowid
        return user_id

    def update(
        self,
        user_id: int,
        username: str,
        hash: bytes
    ) -> None:
        get_db().execute("""
            UPDATE users
            SET username = :username, hash = :hash
            WHERE id = :user_id;
            """,
            {
                "username": username,
                "hash": hash,
                "user_id": user_id
            }
        )
        return

    def delete(
        self,
        user_id: int
    ) -> None:
        get_db().executescript(f"""
            BEGIN TRANSACTION;

            DELETE FROM reminders WHERE user_id = {user_id};
            DELETE FROM templates WHERE user_id = {user_id};
            DELETE FROM static_reminders WHERE user_id = {user_id};
            DELETE FROM notification_services WHERE user_id = {user_id};
            DELETE FROM users WHERE id = {user_id};

            COMMIT;
        """)
        return


class TemplatesDB:
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        self.rms_db = ReminderServicesDB(ReminderType.TEMPLATE)
        return

    def exists(self, template_id: int) -> bool:
        return get_db().execute(
            "SELECT 1 FROM templates WHERE id = ? AND user_id = ? LIMIT 1;",
            (template_id, self.user_id)
        ).fetchone() is not None

    def fetch(
        self,
        template_id: Union[int, None] = None
    ) -> List[TemplateData]:
        id_filter = ""
        if template_id:
            id_filter = "AND id = :t_id"

        result = get_db().execute(f"""
            SELECT
                id, title, text, color
            FROM templates
            WHERE user_id = :user_id
                {id_filter}
            ORDER BY title, id;
            """,
            {
                "user_id": self.user_id,
                "t_id": template_id
            }
        ).fetchalldict()

        for r in result:
            r['notification_services'] = self.rms_db.reminder_to_ns(r['id'])

        return [
            TemplateData(**entry)
            for entry in result
        ]

    def add(
        self,
        title: str,
        text: Union[str, None],
        color: Union[str, None],
        notification_services: List[int]
    ) -> int:
        new_id = get_db().execute("""
            INSERT INTO templates(user_id, title, text, color)
            VALUES (?, ?, ?, ?);
            """,
            (self.user_id, title, text, color)
        ).lastrowid

        self.rms_db.update_ns_bindings(
            new_id, notification_services
        )

        return new_id

    def update(
        self,
        template_id: int,
        title: str,
        text: Union[str, None],
        color: Union[str, None],
        notification_services: List[int]
    ) -> None:
        get_db().execute("""
            UPDATE templates
            SET
                title = :title,
                text = :text,
                color = :color
            WHERE id = :t_id;
            """,
            {
                "title": title,
                "text": text,
                "color": color,
                "t_id": template_id
            }
        )

        self.rms_db.update_ns_bindings(
            template_id,
            notification_services
        )

        return

    def delete(
        self,
        template_id: int
    ) -> None:
        get_db().execute(
            "DELETE FROM templates WHERE id = ?;",
            (template_id,)
        )
        return


class StaticRemindersDB:
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        self.rms_db = ReminderServicesDB(ReminderType.STATIC_REMINDER)
        return

    def exists(self, reminder_id: int) -> bool:
        return get_db().execute("""
            SELECT 1
            FROM static_reminders
            WHERE id = ?
                AND user_id = ?
            LIMIT 1;
            """,
            (reminder_id, self.user_id)
        ).fetchone() is not None

    def fetch(
        self,
        reminder_id: Union[int, None] = None
    ) -> List[StaticReminderData]:
        id_filter = ""
        if reminder_id:
            id_filter = "AND id = :r_id"

        result = get_db().execute(f"""
            SELECT
                id, title, text, color
            FROM static_reminders
            WHERE user_id = :user_id
                {id_filter}
            ORDER BY title, id;
            """,
            {
                "user_id": self.user_id,
                "r_id": reminder_id
            }
        ).fetchalldict()

        for r in result:
            r['notification_services'] = self.rms_db.reminder_to_ns(r['id'])

        return [
            StaticReminderData(**entry)
            for entry in result
        ]

    def add(
        self,
        title: str,
        text: Union[str, None],
        color: Union[str, None],
        notification_services: List[int]
    ) -> int:
        new_id = get_db().execute("""
            INSERT INTO static_reminders(user_id, title, text, color)
            VALUES (?, ?, ?, ?);
            """,
            (self.user_id, title, text, color)
        ).lastrowid

        self.rms_db.update_ns_bindings(
            new_id, notification_services
        )

        return new_id

    def update(
        self,
        reminder_id: int,
        title: str,
        text: Union[str, None],
        color: Union[str, None],
        notification_services: List[int]
    ) -> None:
        get_db().execute("""
            UPDATE static_reminders
            SET
                title = :title,
                text = :text,
                color = :color
            WHERE id = :r_id;
            """,
            {
                "title": title,
                "text": text,
                "color": color,
                "r_id": reminder_id
            }
        )

        self.rms_db.update_ns_bindings(
            reminder_id,
            notification_services
        )

        return

    def delete(
        self,
        reminder_id: int
    ) -> None:
        get_db().execute(
            "DELETE FROM static_reminders WHERE id = ?;",
            (reminder_id,)
        )
        return


class RemindersDB:
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        self.rms_db = ReminderServicesDB(ReminderType.REMINDER)
        return

    def exists(self, reminder_id: int) -> bool:
        return get_db().execute("""
            SELECT 1
            FROM reminders
            WHERE id = ?
                AND user_id = ?
            LIMIT 1;
            """,
            (reminder_id, self.user_id)
        ).fetchone() is not None

    def fetch(
        self,
        reminder_id: Union[int, None] = None
    ) -> List[ReminderData]:
        id_filter = ""
        if reminder_id:
            id_filter = "AND id = :r_id"

        result = get_db().execute(f"""
            SELECT
                id, title, text, color,
                time, original_time,
                repeat_quantity, repeat_interval,
                weekdays AS _weekdays, enabled
            FROM reminders
            WHERE user_id = :user_id
                {id_filter};
            """,
            {
                "user_id": self.user_id,
                "r_id": reminder_id
            }
        ).fetchalldict()

        for r in result:
            r['notification_services'] = self.rms_db.reminder_to_ns(r['id'])

        return [
            ReminderData(**entry)
            for entry in result
        ]

    def add(
        self,
        title: str,
        text: Union[str, None],
        time: int,
        repeat_quantity: Union[str, None],
        repeat_interval: Union[int, None],
        weekdays: Union[str, None],
        original_time: Union[int, None],
        color: Union[str, None],
        notification_services: List[int],
        enabled: bool
    ) -> int:
        new_id = get_db().execute("""
            INSERT INTO reminders(
                user_id,
                title, text,
                time,
                repeat_quantity, repeat_interval,
                weekdays,
                original_time,
                color,
                enabled
            )
            VALUES (
                :user_id,
                :title, :text,
                :time,
                :rq, :ri,
                :wd,
                :ot,
                :color,
                :enabled
            );
            """,
            {
                "user_id": self.user_id,
                "title": title,
                "text": text,
                "time": time,
                "rq": repeat_quantity,
                "ri": repeat_interval,
                "wd": weekdays,
                "ot": original_time,
                "color": color,
                "enabled": enabled
            }
        ).lastrowid

        self.rms_db.update_ns_bindings(
            new_id, notification_services
        )

        return new_id

    def update(
        self,
        reminder_id: int,
        title: str,
        text: Union[str, None],
        time: int,
        repeat_quantity: Union[str, None],
        repeat_interval: Union[int, None],
        weekdays: Union[str, None],
        original_time: Union[int, None],
        color: Union[str, None],
        notification_services: List[int],
        enabled: bool
    ) -> None:
        get_db().execute("""
            UPDATE reminders
            SET
                title = :title,
                text = :text,
                time = :time,
                repeat_quantity = :rq,
                repeat_interval = :ri,
                weekdays = :wd,
                original_time = :ot,
                color = :color,
                enabled = :enabled
            WHERE id = :r_id;
            """,
            {
                "title": title,
                "text": text,
                "time": time,
                "rq": repeat_quantity,
                "ri": repeat_interval,
                "wd": weekdays,
                "ot": original_time,
                "color": color,
                "enabled": enabled,
                "r_id": reminder_id
            }
        )

        self.rms_db.update_ns_bindings(
            reminder_id,
            notification_services
        )

        return

    def delete(
        self,
        reminder_id: int
    ) -> None:
        get_db().execute(
            "DELETE FROM reminders WHERE id = ?;",
            (reminder_id,)
        )
        return


class UserlessRemindersDB:
    def __init__(self) -> None:
        self.rms_db = ReminderServicesDB(ReminderType.REMINDER)
        return

    def exists(self, reminder_id: int) -> bool:
        return get_db().execute("""
            SELECT 1
            FROM reminders
            WHERE id = ?
            LIMIT 1;
            """,
            (reminder_id,)
        ).fetchone() is not None

    def reminder_id_to_user_id(self, reminder_id: int) -> int:
        return get_db().execute(
            """
            SELECT user_id
            FROM reminders
            WHERE id = ?
            LIMIT 1;
            """,
            (reminder_id,)
        ).exists() or -1

    def get_soonest_time(self) -> Union[int, None]:
        """Get the earliest time a reminder goes off that is enabled.

        Returns:
            Union[int, None]: The time, or None if there are no reminders.
        """
        return get_db().execute(
            "SELECT MIN(time) FROM reminders WHERE enabled = 1;"
        ).exists()

    def fetch(
        self,
        time: Union[int, None] = None
    ) -> List[ReminderData]:
        time_filter = ""
        if time:
            time_filter = "WHERE time = :time"

        result = get_db().execute(f"""
            SELECT
                id,
                title, text, color,
                time, original_time,
                repeat_quantity, repeat_interval,
                weekdays AS _weekdays, enabled
            FROM reminders
            {time_filter};
            """,
            {
                "time": time
            }
        ).fetchalldict()

        for r in result:
            r['notification_services'] = self.rms_db.reminder_to_ns(r['id'])

        return [
            ReminderData(**entry)
            for entry in result
        ]

    def add(
        self,
        user_id: int,
        title: str,
        text: Union[str, None],
        time: int,
        repeat_quantity: Union[str, None],
        repeat_interval: Union[int, None],
        weekdays: Union[str, None],
        original_time: Union[int, None],
        color: Union[str, None],
        notification_services: List[int],
        enabled: bool
    ) -> int:
        new_id = get_db().execute("""
            INSERT INTO reminders(
                user_id,
                title, text,
                time,
                repeat_quantity, repeat_interval,
                weekdays,
                original_time,
                color,
                enabled
            )
            VALUES (
                :user_id,
                :title, :text,
                :time,
                :rq, :ri,
                :wd,
                :ot,
                :color,
                :enabled
            );
            """,
            {
                "user_id": user_id,
                "title": title,
                "text": text,
                "time": time,
                "rq": repeat_quantity,
                "ri": repeat_interval,
                "wd": weekdays,
                "ot": original_time,
                "color": color,
                "enabled": enabled
            }
        ).lastrowid

        self.rms_db.update_ns_bindings(
            new_id, notification_services
        )

        return new_id

    def update(
        self,
        reminder_id: int,
        time: int
    ) -> None:
        get_db().execute("""
            UPDATE reminders
            SET time = :time
            WHERE id = :r_id;
            """,
            {
                "time": time,
                "r_id": reminder_id
            }
        )

        return

    def delete(
        self,
        reminder_id: int
    ) -> None:
        get_db().execute(
            "DELETE FROM reminders WHERE id = ?;",
            (reminder_id,)
        )
        return
