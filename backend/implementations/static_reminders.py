# -*- coding: utf-8 -*-

from typing import List, Union

from backend.base.custom_exceptions import StaticReminderNotFound
from backend.base.definitions import (SendResult, StaticReminderData,
                                      TimelessSortingMethod)
from backend.base.helpers import search_filter, send_apprise_notification
from backend.base.logging import LOGGER
from backend.implementations.notification_services import NotificationService
from backend.internals.db_models import StaticRemindersDB


class StaticReminder:
    def __init__(self, user_id: int, static_reminder_id: int) -> None:
        """Create an instance.

        Args:
            user_id (int): The ID of the user.
            static_reminder_id (int): The ID of the static reminder.

        Raises:
            StaticReminderNotFound: Reminder with given ID does not exist or is
                not owned by user.
        """
        self.user_id = user_id
        self.id = static_reminder_id
        self.reminder_db = StaticRemindersDB(self.user_id)

        if not self.reminder_db.exists(self.id):
            raise StaticReminderNotFound(static_reminder_id)
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

        urls = [
            NotificationService(self.user_id, ns_id).get().url
            for ns_id in reminder_data.notification_services
        ]

        return send_apprise_notification(
            urls,
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
            title (Union[str, None], optional): The new title of the
                static reminder.
                Defaults to None.

            notification_services (Union[List[int], None], optional): The new
                IDs of the notification services to use to send the reminder.
                Defaults to None.

            text (Union[str, None], optional): The new body of the
                static reminder.
                Defaults to None.

            color (Union[str, None], optional): The new hex code of the color of
                the static reminder, which is shown in the web-ui.
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
            # Check if all notification services exist. Creating an instance
            # raises NotificationServiceNotFound if the ID is not valid.
            for ns in notification_services:
                NotificationService(self.user_id, ns)

        data = self.get().todict()

        new_values = {
            'title': title,
            'text': text,
            'color': color,
            'notification_services': notification_services
        }
        for k, v in new_values.items():
            if k == 'color' or v is not None:
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

    def get_all(
        self,
        sort_by: TimelessSortingMethod = TimelessSortingMethod.TITLE
    ) -> List[StaticReminderData]:
        """Get all static reminders of the user.

        Args:
            sort_by (TimelessSortingMethod, optional): How to sort the
                static reminders.
                Defaults to TimelessSortingMethod.TITLE.

        Returns:
            List[StaticReminderData]: The info about all static reminders of
                the user.
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
            sort_by (TimelessSortingMethod, optional): How to sort the
                static reminders.
                Defaults to TimelessSortingMethod.TITLE.

        Returns:
            List[StaticReminderData]: the info about all static reminders of
                the user that match the search term.
        """
        return [
            r
            for r in self.get_all(sort_by)
            if search_filter(query, r)
        ]

    def get_one(self, static_reminder_id: int) -> StaticReminder:
        """Get a static reminder instance based on the ID.

        Args:
            reminder_id (int): The id of the static reminder to fetch.

        Raises:
            StaticReminderNotFound: The user does not own a static reminder
                with the given ID.

        Returns:
            StaticReminder: Instance of StaticReminder.
        """
        return StaticReminder(self.user_id, static_reminder_id)

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

            notification_services (List[int]): The IDs of the notification
                services to use to send the static reminder.

            text (str, optional): The body of the static reminder.
                Defaults to ''.

            color (Union[str, None], optional): The hex code of the color of the
                static reminder, which is shown in the web-ui.
                Defaults to None.

        Raises:
            NotificationServiceNotFound: One of the notification services was
                not found.

        Returns:
            StaticReminder: The info about the static reminder.
        """
        LOGGER.info(
            f'Adding static reminder with {title=}, {notification_services=}, '
            f'{text=}, {color=}'
        )

        # Check if all notification services exist. Creating an instance
        # raises NotificationServiceNotFound if the ID is not valid.
        for ns in notification_services:
            NotificationService(self.user_id, ns)

        new_id = self.reminder_db.add(
            title, text, color,
            notification_services
        )

        return self.get_one(new_id)
