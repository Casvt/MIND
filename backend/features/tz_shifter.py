# -*- coding: utf-8 -*-

"""
Detector of timezone/DST changes and shifts reminder times to counter it.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Union

from backend.base.definitions import Constants
from backend.base.logging import LOGGER
from backend.features.reminder_handler import ReminderHandler
from backend.internals.db_models import UserlessRemindersDB
from backend.internals.server import Server
from backend.internals.settings import Settings

if TYPE_CHECKING:
    from threading import Timer


def get_timezone_offset() -> int:
    """Get the offset between the local timezone and UTC, in minutes.

    Returns:
        int: The offset in minutes.
    """
    time.tzset()
    if time.localtime().tm_isdst == 0:
        return -time.timezone
    return -time.altzone


class TimezoneChangeHandler:
    detector_timer: Union[Timer, None] = None

    @staticmethod
    def __get_next_trigger_time() -> int:
        """Get the epoch timestamp of the next time a timezone change check
        should be done.

        Returns:
            int: The epoch timestamp.
        """
        # Get current time, but set hour and minute to desired trigger time
        current_time = datetime.now()
        target_time = current_time.replace(
            hour=Constants.TZ_CHANGE_CHECK_TIME[0],
            minute=Constants.TZ_CHANGE_CHECK_TIME[1]
        )

        if target_time < current_time:
            # Current target time is in the past (trigger time has already been
            # today), so run tomorrow at trigger time.
            target_time += timedelta(days=1)

        return int(target_time.timestamp())

    @classmethod
    def detect_and_handle_timezone_change(cls) -> None:
        """
        Check whether a change in timezone/DST has happened and if so shift
        all reminders. Also update DB on last measured timezone.
        """
        settings = Settings()
        measured_timezone = settings.sv.measured_timezone
        current_timezone = get_timezone_offset()

        if measured_timezone == -1:
            # First measurement, so nothing to compare against
            settings.update({"measured_timezone": current_timezone})

        elif measured_timezone != current_timezone:
            # Timezone change
            settings.update({"measured_timezone": current_timezone})

            shift_delta = measured_timezone - current_timezone
            UserlessRemindersDB().shift(
                reminder_id=None,
                offset=shift_delta
            )
            ReminderHandler.set_reminder_timer()

            LOGGER.info(
                "Detected timezone/DST change (%s to %s), shifted reminders",
                measured_timezone, current_timezone
            )

        cls.detector_timer = None
        cls.set_detector_timer()
        return

    @classmethod
    def set_detector_timer(cls) -> None:
        """
        Set the timer for checking on a change in timezone and handling it if
        so. Doesn't do anything if timer is already set.
        """
        if cls.detector_timer is not None:
            return

        cls.detector_timer = Server().get_db_timer_thread(
            cls.__get_next_trigger_time() - time.time(),
            cls.detect_and_handle_timezone_change,
            "TimezoneChangeHandler"
        )
        cls.detector_timer.start()
        return

    @classmethod
    def stop_detector_timer(cls) -> None:
        "If the timezone change detection timer is running, stop it"
        if cls.detector_timer is not None:
            cls.detector_timer.cancel()
        return
