#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
The main file where MIND is started from
"""

from sys import argv

from backend.db import setup_db, setup_db_location
from backend.helpers import check_python_version
from backend.logging import LOGGER, setup_logging
from backend.reminders import ReminderHandler
from backend.server import SERVER, handle_flags
from backend.settings import get_setting

#=============================
# WARNING:
# These settings have moved into the admin panel. Their current value has been
# taken over. The values will from now on be ignored, and the variables will
# be deleted next version.
HOST = '0.0.0.0'
PORT = '8080'
URL_PREFIX = '' # Must either be empty or start with '/' e.g. '/mind' 
#=============================

def MIND() -> None:
	"""The main function of MIND
	"""
	setup_logging()
	LOGGER.info('Starting up MIND')

	if not check_python_version():
		exit(1)

	flag = argv[1] if len(argv) > 1 else None
	handle_flags(flag)

	setup_db_location()

	SERVER.create_app()
	reminder_handler = ReminderHandler(SERVER.app.app_context)
	with SERVER.app.app_context():
		setup_db()

		host = get_setting("host")
		port = get_setting("port")
		url_prefix = get_setting("url_prefix")
		SERVER.set_url_prefix(url_prefix)

		reminder_handler.find_next_reminder()

	# =================
	SERVER.run(host, port)
	# =================

	reminder_handler.stop_handling()

	if SERVER.do_restart:
		SERVER.handle_restart(flag)

	return

if __name__ == "__main__":
	MIND()
