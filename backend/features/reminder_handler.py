# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Union

from backend.base.definitions import Constants, RepeatQuantity, SendResult
from backend.base.helpers import (Singleton, find_next_time,
                                  send_apprise_notification, when_not_none)
from backend.base.logging import LOGGER
from backend.implementations.notification_services import NotificationService
from backend.internals.db_models import UserlessRemindersDB
from backend.internals.server import Server

if TYPE_CHECKING:
    from threading import Timer


class ReminderHandler(metaclass=Singleton):
    """
    Handle set reminders. This class is a singleton.
    """

    def __init__(self) -> None:
        "Create instance of handler"
        self.thread: Union[Timer, None] = None
        self.time: Union[int, None] = None
        self.reminder_db = UserlessRemindersDB()
        return

    def __trigger_reminders(self, time: int) -> None:
        """Trigger all reminders that are set for a certain time.

        Args:
            time (int): The time of the reminders to trigger.
        """
        for reminder in self.reminder_db.fetch(time):
            try:
                user_id = self.reminder_db.reminder_id_to_user_id(
                    reminder.id
                )
                result = send_apprise_notification(
                    [
                        NotificationService(user_id, ns).get().url
                        for ns in reminder.notification_services
                    ],
                    reminder.title,
                    reminder.text
                )

                self.thread = None
                self.time = None

                if result == SendResult.CONNECTION_ERROR:
                    # Retry sending the notification in a few minutes
                    self.reminder_db.update(
                        reminder.id,
                        time + Constants.CONNECTION_ERROR_TIMEOUT
                    )

                elif (
                    reminder.repeat_quantity,
                    reminder.weekdays
                ) == (None, None):
                    # Delete the reminder from the database
                    self.reminder_db.delete(reminder.id)

                else:
                    # Set next time
                    new_time = find_next_time(
                        reminder.original_time or -1,
                        when_not_none(
                            reminder.repeat_quantity,
                            lambda q: RepeatQuantity(q)
                        ),
                        reminder.repeat_interval,
                        reminder.weekdays
                    )

                    self.reminder_db.update(reminder.id, new_time)

            except Exception:
                # If the notification fails, we don't want to crash the whole program
                # Just log the error and continue
                LOGGER.exception(
                    "Failed to send notification for reminder %s: ",
                    reminder.id
                )

            finally:
                self.find_next_reminder()

        return

    def find_next_reminder(self, time: Union[int, None] = None) -> None:
        """Determine when the soonest reminder is and set the timer to that time.

        Args:
            time (Union[int, None], optional): The timestamp to check for.
            Otherwise check soonest in database.
                Defaults to None.
        """
        if time is None:
            time = self.reminder_db.get_soonest_time()
            if not time:
                return

        if (
            self.thread is None
            or (
                self.time is not None
                and time < self.time
            )
        ):
            if self.thread is not None:
                self.thread.cancel()

            delta_t = time - datetime.utcnow().timestamp()
            self.thread = Server().get_db_timer_thread(
                delta_t,
                self.__trigger_reminders,
                "ReminderHandler",
                args=(time,)
            )
            self.thread.start()
            self.time = time

        return

    def stop_handling(self) -> None:
        """Stop the timer if it's active
        """
        if self.thread is not None:
            self.thread.cancel()
        return
