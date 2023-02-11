#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from os import makedirs, urandom
from os.path import abspath, dirname, join, isfile
from shutil import move
from sys import version_info

from flask import Flask, render_template, request
from waitress.server import create_server

from backend.db import DBConnection, close_db, setup_db
from frontend.api import api, reminder_handler
from frontend.ui import ui

HOST = '0.0.0.0'
PORT = '8080'
THREADS = 10
DB_FILENAME = 'db', 'MIND.db'

def _folder_path(*folders) -> str:
	"""Turn filepaths relative to the project folder into absolute paths
	Returns:
		str: The absolute filepath
	"""
	return join(dirname(abspath(__file__)), *folders)

def _create_app() -> Flask:
	"""Create a Flask app instance
	Returns:
		Flask: The created app instance
	""" 
	app = Flask(
		__name__,
		template_folder=_folder_path('frontend','templates'),
		static_folder=_folder_path('frontend','static'),
		static_url_path='/static'
	)
	app.config['SECRET_KEY'] = urandom(32)
	app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
	app.config['JSON_SORT_KEYS'] = False

	# Add error handlers
	@app.errorhandler(404)
	def not_found(e):
		if request.path.startswith('/api'):
			return {'error': 'Not Found', 'result': {}}, 404
		else:
			return render_template('page_not_found.html')

	@app.errorhandler(400)
	def bad_request(e):
		return {'error': 'Bad request', 'result': {}}, 400

	@app.errorhandler(405)
	def method_not_allowed(e):
		return {'error': 'Method not allowed', 'result': {}}, 405

	@app.errorhandler(500)
	def internal_error(e):
		return {'error': 'Internal error', 'result': {}}, 500

	app.register_blueprint(ui)
	app.register_blueprint(api, url_prefix="/api")

	# Setup closing database
	app.teardown_appcontext(close_db)
	
	return app

def MIND() -> None:
	"""The main function of MIND
	Returns:
		None
	"""
	# Check python version
	if (version_info.major < 3) or (version_info.major == 3 and version_info.minor < 7):
		print('Error: the minimum python version required is python3.7 (currently ' + version_info.major + '.' + version_info.minor + '.' + version_info.micro + ')')

	# Register web server
	app = _create_app()
	with app.app_context():
		if isfile(_folder_path('db', 'Noted.db')):
			move(_folder_path('db', 'Noted.db'), _folder_path('db', 'MIND.db'))
		db_location = _folder_path(*DB_FILENAME)
		makedirs(dirname(db_location), exist_ok=True)
		DBConnection.file = db_location
		setup_db()
		reminder_handler._find_next_reminder()

	# Start thread
	reminder_handler.thread.start()

	# Create waitress server and run
	server = create_server(app, host=HOST, port=PORT, threads=THREADS)
	print(f'MIND running on http://{HOST}:{PORT}/')
	server.run()
	print(f'\nShutting down MIND...')
	
	# Stopping thread
	reminder_handler.stop_handling()

	print('Bye')
	return

if __name__ == "__main__":
	MIND()
