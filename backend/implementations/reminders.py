# -*- coding: utf-8 -*-

from datetime import datetime
from typing import List, Union

from backend.base.custom_exceptions import (InvalidKeyValue, InvalidTime,
                                            ReminderNotFound)
from backend.base.definitions import (WEEKDAY_NUMBER, ReminderData,
                                      RepeatQuantity, SendResult,
                                      SortingMethod)
from backend.base.helpers import (find_next_time, search_filter,
                                  send_apprise_notification, when_not_none)
from backend.base.logging import LOGGER
from backend.implementations.notification_services import NotificationService
from backend.internals.db_models import RemindersDB


class Reminder:
    def __init__(self, user_id: int, reminder_id: int) -> None:
        """Create an instance.

        Args:
            user_id (int): The ID of the user.
            reminder_id (int): The ID of the reminder.

        Raises:
            ReminderNotFound: Reminder with given ID does not exist or is not
                owned by user.
        """
        self.user_id = user_id
        self.id = reminder_id
        self.reminder_db = RemindersDB(self.user_id)

        if not self.reminder_db.exists(self.id):
            raise ReminderNotFound(reminder_id)
        return

    def get(self) -> ReminderData:
        """Get info about the reminder.

        Returns:
            ReminderData: The info about the reminder.
        """
        return self.reminder_db.fetch(self.id)[0]

    def trigger_reminder(self) -> SendResult:
        """Send the reminder.

        Returns:
            SendResult: The result of the sending process.
        """
        LOGGER.info(f'Triggering reminder {self.id}')

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
        time: Union[int, None] = None,
        notification_services: Union[List[int], None] = None,
        text: Union[str, None] = None,
        repeat_quantity: Union[RepeatQuantity, None] = None,
        repeat_interval: Union[int, None] = None,
        weekdays: Union[List[WEEKDAY_NUMBER], None] = None,
        cron_schedule: Union[str, None] = None,
        color: Union[str, None] = None,
        enabled: Union[bool, None] = None
    ) -> ReminderData:
        """Edit the reminder.

        Args:
            title (Union[str, None], optional): The new title of the reminder.
                Defaults to None.

            time (Union[int, None], optional): The new UTC epoch timestamp when
                the reminder should be send.
                Defaults to None.

            notification_services (Union[List[int], None], optional): The new
                IDs of the notification services to use to send the reminder.
                Defaults to None.

            text (Union[str, None], optional): The new body of the reminder.
                Defaults to None.

            repeat_quantity (Union[RepeatQuantity, None], optional): The new
                quantity of the repeat_interval specified for the reminder.
                Defaults to None.

            repeat_interval (Union[int, None], optional): The new interval of
                repeat_quantity, like "5" (hours).
                Defaults to None.

            weekdays (Union[List[WEEKDAY_NUMBER], None], optional): The new
                indexes of the days of the week that the reminder should run.
                Defaults to None.

            cron_schedule (Union[str, None], optional): The new cron schedule
                that the reminder should run on.
                Defaults to None.

            color (Union[str, None], optional): The new hex code of the color
                of the reminder, which is shown in the web-ui.
                Defaults to None.

            enabled (Union[bool, None], optional): Whether the reminder should
                be enabled.
                Defaults to None.

        Note about args:
            Either repeat_quantity and repeat_interval are given, weekdays is
            given, cron_schedule is given, or none, but not a combination.

        Raises:
            NotificationServiceNotFound: One of the notification services was
                not found.
            InvalidKeyValue: The value of one of the keys is not valid or
                the "Note about args" is violated.

        Returns:
            ReminderData: The new reminder info.
        """
        from backend.features.reminder_handler import ReminderHandler

        LOGGER.info(
            f'Updating notification service {self.id}: '
            + f'{title=}, {time=}, {notification_services=}, {text=}, '
            + f'{repeat_quantity=}, {repeat_interval=}, '
            + f'{weekdays=}, {cron_schedule=}, '
            + f'{color=}, {enabled=}'
        )

        # Validate data
        if cron_schedule is not None and (
            repeat_quantity is not None
            or repeat_interval is not None
            or weekdays is not None
        ):
            raise InvalidKeyValue('cron_schedule', cron_schedule)
        if repeat_quantity is None and repeat_interval is not None:
            raise InvalidKeyValue('repeat_quantity', repeat_quantity)
        elif repeat_quantity is not None and repeat_interval is None:
            raise InvalidKeyValue('repeat_interval', repeat_interval)
        elif weekdays is not None and repeat_quantity is not None:
            raise InvalidKeyValue('weekdays', weekdays)

        repeated_reminder = (
            (repeat_quantity is not None and repeat_interval)
            or weekdays
            or cron_schedule
        )

        if time is not None:
            if not repeated_reminder:
                if time < datetime.utcnow().timestamp():
                    raise InvalidTime(time)
            time = round(time)

        if notification_services:
            # Check if all notification services exist. Creating an instance
            # raises NotificationServiceNotFound if the ID is not valid.
            for ns in notification_services:
                NotificationService(self.user_id, ns)

        data = self.get().todict()

        new_values = {
            'title': title,
            'time': time,
            'text': text,
            'repeat_quantity': when_not_none(
                repeat_quantity,
                lambda q: q.value
            ),
            'repeat_interval': repeat_interval,
            'weekdays': when_not_none(
                weekdays,
                lambda w: ",".join(map(str, sorted(w)))
            ),
            'cron_schedule': cron_schedule,
            'color': color,
            'notification_services': notification_services,
            'enabled': enabled
        }
        for k, v in new_values.items():
            if (
                k in (
                    'repeat_quantity', 'repeat_interval',
                    'weekdays', 'cron_schedule',
                    'color'
                )
                or v is not None
            ):
                data[k] = v

        if repeated_reminder:
            next_time = find_next_time(
                data["time"],
                repeat_quantity,
                data["repeat_interval"],
                weekdays,
                cron_schedule
            )
            self.reminder_db.update(
                self.id,
                data["title"],
                data["text"],
                next_time,
                data["repeat_quantity"],
                data["repeat_interval"],
                data["weekdays"],
                data["cron_schedule"],
                data["time"],
                data["color"],
                data["notification_services"],
                data["enabled"]
            )

        else:
            next_time = data["time"]
            self.reminder_db.update(
                self.id,
                data["title"],
                data["text"],
                next_time,
                data["repeat_quantity"],
                data["repeat_interval"],
                data["weekdays"],
                data["cron_schedule"],
                data["original_time"],
                data["color"],
                data["notification_services"],
                data["enabled"]
            )

        ReminderHandler().find_next_reminder(next_time)
        return self.get()

    def delete(self) -> None:
        "Delete the reminder"
        from backend.features.reminder_handler import ReminderHandler

        LOGGER.info(f'Deleting reminder {self.id}')
        self.reminder_db.delete(self.id)
        ReminderHandler().find_next_reminder()
        return


class Reminders:
    def __init__(self, user_id: int) -> None:
        """Create an instance.

        Args:
            user_id (int): The ID of the user.
        """
        self.user_id = user_id
        self.reminder_db = RemindersDB(self.user_id)
        return

    def get_all(
        self,
        sort_by: SortingMethod = SortingMethod.TIME
    ) -> List[ReminderData]:
        """Get all reminders of the user.

        Args:
            sort_by (SortingMethod, optional): How to sort the
                reminders.
                Defaults to SortingMethod.TIME.

        Returns:
            List[ReminderData]: The info about all reminders of the user.
        """
        reminders = self.reminder_db.fetch()
        reminders.sort(key=sort_by.value[0], reverse=sort_by.value[1])
        return reminders

    def search(
        self,
        query: str,
        sort_by: SortingMethod = SortingMethod.TIME
    ) -> List[ReminderData]:
        """Search for reminders.

        Args:
            query (str): The term to search for.
            sort_by (SortingMethod, optional): How to sort the
                reminders.
                Defaults to SortingMethod.TIME.

        Returns:
            List[ReminderData]: The info about all reminders of the user that
                match the search term.
        """
        return [
            r
            for r in self.get_all(sort_by)
            if search_filter(query, r)
        ]

    def get_one(self, reminder_id: int) -> Reminder:
        """Get a reminder instance based on the ID.

        Args:
            reminder_id (int): The ID of the reminder to fetch.

        Raises:
            ReminderNotFound: The user does not own a reminder with the given ID.

        Returns:
            Reminder: Instance of Reminder.
        """
        return Reminder(self.user_id, reminder_id)

    def add(
        self,
        title: str,
        time: int,
        notification_services: List[int],
        text: str = '',
        repeat_quantity: Union[RepeatQuantity, None] = None,
        repeat_interval: Union[int, None] = None,
        weekdays: Union[List[WEEKDAY_NUMBER], None] = None,
        cron_schedule: Union[str, None] = None,
        color: Union[str, None] = None,
        enabled: bool = True
    ) -> Reminder:
        """Add a reminder.

        Args:
            title (str): The title of the reminder.

            time (int): The UTC epoch timestamp the the reminder should be send.

            notification_services (List[int]): The IDs of the notification
                services to use to send the reminder.

            text (str, optional): The body of the reminder.
                Defaults to ''.

            repeat_quantity (Union[RepeatQuantity, None], optional): The
                quantity of the repeat_interval specified for the reminder.
                Defaults to None.

            repeat_interval (Union[int, None], optional): The interval of
                repeat_quantity, like "5" (hours).
                Defaults to None.

            weekdays (Union[List[WEEKDAY_NUMBER], None], optional): The indexes
                of the days of the week that the reminder should run.
                Defaults to None.

            cron_schedule (Union[str, None], optional): The cron schedule that
                the reminder should run on.
                Defaults to None.

            color (Union[str, None], optional): The hex code of the color of the
                reminder, which is shown in the web-ui.
                Defaults to None.

            enabled (Union[bool, None], optional): Whether the reminder should
                be enabled.
                Defaults to None.

        Note about args:
            Either repeat_quantity and repeat_interval are given, weekdays is
            given, cron_schedule is given, or none, but not a combination.

        Raises:
            NotificationServiceNotFound: One of the notification services was
                not found.
            InvalidKeyValue: The value of one of the keys is not valid or
                the "Note about args" is violated.

        Returns:
            Reminder: The info about the reminder.
        """
        from backend.features.reminder_handler import ReminderHandler

        LOGGER.info(
            f'Adding reminder with {title=}, {time=}, {notification_services=}, '
            f'{text=}, {repeat_quantity=}, {repeat_interval=}, {weekdays=}, '
            f'{cron_schedule=}, {color=}, {enabled=}')

        # Validate data
        if time < datetime.utcnow().timestamp():
            raise InvalidTime(time)
        time = round(time)

        if cron_schedule is not None and (
            repeat_quantity is not None
            or repeat_interval is not None
            or weekdays is not None
        ):
            raise InvalidKeyValue('cron_schedule', cron_schedule)
        if repeat_quantity is None and repeat_interval is not None:
            raise InvalidKeyValue('repeat_quantity', repeat_quantity)
        elif repeat_quantity is not None and repeat_interval is None:
            raise InvalidKeyValue('repeat_interval', repeat_interval)
        elif (
            weekdays is not None
            and repeat_quantity is not None
            and repeat_interval is not None
        ):
            raise InvalidKeyValue('weekdays', weekdays)

        # Check if all notification services exist. Creating an instance
        # raises NotificationServiceNotFound if the ID is not valid.
        for ns in notification_services:
            NotificationService(self.user_id, ns)

        # Prepare args
        if any((repeat_quantity, weekdays, cron_schedule)):
            original_time = time
            time = find_next_time(
                original_time,
                repeat_quantity,
                repeat_interval,
                weekdays,
                cron_schedule
            )
        else:
            original_time = None

        weekdays_str = when_not_none(
            weekdays,
            lambda w: ",".join(map(str, sorted(w)))
        )
        repeat_quantity_str = when_not_none(
            repeat_quantity,
            lambda q: q.value
        )

        new_id = self.reminder_db.add(
            title,
            text,
            time,
            repeat_quantity_str,
            repeat_interval,
            weekdays_str,
            cron_schedule,
            original_time,
            color,
            notification_services,
            enabled
        )

        ReminderHandler().find_next_reminder(time)

        return self.get_one(new_id)

    def test_reminder(
        self,
        title: str,
        notification_services: List[int],
        text: str = ''
    ) -> SendResult:
        """Test a reminder by sending it.

        Args:
            title (str): The title of the reminder.

            notification_service (int): The IDs of the notification
                services to use to send the reminder.

            text (str, optional): The body of the reminder.
                Defaults to ''.

        Returns:
            SendResult: The result of the test.
        """
        LOGGER.info(
            f'Testing reminder with {title=}, {notification_services=}, {text=}'
        )

        urls = [
            NotificationService(self.user_id, ns_id).get().url
            for ns_id in notification_services
        ]

        return send_apprise_notification(
            urls,
            title,
            text
        )
