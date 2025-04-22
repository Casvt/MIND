# -*- coding: utf-8 -*-

from dataclasses import asdict
from typing import List, Union

from backend.base.custom_exceptions import TemplateNotFound
from backend.base.definitions import TemplateData, TimelessSortingMethod
from backend.base.helpers import search_filter
from backend.base.logging import LOGGER
from backend.implementations.notification_services import NotificationService
from backend.internals.db_models import TemplatesDB


class Template:
    def __init__(self, user_id: int, template_id: int) -> None:
        """Represent a template.

        Args:
            user_id (int): The ID of the user.
            template_id (int): The ID of the template.

        Raises:
            TemplateNotFound: Template with given ID does not exist or is not
            owned by user.
        """
        self.user_id = user_id
        self.id = template_id

        self.template_db = TemplatesDB(self.user_id)

        if not self.template_db.exists(self.id):
            raise TemplateNotFound(self.id)
        return

    def get(self) -> TemplateData:
        """Get info about the template.

        Returns:
            TemplateData: The info about the template.
        """
        return self.template_db.fetch(self.id)[0]

    def update(self,
        title: Union[str, None] = None,
        notification_services: Union[List[int], None] = None,
        text: Union[str, None] = None,
        color: Union[str, None] = None
    ) -> TemplateData:
        """Edit the template.

        Args:
            title (Union[str, None]): The new title of the entry.
                Defaults to None.

            notification_services (Union[List[int], None]): The new id's of the
            notification services to use to send the reminder.
                Defaults to None.

            text (Union[str, None], optional): The new body of the template.
                Defaults to None.

            color (Union[str, None], optional): The new hex code of the color of
            the template, which is shown in the web-ui.
                Defaults to None.

        Raises:
            NotificationServiceNotFound: One of the notification services was
            not found.

        Returns:
            TemplateData: The new template info.
        """
        LOGGER.info(
            f'Updating template {self.id}: '
            + f'{title=}, {notification_services=}, {text=}, {color=}'
        )

        if notification_services:
            # Check if all notification services exist
            for ns in notification_services:
                NotificationService(self.user_id, ns)

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

        self.template_db.update(
            self.id,
            data['title'],
            data['text'],
            data['color'],
            data['notification_services']
        )

        return self.get()

    def delete(self) -> None:
        "Delete the template"
        LOGGER.info(f'Deleting template {self.id}')
        self.template_db.delete(self.id)
        return


class Templates:
    def __init__(self, user_id: int) -> None:
        """Create an instance.

        Args:
            user_id (int): The ID of the user.
        """
        self.user_id = user_id
        self.template_db = TemplatesDB(self.user_id)
        return

    def fetchall(
        self,
        sort_by: TimelessSortingMethod = TimelessSortingMethod.TITLE
    ) -> List[TemplateData]:
        """Get all templates of the user.

        Args:
            sort_by (TimelessSortingMethod, optional): The sorting method of
            the resulting list.
                Defaults to TimelessSortingMethod.TITLE.

        Returns:
            List[TemplateData]: The id, title, text and color of each template.
        """
        templates = self.template_db.fetch()
        templates.sort(key=sort_by.value[0], reverse=sort_by.value[1])
        return templates

    def search(
        self,
        query: str,
        sort_by: TimelessSortingMethod = TimelessSortingMethod.TITLE
    ) -> List[TemplateData]:
        """Search for templates.

        Args:
            query (str): The term to search for.

            sort_by (TimelessSortingMethod, optional): The sorting method of
            the resulting list.
                Defaults to TimelessSortingMethod.TITLE.

        Returns:
            List[TemplateData]: All templates that match. Similar output to
            `self.fetchall`.
        """
        templates = [
            r
            for r in self.fetchall(sort_by)
            if search_filter(query, r)
        ]
        return templates

    def fetchone(self, template_id: int) -> Template:
        """Get one template.

        Args:
            template_id (int): The id of the template to fetch.

        Raises:
            TemplateNotFound: Template with given ID does not exist or is not
            owned by user.

        Returns:
            Template: A Template instance.
        """
        return Template(self.user_id, template_id)

    def add(
        self,
        title: str,
        notification_services: List[int],
        text: str = '',
        color: Union[str, None] = None
    ) -> Template:
        """Add a template.

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
            Template: The info about the template.
        """
        LOGGER.info(
            f'Adding template with {title=}, {notification_services=}, {text=}, {color=}'
        )

        # Check if all notification services exist
        for ns in notification_services:
            NotificationService(self.user_id, ns)

        new_id = self.template_db.add(
            title, text, color,
            notification_services
        )

        return self.fetchone(new_id)
