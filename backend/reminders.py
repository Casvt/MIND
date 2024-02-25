#-*- coding: utf-8 -*-

import logging
from datetime import datetime
from sqlite3 import IntegrityError
from threading import Timer
from typing import List, Literal, Union

from apprise import Apprise
from dateutil.relativedelta import relativedelta
from dateutil.relativedelta import weekday as du_weekday

from backend.custom_exceptions import (InvalidKeyValue, InvalidTime,
                                       NotificationServiceNotFound,
                                       ReminderNotFound)
from backend.db import get_db
from backend.helpers import RepeatQuantity, Singleton, SortingMethod, search_filter


def __next_selected_day(
	weekdays: List[int],
	weekday: int
) -> int:
	"""Find the next allowed day in the week.

	Args:
		weekdays (List[int]): The days of the week that are allowed.
		Monday is 0, Sunday is 6.
		weekday (int): The current weekday.

	Returns:
		int: The next allowed weekday.
	"""
	return (
		# Get all days later than current, then grab first one.
		[d for d in weekdays if weekday < d]
		or
		# weekday is last allowed day, so it should grab the first
		# allowed day of the week.
		weekdays
	)[0]

def _find_next_time(
	original_time: int,
	repeat_quantity: Union[RepeatQuantity, None],
	repeat_interval: Union[int, None],
	weekdays: Union[List[int], None]
) -> int:
	"""Calculate the next timestep based on original time and repeat/interval
	values.

	Args:
		original_time (int): The original time of the repeating timestamp.

		repeat_quantity (Union[RepeatQuantity, None]): If set, what the quantity
		is of the repetition.

		repeat_interval (Union[int, None]): If set, the value of the repetition.

		weekdays (Union[List[int], None]): If set, on which days the time can
		continue. Monday is 0, Sunday is 6.

	Returns:
		int: The next timestamp in the future.
	"""
	if weekdays is not None:
		weekdays.sort()

	new_time = datetime.fromtimestamp(original_time)
	current_time = datetime.fromtimestamp(datetime.utcnow().timestamp())

	if repeat_quantity is not None:
		td = relativedelta(**{repeat_quantity.value: repeat_interval})
		while new_time <= current_time:
			new_time += td

	else:
		# We run the loop contents at least once and then actually use the cond.
		# This is because we need to force the 'free' date to go to one of the
		# selected weekdays.
		# Say it's Monday, we set a reminder for Wednesday and make it repeat
		# on Tuesday and Thursday. Then the first notification needs to go on
		# Thurday, not Wednesday. So run code at least once to force that.
		# Afterwards, it can run normally to push the timestamp into the future.
		one_to_go = True
		while one_to_go or new_time <= current_time:
			next_day = __next_selected_day(weekdays, new_time.weekday())
			proposed_time = new_time + relativedelta(weekday=du_weekday(next_day))
			if proposed_time == new_time:
				proposed_time += relativedelta(weekday=du_weekday(next_day, 2))
			new_time = proposed_time
			one_to_go = False

	result = int(new_time.timestamp())
	logging.debug(
		f'{original_time=}, {current_time=} ' +
		f'and interval of {repeat_interval} {repeat_quantity} ' +
		f'leads to {result}'
	)
	return result


class Reminder:
	"""Represents a reminder
	"""	
	def __init__(self, user_id: int, reminder_id: int) -> None:
		"""Create an instance.

		Args:
			user_id (int): The ID of the user.
			reminder_id (int): The ID of the reminder.

		Raises:
			ReminderNotFound: Reminder with given ID does not exist or is not
			owned by user.
		"""
		self.id = reminder_id

		# Check if reminder exists
		if not get_db().execute(
			"SELECT 1 FROM reminders WHERE id = ? AND user_id = ? LIMIT 1",
			(self.id, user_id)
		).fetchone():
			raise ReminderNotFound

		return

	def _get_notification_services(self) -> List[int]:
		"""Get ID's of notification services linked to the reminder.

		Returns:
			List[int]: The list with ID's.
		"""
		result = [
			r[0]
			for r in get_db().execute("""
				SELECT notification_service_id
				FROM reminder_services
				WHERE reminder_id = ?;
				""",
				(self.id,)
			)
		]
		return result

	def get(self) -> dict:
		"""Get info about the reminder

		Returns:
			dict: The info about the reminder
		"""
		reminder = get_db(dict).execute("""
			SELECT
				id,
				title, text,
				time,
				repeat_quantity,
				repeat_interval,
				weekdays,
				color
			FROM reminders
			WHERE id = ?
			LIMIT 1;
			""",
			(self.id,)
		).fetchone()
		reminder = dict(reminder)

		reminder["weekdays"] = [
			int(n)
			for n in reminder["weekdays"].split(",")
			if n
		] if reminder["weekdays"] else None
		reminder['notification_services'] = self._get_notification_services()

		return reminder

	def update(
		self,
		title: Union[None, str] = None,
		time: Union[None, int] = None,
		notification_services: Union[None, List[int]] = None,
		text: Union[None, str] = None,
		repeat_quantity: Union[None, RepeatQuantity] = None,
		repeat_interval: Union[None, int] = None,
		weekdays: Union[None, List[int]] = None,
		color: Union[None, str] = None
	) -> dict:
		"""Edit the reminder.

		Args:
			title (Union[None, str]): The new title of the entry.
				Defaults to None.

			time (Union[None, int]): The new UTC epoch timestamp when the
			reminder should be send.
				Defaults to None.

			notification_services (Union[None, List[int]]): The new list
			of id's of the notification services to use to send the reminder.
				Defaults to None.

			text (Union[None, str], optional): The new body of the reminder.
				Defaults to None.

			repeat_quantity (Union[None, RepeatQuantity], optional): The new
			quantity of the repeat specified for the reminder.
				Defaults to None.

			repeat_interval (Union[None, int], optional): The new amount of
			repeat_quantity, like "5" (hours).
				Defaults to None.

			weekdays (Union[None, List[int]], optional): The new indexes of
			the days of the week that the reminder should run.
				Defaults to None.

			color (Union[None, str], optional): The new hex code of the color
			of the reminder, which is shown in the web-ui.
				Defaults to None.

		Note about args:
			Either repeat_quantity and repeat_interval are given, weekdays is
			given or neither, but not both.

		Raises:
			NotificationServiceNotFound: One of the notification services was not found.
			InvalidKeyValue: The value of one of the keys is not valid or
			the "Note about args" is violated.

		Returns:
			dict: The new reminder info.
		"""
		logging.info(
			f'Updating notification service {self.id}: '
			+ f'{title=}, {time=}, {notification_services=}, {text=}, '
			+ f'{repeat_quantity=}, {repeat_interval=}, {weekdays=}, {color=}'
		)
		cursor = get_db()

		# Validate data
		if repeat_quantity is None and repeat_interval is not None:
			raise InvalidKeyValue('repeat_quantity', repeat_quantity)
		elif repeat_quantity is not None and repeat_interval is None:
			raise InvalidKeyValue('repeat_interval', repeat_interval)
		elif weekdays is not None and repeat_quantity is not None:
			raise InvalidKeyValue('weekdays', weekdays)

		repeated_reminder = (
			(repeat_quantity is not None and repeat_interval is not None)
			or weekdays is not None
		)

		if time is not None:
			if not repeated_reminder:
				if time < datetime.utcnow().timestamp():
					raise InvalidTime
			time = round(time)

		# Get current data and update it with new values
		data = self.get()
		new_values = {
			'title': title,
			'time': time,
			'text': text,
			'repeat_quantity': repeat_quantity,
			'repeat_interval': repeat_interval,
			'weekdays':
				",".join(map(str, sorted(weekdays)))
				if weekdays is not None else
				None,
			'color': color
		}
		for k, v in new_values.items():
			if (
				k in ('repeat_quantity', 'repeat_interval', 'weekdays', 'color')
				or v is not None
			):
				data[k] = v

		# Update database
		rq = (data["repeat_quantity"].value
			if data["repeat_quantity"] is not None else
			None)
		if repeated_reminder:
			next_time = _find_next_time(
				data["time"],
				data["repeat_quantity"],
				data["repeat_interval"],
				weekdays
			)
			cursor.execute("""
				UPDATE reminders
				SET
					title=?,
					text=?,
					time=?,
					repeat_quantity=?,
					repeat_interval=?,
					weekdays=?,
					original_time=?,
					color=?
				WHERE id = ?;
				""", (
					data["title"],
					data["text"],
					next_time,
					rq,
					data["repeat_interval"],
					data["weekdays"],
					data["time"],
					data["color"],
					self.id
			))

		else:
			next_time = data["time"]
			cursor.execute("""
				UPDATE reminders
				SET
					title=?,
					text=?,
					time=?,
					repeat_quantity=?,
					repeat_interval=?,
					weekdays=?,
					color=?
				WHERE id = ?;
				""", (
					data["title"],
					data["text"],
					data["time"],
					rq,
					data["repeat_interval"],
					data["weekdays"],
					data["color"],
					self.id
			))

		if notification_services:
			cursor.connection.isolation_level = None
			cursor.execute("BEGIN TRANSACTION;")
			cursor.execute(
				"DELETE FROM reminder_services WHERE reminder_id = ?",
				(self.id,)
			)
			try:
				cursor.executemany("""
					INSERT INTO reminder_services(
						reminder_id,
						notification_service_id
					)
					VALUES (?,?);
					""",
					((self.id, s) for s in notification_services)
				)
				cursor.execute("COMMIT;")

			except IntegrityError:
				raise NotificationServiceNotFound

			finally:
				cursor.connection.isolation_level = ""

		ReminderHandler().find_next_reminder(next_time)
		return self.get()

	def delete(self) -> None:
		"""Delete the reminder
		"""
		logging.info(f'Deleting reminder {self.id}')
		get_db().execute("DELETE FROM reminders WHERE id = ?", (self.id,))
		ReminderHandler().find_next_reminder()
		return

class Reminders:
	"""Represents the reminder library of the user account
	"""

	def __init__(self, user_id: int) -> None:
		"""Create an instance.

		Args:
			user_id (int): The ID of the user.
		"""
		self.user_id = user_id
		return

	def fetchall(
		self,
		sort_by: SortingMethod = SortingMethod.TIME
	) -> List[dict]:
		"""Get all reminders

		Args:
			sort_by (SortingMethod, optional): How to sort the result.
				Defaults to SortingMethod.TIME.

		Returns:
			List[dict]: The id, title, text, time and color of each reminder
		"""
		reminders = [
			dict(r)
			for r in get_db(dict).execute("""
				SELECT
					id,
					title, text,
					time,
					repeat_quantity,
					repeat_interval,
					weekdays,
					color
				FROM reminders
				WHERE user_id = ?;
				""",
				(self.user_id,)
			)
		]
		for r in reminders:
			r["weekdays"] = [
				int(n)
				for n in r["weekdays"].split(",")
				if n
			] if r["weekdays"] else None

		# Sort result
		reminders.sort(key=sort_by.value[0], reverse=sort_by.value[1])

		return reminders

	def search(
		self,
		query: str,
		sort_by: SortingMethod = SortingMethod.TIME) -> List[dict]:
		"""Search for reminders

		Args:
			query (str): The term to search for.
			sort_by (SortingMethod, optional): How to sort the result.
				Defaults to SortingMethod.TIME.

		Returns:
			List[dict]: All reminders that match. Similar output to self.fetchall
		"""
		reminders = [
			r for r in self.fetchall(sort_by)
			if search_filter(query, r)
		]
		return reminders

	def fetchone(self, id: int) -> Reminder:
		"""Get one reminder

		Args:
			id (int): The id of the reminder to fetch

		Returns:
			Reminder: A Reminder instance
		"""		
		return Reminder(self.user_id, id)

	def add(
		self,
		title: str,
		time: int,
		notification_services: List[int],
		text: str = '',
		repeat_quantity: Union[None, RepeatQuantity] = None,
		repeat_interval: Union[None, int] = None,
		weekdays: Union[None, List[int]] = None,
		color: Union[None, str] = None
	) -> Reminder:
		"""Add a reminder

		Args:
			title (str): The title of the entry.

			time (int): The UTC epoch timestamp the the reminder should be send.

			notification_services (List[int]): The id's of the notification services
			to use to send the reminder.

			text (str, optional): The body of the reminder.
				Defaults to ''.

			repeat_quantity (Union[None, RepeatQuantity], optional): The quantity
			of the repeat specified for the reminder.
				Defaults to None.

			repeat_interval (Union[None, int], optional): The amount of repeat_quantity,
			like "5" (hours).
				Defaults to None.

			weekdays (Union[None, List[int]], optional): The indexes of the days
			of the week that the reminder should run.
				Defaults to None.

			color (Union[None, str], optional): The hex code of the color of the
			reminder, which is shown in the web-ui.
				Defaults to None.

		Note about args:
			Either repeat_quantity and repeat_interval are given,
			weekdays is given or neither, but not both.

		Raises:
			NotificationServiceNotFound: One of the notification services was not found.
			InvalidKeyValue: The value of one of the keys is not valid
			or the "Note about args" is violated.

		Returns:
			dict: The info about the reminder.
		"""
		logging.info(
			f'Adding reminder with {title=}, {time=}, {notification_services=}, '
			+ f'{text=}, {repeat_quantity=}, {repeat_interval=}, {weekdays=}, {color=}'
		)
		
		if time < datetime.utcnow().timestamp():
			raise InvalidTime
		time = round(time)

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

		cursor = get_db()
		for service in notification_services:
			if not cursor.execute("""
				SELECT 1
				FROM notification_services
				WHERE id = ?
					AND user_id = ?
				LIMIT 1;
				""",
				(service, self.user_id)
			).fetchone():
				raise NotificationServiceNotFound

		# Prepare args
		if any((repeat_quantity, weekdays)):
			original_time = time
			time = _find_next_time(
				original_time,
				repeat_quantity,
				repeat_interval,
				weekdays
			)
		else:
			original_time = None

		if weekdays is not None:
			weekdays = ",".join(map(str, sorted(weekdays)))

		if repeat_quantity is not None:
			repeat_quantity = repeat_quantity.value

		cursor.connection.isolation_level = None
		cursor.execute("BEGIN TRANSACTION;")

		id = cursor.execute("""
			INSERT INTO reminders(
				user_id,
				title, text,
				time,
				repeat_quantity, repeat_interval,
				weekdays,
				original_time,
				color
			)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
			""", (
				self.user_id,
				title, text,
				time,
				repeat_quantity,
				repeat_interval,
				weekdays,
				original_time,
				color
		)).lastrowid

		try:
			cursor.executemany("""
				INSERT INTO reminder_services(
					reminder_id,
					notification_service_id
				)
				VALUES (?, ?);
				""",
				((id, service) for service in notification_services)
			)
			cursor.execute("COMMIT;")

		except IntegrityError:
			raise NotificationServiceNotFound

		finally:
			cursor.connection.isolation_level = ''
		
		ReminderHandler().find_next_reminder(time)

		return self.fetchone(id)

	def test_reminder(
		self,
		title: str,
		notification_services: List[int],
		text: str = ''
	) -> None:
		"""Test send a reminder draft.

		Args:
			title (str): Title title of the entry.

			notification_service (int): The id of the notification service to
			use to send the reminder.

			text (str, optional): The body of the reminder.
				Defaults to ''.
		"""
		logging.info(f'Testing reminder with {title=}, {notification_services=}, {text=}')
		a = Apprise()
		cursor = get_db(dict)

		for service in notification_services:
			url = cursor.execute("""
				SELECT url
				FROM notification_services
				WHERE id = ?
					AND user_id = ?
				LIMIT 1;
				""",
				(service, self.user_id)
			).fetchone()
			if not url:
				raise NotificationServiceNotFound
			a.add(url[0])

		a.notify(title=title, body=text)
		return


class ReminderHandler(metaclass=Singleton):
	"""Handle set reminders.
	
	Note: Singleton.
	"""	
	def __init__(self, context) -> None:
		"""Create instance of handler.

		Args:
			context (AppContext): `Flask.app_context`
		"""
		self.context = context
		self.thread: Union[Timer, None] = None
		self.time: Union[int, None] = None
		return

	def __trigger_reminders(self, time: int) -> None:
		"""Trigger all reminders that are set for a certain time

		Args:
			time (int): The time of the reminders to trigger
		"""
		with self.context():
			cursor = get_db(dict)
			reminders = [
				dict(r)
				for r in cursor.execute("""
					SELECT
						id, user_id,
						title, text,
						repeat_quantity, repeat_interval,
						weekdays,
						original_time
					FROM reminders
					WHERE time = ?;
					""",
					(time,)
				)
			]
			
			for reminder in reminders:
				cursor.execute("""
					SELECT url
					FROM reminder_services rs
					INNER JOIN notification_services ns
					ON rs.notification_service_id = ns.id
					WHERE rs.reminder_id = ?;
					""",
					(reminder['id'],)
				)

				# Send reminder
				a = Apprise()
				for url in cursor:
					a.add(url['url'])
				a.notify(title=reminder["title"], body=reminder["text"])

				self.thread = None
				self.time = None

				if (reminder['repeat_quantity'], reminder['weekdays']) == (None, None):
					# Delete the reminder from the database
					Reminder(reminder["user_id"], reminder["id"]).delete()

				else:
					# Set next time
					new_time = _find_next_time(
						reminder['original_time'],
						RepeatQuantity(reminder['repeat_quantity']),
						reminder['repeat_interval'],
						[int(d) for d in reminder['weekdays'].split(',')]
						if reminder['weekdays'] is not None else
						None
					)
					cursor.execute(
						"UPDATE reminders SET time = ? WHERE id = ?;",
						(new_time, reminder['id'])
					)

				self.find_next_reminder()
			return

	def find_next_reminder(self, time: int=None) -> None:
		"""Determine when the soonest reminder is and set the timer to that time

		Args:
			time (int, optional): The timestamp to check for.
			Otherwise check soonest in database.
				Defaults to None.
		"""
		if not time:
			with self.context():
				time = get_db().execute("""
					SELECT DISTINCT r1.time
					FROM reminders r1
					LEFT JOIN reminders r2
					ON r1.time > r2.time
					WHERE r2.id IS NULL;
				""").fetchone()
				if time is None:
					return
				time = time[0]

		if (
			self.thread is None
			or time < self.time
		):
			if self.thread is not None:
				self.thread.cancel()

			t = time - datetime.utcnow().timestamp()
			self.thread = Timer(
				t,
				self.__trigger_reminders,
				(time,)
			)
			self.thread.name = "ReminderHandler"
			self.thread.start()
			self.time = time

		return
	
	def stop_handling(self) -> None:
		"""Stop the timer if it's active
		"""
		if self.thread is not None:
			self.thread.cancel()
		return
