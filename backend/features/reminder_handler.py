# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Union

from backend.base.definitions import Constants, RepeatQuantity, SendResult
from backend.base.helpers import find_next_time, when_not_none
from backend.base.logging import LOGGER
from backend.implementations.reminders import Reminder
from backend.internals.db_models import UserlessRemindersDB
from backend.internals.server import Server

if TYPE_CHECKING:
    from threading import Timer


class ReminderHandler:
    """
    Handling of the reminders such that they are sent at their scheduled time.
    """

    reminder_timer: Union[Timer, None] = None
    next_trigger_time: Union[int, None] = None
    reminder_db = UserlessRemindersDB()

    @classmethod
    def _trigger_reminders(cls, time: int) -> None:
        """Trigger all reminders that are set for a certain time.

        Args:
            time (int): The time of the reminders to trigger.
        """
        for reminder in cls.reminder_db.fetch(time):
            try:
                user_id = cls.reminder_db.reminder_id_to_user_id(
                    reminder.id
                )
                result = Reminder(user_id, reminder.id).trigger_reminder()

                if result == SendResult.CONNECTION_ERROR:
                    # Retry sending the notification in a few minutes
                    cls.reminder_db.shift(
                        reminder.id,
                        Constants.CONNECTION_ERROR_TIMEOUT
                    )

                elif not any((
                    reminder.repeat_quantity,
                    reminder.weekdays,
                    reminder.cron_schedule
                )):
                    # Delete the reminder from the database
                    cls.reminder_db.delete(reminder.id)

                else:
                    # Set next time
                    new_time = find_next_time(
                        reminder.original_time or -1,
                        when_not_none(
                            reminder.repeat_quantity,
                            lambda q: RepeatQuantity(q)
                        ),
                        reminder.repeat_interval,
                        reminder.weekdays,
                        reminder.cron_schedule
                    )

                    cls.reminder_db.update(reminder.id, new_time)

            except Exception:
                # If the notification fails, we don't want to crash the whole program
                # Just log the error and continue
                LOGGER.exception(
                    "Failed to send notification for reminder %s: ",
                    reminder.id
                )

            finally:
                cls.reminder_timer = None
                cls.next_trigger_time = None
                cls.set_reminder_timer()

        return

    @classmethod
    def set_reminder_timer(cls, time: Union[int, None] = None) -> None:
        """Update the timer for sending the soonest upcoming reminder. Start one
        if it hasn't already. Replace it if it does already exist, in case the
        time the soonest reminder triggers has changed.

        Args:
            time (Union[int, None], optional): Check whether the given timestamp
                changes anything to the situation. If not given, the soonest
                timestamp in the database is checked.

                Defaults to None.
        """
        if time is None:
            time = cls.reminder_db.get_soonest_time()
            if not time:
                return

        if (
            cls.reminder_timer is None
            or (
                cls.next_trigger_time is not None
                and time < cls.next_trigger_time
            )
        ):
            if cls.reminder_timer is not None:
                cls.reminder_timer.cancel()

            delta_t = time - datetime.utcnow().timestamp()
            cls.reminder_timer = Server().get_db_timer_thread(
                delta_t,
                cls._trigger_reminders,
                "ReminderHandler",
                args=(time,)
            )
            cls.reminder_timer.start()
            cls.next_trigger_time = time

        return

    @classmethod
    def stop_reminder_timer(cls) -> None:
        "If the reminder timer is running, stop it"
        if cls.reminder_timer is not None:
            cls.reminder_timer.cancel()
        return
