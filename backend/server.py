#-*- coding: utf-8 -*-

from __future__ import annotations

from os import execv, urandom
from sys import argv
from threading import Timer, current_thread
from typing import TYPE_CHECKING, List, NoReturn, Union

from flask import Flask, render_template, request
from waitress import create_server
from waitress.task import ThreadedTaskDispatcher as TTD
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from backend.db import DB_Singleton, DBConnection, close_db, revert_db_import
from backend.helpers import RestartVars, Singleton, folder_path
from backend.logging import LOGGER
from backend.settings import restore_hosting_settings

if TYPE_CHECKING:
	from waitress.server import TcpWSGIServer

THREADS = 10

class ThreadedTaskDispatcher(TTD):
	def handler_thread(self, thread_no: int) -> None:
		super().handler_thread(thread_no)
		i = f'{DBConnection}{current_thread()}'
		if i in DB_Singleton._instances and not DB_Singleton._instances[i].closed:
			DB_Singleton._instances[i].close()
		return

	def shutdown(self, cancel_pending: bool = True, timeout: int = 5) -> bool:
		print()
		LOGGER.info('Shutting down MIND')
		result = super().shutdown(cancel_pending, timeout)
		DBConnection(timeout=20.0).close()
		return result


class Server(metaclass=Singleton):
	api_prefix = "/api"
	admin_api_extension = "/admin"
	admin_prefix = "/api/admin"

	def __init__(self) -> None:
		self.do_restart = False
		"Restart instead of shutdown"

		self.restart_args: List[str] = []
		"Flag to run with when restarting"

		self.handle_flags: bool = False
		"Run any flag specific actions before restarting"

		self.url_prefix = ""

		self.revert_db_timer = Timer(60.0, self.__revert_db)
		self.revert_db_timer.name = "DatabaseImportHandler"
		self.revert_hosting_timer = Timer(60.0, self.__revert_hosting)
		self.revert_hosting_timer.name = "HostingHandler"

		return

	def create_app(self) -> None:
		"""Create a Flask app instance"""
		from frontend.api import admin_api, api
		from frontend.ui import ui

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
			if request.path.startswith(self.api_prefix):
				return {'error': 'Not Found', 'result': {}}, 404
			return render_template('page_not_found.html', url_prefix=self.url_prefix)

		app.register_blueprint(ui)
		app.register_blueprint(api, url_prefix=self.api_prefix)
		app.register_blueprint(admin_api, url_prefix=self.admin_prefix)

		# Setup closing database
		app.teardown_appcontext(close_db)

		self.app = app
		return

	def set_url_prefix(self, url_prefix: str) -> None:
		"""Change the URL prefix of the server.

		Args:
			url_prefix (str): The desired URL prefix to set it to.
		"""
		self.app.config["APPLICATION_ROOT"] = url_prefix
		self.app.wsgi_app = DispatcherMiddleware(
			Flask(__name__),
			{url_prefix: self.app.wsgi_app}
		)
		self.url_prefix = url_prefix
		return

	def __create_waitress_server(
		self,
		host: str,
		port: int
	) -> TcpWSGIServer:
		"""From the `Flask` instance created in `self.create_app()`, create
		a waitress server instance.

		Args:
			host (str): The host to bind to.
			port (int): The port to listen on.

		Returns:
			TcpWSGIServer: The waitress server.
		"""
		dispatcher = ThreadedTaskDispatcher()
		dispatcher.set_thread_count(THREADS)
		server = create_server(
			self.app,
			_dispatcher=dispatcher,
			host=host,
			port=port,
			threads=THREADS
		)
		return server

	def run(self, host: str, port: int) -> None:
		"""Start the webserver.

		Args:
			host (str): The host to bind to.
			port (int): The port to listen on.
		"""
		self.server = self.__create_waitress_server(host, port)
		LOGGER.info(f'MIND running on http://{host}:{port}{self.url_prefix}')
		self.server.run()

		return

	def __shutdown_thread_function(self) -> None:
		"""Shutdown waitress server. Intended to be run in a thread.
		"""
		self.server.close()
		self.server.task_dispatcher.shutdown()
		self.server._map.clear()
		return

	def shutdown(self) -> None:
		"""Stop the waitress server. Starts a thread that
		shuts down the server.
		"""
		t = Timer(1.0, self.__shutdown_thread_function)
		t.name = "InternalStateHandler"
		t.start()
		return

	def restart(
		self,
		restart_args: List[str] = [],
		handle_flags: bool = False
	) -> None:
		"""Same as `self.shutdown()`, but restart instead of shutting down.

		Args:
			restart_args (List[str], optional): Any arguments to run the new instance with.
				Defaults to [].

			handle_flags (bool, optional): Run flag specific actions just before restarting.
				Defaults to False.
		"""		
		self.do_restart = True
		self.restart_args = restart_args
		self.handle_flags = handle_flags
		self.shutdown()
		return

	def handle_restart(self, flag: Union[str, None]) -> NoReturn:
		"""Restart the interpreter.

		Args:
			flag (Union[str, None]): Supplied flag, for flag handling.

		Returns:
			NoReturn: No return because it replaces the interpreter.
		"""
		if self.handle_flags:
			handle_flags_pre_restart(flag)

		LOGGER.info('Restarting MIND')
		from MIND import __file__ as mind_file
		execv(folder_path(mind_file), [argv[0], *self.restart_args])

	def __revert_db(self) -> None:
		"""Revert database import and restart.
		"""
		LOGGER.warning(f'Timer for database import expired; reverting back to original file')
		self.restart(handle_flags=True)
		return

	def __revert_hosting(self) -> None:
		"""Revert the hosting changes.
		"""
		LOGGER.warning(f'Timer for hosting changes expired; reverting back to original settings')
		self.restart(handle_flags=True)
		return


SERVER = Server()


def handle_flags(flag: Union[None, str]) -> None:
	"""Run flag specific actions on startup.

	Args:
		flag (Union[None, str]): The flag or `None` if there is no flag set.
	"""
	if flag == RestartVars.DB_IMPORT:
		LOGGER.info('Starting timer for database import')
		SERVER.revert_db_timer.start()

	elif flag == RestartVars.HOST_CHANGE:
		LOGGER.info('Starting timer for hosting changes')
		SERVER.revert_hosting_timer.start()

	return


def handle_flags_pre_restart(flag: Union[None, str]) -> None:
	"""Run flag specific actions just before restarting.

	Args:
		flag (Union[None, str]): The flag or `None` if there is no flag set.
	"""
	if flag == RestartVars.DB_IMPORT:
		revert_db_import(swap=True)

	elif flag == RestartVars.HOST_CHANGE:
		with SERVER.app.app_context():
			restore_hosting_settings()
			close_db()

	return
