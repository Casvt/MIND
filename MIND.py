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

from flask import Flask, render_template, request
from waitress.server import create_server
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from backend.db import DBConnection, ThreadedTaskDispatcher, close_db, setup_db
from backend.helpers import check_python_version, folder_path
from backend.reminders import ReminderHandler
from frontend.api import (APIVariables, admin_api, admin_api_prefix, api,
                          api_prefix)
from frontend.ui import UIVariables, ui

HOST = '0.0.0.0'
PORT = '8080'
URL_PREFIX = '' # Must either be empty or start with '/' e.g. '/mind' 
LOGGING_LEVEL = logging.INFO
THREADS = 10
DB_FILENAME = 'db', 'MIND.db'

UIVariables.url_prefix = URL_PREFIX
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
	app.config['APPLICATION_ROOT'] = URL_PREFIX
	app.wsgi_app = DispatcherMiddleware(
		Flask(__name__),
		{URL_PREFIX: app.wsgi_app}
	)

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

def MIND() -> None:
	"""The main function of MIND
	"""
	logging.info('Starting up MIND')

	if not check_python_version():
		exit(1)
	
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
		reminder_handler.find_next_reminder()

	# Create waitress server and run
	dispatcher = ThreadedTaskDispatcher()
	dispatcher.set_thread_count(THREADS)
	server = create_server(
		app,
		_dispatcher=dispatcher,
		host=HOST,
		port=PORT,
		threads=THREADS
	)
	APIVariables.server_instance = server
	logging.info(f'MIND running on http://{HOST}:{PORT}{URL_PREFIX}')
	# =================
	server.run()
	# =================

	reminder_handler.stop_handling()

	if APIVariables.restart:
		logging.info('Restarting MIND')
		execv(__file__, argv)

	return

if __name__ == "__main__":
	MIND()
