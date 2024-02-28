#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
The main file where MIND is started from
"""

import logging
from os import execv, makedirs, urandom
from os.path import dirname, isfile
from shutil import move
from sys import argv
from typing import Union

from flask import Flask, render_template, request
from waitress.server import create_server
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from backend.db import (DBConnection, ThreadedTaskDispatcher, close_db,
                        revert_db_import, setup_db)
from backend.helpers import RestartVars, check_python_version, folder_path
from backend.reminders import ReminderHandler
from backend.settings import get_setting, restore_hosting_settings
from frontend.api import (APIVariables, admin_api, admin_api_prefix, api,
                          api_prefix, revert_db_thread, revert_hosting_thread)
from frontend.ui import UIVariables, ui

#=============================
# WARNING:
# These settings have moved into the admin panel. Their current value has been
# taken over. The values will from now on be ignored, and the variables will
# be deleted next version.
HOST = '0.0.0.0'
PORT = '8080'
URL_PREFIX = '' # Must either be empty or start with '/' e.g. '/mind' 
#=============================

LOGGING_LEVEL = logging.INFO
THREADS = 10
DB_FILENAME = 'db', 'MIND.db'

logging.basicConfig(
	level=LOGGING_LEVEL,
	format='[%(asctime)s][%(threadName)s][%(levelname)s] %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S'
)

def _create_app() -> Flask:
	"""Create a Flask app instance

	Returns:
		Flask: The created app instance
	"""	
	app = Flask(
		__name__,
		template_folder=folder_path('frontend','templates'),
		static_folder=folder_path('frontend','static'),
		static_url_path='/static'
	)
	app.config['SECRET_KEY'] = urandom(32)
	app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
	app.config['JSON_SORT_KEYS'] = False

	# Add error handlers
	@app.errorhandler(400)
	def bad_request(e):
		return {'error': 'Bad request', 'result': {}}, 400

	@app.errorhandler(405)
	def method_not_allowed(e):
		return {'error': 'Method not allowed', 'result': {}}, 405

	@app.errorhandler(500)
	def internal_error(e):
		return {'error': 'Internal error', 'result': {}}, 500
	
	@app.errorhandler(404)
	def not_found(e):
		if request.path.startswith(api_prefix):
			return {'error': 'Not Found', 'result': {}}, 404
		return render_template('page_not_found.html', url_prefix=UIVariables.url_prefix)

	app.register_blueprint(ui)
	app.register_blueprint(api, url_prefix=api_prefix)
	app.register_blueprint(admin_api, url_prefix=admin_api_prefix)

	# Setup closing database
	app.teardown_appcontext(close_db)
	
	return app

def _set_url_prefix(app: Flask, url_prefix: str) -> None:
	"""Change the URL prefix of the server.

	Args:
		app (Flask): The `Flask` instance to change the URL prefix of.
		url_prefix (str): The desired URL prefix to set it to.
	"""
	app.config["APPLICATION_ROOT"] = url_prefix
	app.wsgi_app = DispatcherMiddleware(
		Flask(__name__),
		{url_prefix: app.wsgi_app}
	)
	UIVariables.url_prefix = url_prefix
	return

def _handle_flags(flag: Union[None, str]) -> None:
	"""Run flag specific actions on startup.

	Args:
		flag (Union[None, str]): The flag or `None` if there is no flag set.
	"""
	if flag == RestartVars.DB_IMPORT:
		logging.info('Starting timer for database import')
		revert_db_thread.start()

	elif flag == RestartVars.HOST_CHANGE:
		logging.info('Starting timer for hosting changes')
		revert_hosting_thread.start()

	return

def _handle_flags_pre_restart(flag: Union[None, str]) -> None:
	"""Run flag specific actions just before restarting.

	Args:
		flag (Union[None, str]): The flag or `None` if there is no flag set.
	"""
	if flag == RestartVars.DB_IMPORT:
		revert_db_import(swap=True)

	elif flag == RestartVars.HOST_CHANGE:
		with Flask(__name__).app_context():
			restore_hosting_settings()
			close_db()

	return

def MIND() -> None:
	"""The main function of MIND
	"""
	logging.info('Starting up MIND')

	if not check_python_version():
		exit(1)

	flag = argv[1] if len(argv) > 1 else None
	_handle_flags(flag)

	if isfile(folder_path('db', 'Noted.db')):
		move(folder_path('db', 'Noted.db'), folder_path(*DB_FILENAME))

	db_location = folder_path(*DB_FILENAME)
	logging.debug(f'Database location: {db_location}')
	makedirs(dirname(db_location), exist_ok=True)

	DBConnection.file = db_location

	app = _create_app()
	reminder_handler = ReminderHandler(app.app_context)
	with app.app_context():
		setup_db()

		host = get_setting("host")
		port = get_setting("port")
		url_prefix = get_setting("url_prefix")
		_set_url_prefix(app, url_prefix)

		reminder_handler.find_next_reminder()

	# Create waitress server and run
	dispatcher = ThreadedTaskDispatcher()
	dispatcher.set_thread_count(THREADS)
	server = create_server(
		app,
		_dispatcher=dispatcher,
		host=host,
		port=port,
		threads=THREADS
	)
	APIVariables.server_instance = server
	logging.info(f'MIND running on http://{host}:{port}{url_prefix}')
	# =================
	server.run()
	# =================

	reminder_handler.stop_handling()

	if APIVariables.restart:
		if APIVariables.handle_flags:
			_handle_flags_pre_restart(flag)

		logging.info('Restarting MIND')
		execv(__file__, [argv[0], *APIVariables.restart_args])

	return

if __name__ == "__main__":
	MIND()
