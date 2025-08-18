# -*- coding: utf-8 -*-

from dataclasses import asdict
from typing import List, Union

from backend.base.custom_exceptions import ReminderNotFound
from backend.base.definitions import (SendResult, StaticReminderData,
                                      TimelessSortingMethod)
from backend.base.helpers import search_filter, send_apprise_notification
from backend.base.logging import LOGGER
from backend.implementations.notification_services import NotificationService
from backend.internals.db_models import StaticRemindersDB


class StaticReminder:
    def __init__(self, user_id: int, reminder_id: int) -> None:
        """Represent a static reminder.

        Args:
            user_id (int): The ID of the user.
            reminder_id (int): The ID of the reminder.

        Raises:
            ReminderNotFound: Reminder with given ID does not exist or is not
            owned by user.
        """
        self.user_id = user_id
        self.id = reminder_id

        self.reminder_db = StaticRemindersDB(self.user_id)

        if not self.reminder_db.exists(self.id):
            raise ReminderNotFound(reminder_id)
        return

    def get(self) -> StaticReminderData:
        """Get info about the static reminder.

        Returns:
            StaticReminderData: The info about the static reminder.
        """
        return self.reminder_db.fetch(self.id)[0]

    def trigger_reminder(self) -> SendResult:
        """Send the reminder.

        Returns:
            SendResult: The result of the sending process.
        """
        LOGGER.info(f'Triggering static reminder {self.id}')

        reminder_data = self.get()

        return send_apprise_notification(
            [
                NotificationService(self.user_id, ns_id).get().url
                for ns_id in reminder_data.notification_services
            ],
            reminder_data.title,
            reminder_data.text
        )

    def update(
        self,
        title: Union[str, None] = None,
        notification_services: Union[List[int], None] = None,
        text: Union[str, None] = None,
        color: Union[str, None] = None
    ) -> StaticReminderData:
        """Edit the static reminder.

        Args:
            title (Union[str, None], optional): The new title of the entry.
                Defaults to None.

            notification_services (Union[List[int], None], optional): The new
            id's of the notification services to use to send the reminder.
                Defaults to None.

            text (Union[str, None], optional): The new body of the reminder.
                Defaults to None.

            color (Union[str, None], optional): The new hex code of the color
            of the reminder, which is shown in the web-ui.
                Defaults to None.

        Raises:
            NotificationServiceNotFound: One of the notification services was
            not found.

        Returns:
            StaticReminderData: The new static reminder info.
        """
        LOGGER.info(
            f'Updating static reminder {self.id}: '
            + f'{title=}, {notification_services=}, {text=}, {color=}'
        )

        if notification_services:
            # Check whether all notification services exist
            for ns in notification_services:
                NotificationService(self.user_id, ns)

        # Get current data and update it with new values
        data = asdict(self.get())

        new_values = {
            'title': title,
            'text': text,
            'color': color,
            'notification_services': notification_services
        }
        for k, v in new_values.items():
            if k in ('color',) or v is not None:
                data[k] = v

        self.reminder_db.update(
            self.id,
            data['title'],
            data['text'],
            data['color'],
            data['notification_services']
        )

        return self.get()

    def delete(self) -> None:
        "Delete the static reminder"
        LOGGER.info(f'Deleting static reminder {self.id}')
        self.reminder_db.delete(self.id)
        return


class StaticReminders:
    def __init__(self, user_id: int) -> None:
        """Create an instance.

        Args:
            user_id (int): The ID of the user.
        """
        self.user_id = user_id
        self.reminder_db = StaticRemindersDB(self.user_id)
        return

    def fetchall(
        self,
        sort_by: TimelessSortingMethod = TimelessSortingMethod.TITLE
    ) -> List[StaticReminderData]:
        """Get all static reminders.

        Args:
            sort_by (TimelessSortingMethod, optional): How to sort the result.
                Defaults to TimelessSortingMethod.TITLE.

        Returns:
            List[StaticReminderData]: The info of each static reminder.
        """
        reminders = self.reminder_db.fetch()
        reminders.sort(key=sort_by.value[0], reverse=sort_by.value[1])
        return reminders

    def search(
        self,
        query: str,
        sort_by: TimelessSortingMethod = TimelessSortingMethod.TITLE
    ) -> List[StaticReminderData]:
        """Search for static reminders.

        Args:
            query (str): The term to search for.

            sort_by (TimelessSortingMethod, optional): The sorting method of
            the resulting list.
                Defaults to TimelessSortingMethod.TITLE.

        Returns:
            List[StaticReminderData]: All static reminders that match.
            Similar output to `self.fetchall`
        """
        static_reminders = [
            r
            for r in self.fetchall(sort_by)
            if search_filter(query, r)
        ]
        return static_reminders

    def fetchone(self, reminder_id: int) -> StaticReminder:
        """Get one static reminder.

        Args:
            reminder_id (int): The id of the static reminder to fetch.

        Raises:
            ReminderNotFound: The static reminder with the given ID does not
            exist or is not owned by the user.

        Returns:
            StaticReminder: A StaticReminder instance.
        """
        return StaticReminder(self.user_id, reminder_id)

    def add(
        self,
        title: str,
        notification_services: List[int],
        text: str = '',
        color: Union[str, None] = None
    ) -> StaticReminder:
        """Add a static reminder.

        Args:
            title (str): The title of the entry.

            notification_services (List[int]): The id's of the
            notification services to use to send the reminder.

            text (str, optional): The body of the reminder.
                Defaults to ''.

            color (Union[str, None], optional): The hex code of the color of the
            template, which is shown in the web-ui.
                Defaults to None.

        Raises:
            NotificationServiceNotFound: One of the notification services was
            not found.

        Returns:
            StaticReminder: The info about the static reminder
        """
        LOGGER.info(
            f'Adding static reminder with {title=}, {notification_services=}, {text=}, {color=}'
        )

        # Check if all notification services exist
        for ns in notification_services:
            NotificationService(self.user_id, ns)

        new_id = self.reminder_db.add(
            title, text, color,
            notification_services
        )

        return self.fetchone(new_id)
