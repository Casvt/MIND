# -*- coding: utf-8 -*-

from dataclasses import asdict
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
        """Create an representation of a notification service.

        Args:
            user_id (int): The ID that the service belongs to.
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

        Returns:
            NotificationServiceData: The new info about the service.
        """
        LOGGER.info(
            f'Updating notification service {self.id}: {title=}, {url=}'
        )

        # Get current data and update it with new values
        data = asdict(self.get())
        test_url = data["url"] != url

        new_values = {
            'title': title,
            'url': url
        }
        for k, v in new_values.items():
            if v is not None:
                data[k] = v

        if test_url:
            test_result = NotificationServices(self.user_id).test(
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
            NotificationServiceInUse: The service is still used by a reminder.
        """
        from backend.features.reminders import Reminder
        from backend.features.static_reminders import StaticReminder
        from backend.features.templates import Template

        LOGGER.info(f'Deleting notification service {self.id}')

        for r_type, RClass in (
            (ReminderType.REMINDER, Reminder),
            (ReminderType.STATIC_REMINDER, StaticReminder),
            (ReminderType.TEMPLATE, Template)
        ):
            uses = ReminderServicesDB(r_type).uses_ns(self.id)
            if uses:
                if not delete_reminders_using:
                    raise NotificationServiceInUse(
                        self.id,
                        r_type.value
                    )

                for r_id in uses:
                    RClass(self.user_id, r_id).delete()

        self.ns_db.delete(self.id)
        return


class NotificationServices:
    def __init__(self, user_id: int) -> None:
        """Represent the notification services of a user.

        Args:
            user_id (int): The ID of the user.
        """
        self.user_id = user_id
        self.ns_db = NotificationServicesDB(self.user_id)
        return

    def fetchall(self) -> List[NotificationServiceData]:
        """Get a list of all notification services.

        Returns:
            List[NotificationServiceData]: The list of all notification services.
        """
        return self.ns_db.fetch()

    def fetchone(self, notification_service_id: int) -> NotificationService:
        """Get one notification service based on it's id.

        Args:
            notification_service_id (int): The id of the desired service.

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

        return self.fetchone(new_id)

    def test(self, url: str) -> SendResult:
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
