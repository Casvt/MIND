# -*- coding: utf-8 -*-

from typing import List, Union

from backend.base.custom_exceptions import (NotificationServiceInUse,
                                            NotificationServiceNotFound,
                                            URLInvalid)
from backend.base.definitions import (Constants, NotificationServiceData,
                                      ReminderType, SendResult)
from backend.base.helpers import send_apprise_notification
from backend.base.logging import LOGGER
from backend.internals.db_models import (NotificationServicesDB,
                                         ReminderServicesDB)


class NotificationService:
    def __init__(
        self,
        user_id: int,
        notification_service_id: int
    ) -> None:
        """Create an instance.

        Args:
            user_id (int): The user ID that the service belongs to.
            notification_service_id (int): The ID of the service itself.

        Raises:
            NotificationServiceNotFound: The user does not own a notification
                service with the given ID.
        """
        self.user_id = user_id
        self.id = notification_service_id
        self.ns_db = NotificationServicesDB(self.user_id)

        if not self.ns_db.exists(self.id):
            raise NotificationServiceNotFound(self.id)

        return

    def get(self) -> NotificationServiceData:
        """Get the info about the notification service.

        Returns:
            NotificationServiceData: The info about the notification service.
        """
        return self.ns_db.fetch(self.id)[0]

    def update(
        self,
        title: Union[str, None] = None,
        url: Union[str, None] = None
    ) -> NotificationServiceData:
        """Edit the notification service. The URL is tested by sending a test
        notification to it.

        Args:
            title (Union[str, None], optional): The new title of the service.
                Defaults to None.

            url (Union[str, None], optional): The new url of the service.
                Defaults to None.

        Raises:
            URLInvalid: The url is invalid.

        Returns:
            NotificationServiceData: The new info about the service.
        """
        LOGGER.info(
            f'Updating notification service {self.id}: {title=}, {url=}'
        )

        # Get current data and update it with new values
        data = self.get().todict()
        is_url_updated = data["url"] != url

        new_values = {
            'title': title,
            'url': url
        }
        for k, v in new_values.items():
            if v is not None:
                data[k] = v

        if is_url_updated:
            test_result = NotificationServices.test(
                data['url']
            )
            if test_result != SendResult.SUCCESS:
                raise URLInvalid(data['url'], test_result)

        self.ns_db.update(self.id, data["title"], data["url"])

        return self.get()

    def delete(
        self,
        delete_reminders_using: bool = False
    ) -> None:
        """Delete the service.

        Args:
            delete_reminders_using (bool, optional): Instead of throwing an
                error when there are still reminders using the service, delete
                the reminders.
                Defaults to False.

        Raises:
            NotificationServiceInUse: The service is still used by a reminder
                and delete_reminders_using is False.
        """
        from backend.implementations.reminders import Reminder
        from backend.implementations.static_reminders import StaticReminder
        from backend.implementations.templates import Template

        LOGGER.info(f'Deleting notification service {self.id}')

        for reminder_type, ReminderClass in (
            (ReminderType.REMINDER, Reminder),
            (ReminderType.STATIC_REMINDER, StaticReminder),
            (ReminderType.TEMPLATE, Template)
        ):
            uses = ReminderServicesDB(reminder_type).uses_ns(self.id)
            if not uses:
                continue

            if not delete_reminders_using:
                raise NotificationServiceInUse(
                    self.id,
                    reminder_type.value
                )

            for r_id in uses:
                ReminderClass(self.user_id, r_id).delete()

        self.ns_db.delete(self.id)
        return


class NotificationServices:
    def __init__(self, user_id: int) -> None:
        """Create an instance.

        Args:
            user_id (int): The ID of the user.
        """
        self.user_id = user_id
        self.ns_db = NotificationServicesDB(self.user_id)
        return

    def get_all(self) -> List[NotificationServiceData]:
        """Get a list of all notification services.

        Returns:
            List[NotificationServiceData]: The info about all
                notification services.
        """
        return self.ns_db.fetch()

    def get_one(self, notification_service_id: int) -> NotificationService:
        """Get a notification service instance based on the ID.

        Args:
            notification_service_id (int): The ID of the service.

        Raises:
            NotificationServiceNotFound: The user does not own a notification
                service with the given ID.

        Returns:
            NotificationService: Instance of NotificationService.
        """
        return NotificationService(self.user_id, notification_service_id)

    def add(self, title: str, url: str) -> NotificationService:
        """Add a notification service. The service is tested by sending a test
        notification to it.

        Args:
            title (str): The title of the service.
            url (str): The apprise url of the service.

        Raises:
            URLInvalid: The url is invalid.

        Returns:
            NotificationService: The instance representing the new service.
        """
        LOGGER.info(f'Adding notification service with {title=}, {url=}')

        test_result = self.test(url)
        if test_result != SendResult.SUCCESS:
            raise URLInvalid(url, test_result)

        new_id = self.ns_db.add(title, url)

        return self.get_one(new_id)

    @staticmethod
    def test(url: str) -> SendResult:
        """Test a notification service by sending a test notification to it.

        Args:
            url (str): The apprise url of the service.

        Returns:
            SendResult: The result of the test.
        """
        return send_apprise_notification(
            [url],
            Constants.APPRISE_TEST_TITLE,
            Constants.APPRISE_TEST_BODY
        )
