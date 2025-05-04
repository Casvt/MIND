# -*- coding: utf-8 -*-

"""
Detector of timezone/DST changes and shifts reminder times to counter it.
"""

import time
from datetime import datetime, timedelta
from threading import Timer
from typing import Union

from backend.base.definitions import Constants
from backend.base.helpers import Singleton
from backend.base.logging import LOGGER
from backend.internals.db_models import UserlessRemindersDB
from backend.internals.server import Server
from backend.internals.settings import Settings


def get_timezone_offset() -> int:
    """Get the offset between the local timezone and UTC, in minutes.

    Returns:
        int: The offset in minutes.
    """
    time.tzset()
    if time.localtime().tm_isdst == 0:
        return -time.timezone
    return -time.altzone


class TimezoneChangeHandler(metaclass=Singleton):
    checker_timer: Union[Timer, None] = None

    def __get_next_trigger_time(self) -> int:
        """Get a timestamp of the next time the timer should be triggered.

        Returns:
            int: The timestamp.
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

    def _detect_timezone_change(self) -> None:
        """
        Check whether a change in timezone/DST has happened and if so shift
        all reminders. Also update DB on last measured timezone.
        """
        settings = Settings()
        measured_timezone = settings.sv.measured_timezone
        current_timezone = get_timezone_offset()

        if measured_timezone == -1:
            settings.update({"measured_timezone": current_timezone})

        elif measured_timezone != current_timezone:
            # Timezone change
            shift_delta = measured_timezone - current_timezone
            UserlessRemindersDB().shift(
                reminder_id=None,
                offset=shift_delta
            )
            settings.update({"measured_timezone": current_timezone})
            LOGGER.info(
                "Detected timezone/DST change (%s to %s), shifted reminders",
                measured_timezone, current_timezone
            )

        self.checker_timer = None
        self.set_detector_timer()
        return

    def set_detector_timer(self) -> None:
        """
        Set the timer for the timezone change detection process. Start one if it
        hasn't already. Don't do anything if it's already set.
        """
        if self.checker_timer is not None:
            return

        self.checker_timer = Server().get_db_timer_thread(
            self.__get_next_trigger_time() - time.time(),
            self._detect_timezone_change,
            "TimezoneChangeHandler"
        )
        self.checker_timer.start()
        return

    def stop_detector_timer(self) -> None:
        "If the timezone change detection timer is running, stop it"
        if self.checker_timer is not None:
            self.checker_timer.cancel()
        return
