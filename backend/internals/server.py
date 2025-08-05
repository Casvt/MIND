# -*- coding: utf-8 -*-

"""
Setting up, running and shutting down the API and web-ui
"""

from __future__ import annotations

from os import urandom
from threading import Timer
from typing import TYPE_CHECKING, Any, Callable, Iterable, Mapping, Union

from flask import Flask, request
from waitress.server import create_server
from waitress.task import ThreadedTaskDispatcher as TTD
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from backend.base.definitions import Constants, StartType
from backend.base.helpers import Singleton, folder_path
from backend.base.logging import LOGGER
from backend.internals.db import DBConnectionManager, close_db
from backend.internals.db_backup_import import revert_db_import
from backend.internals.settings import Settings

if TYPE_CHECKING:
    from waitress.server import BaseWSGIServer, MultiSocketServer


class ThreadedTaskDispatcher(TTD):
    def __init__(self) -> None:
        super().__init__()

        # The DB connection should be closed when the thread is ending, but
        # right before it actually has. Waitress will consider a thread closed
        # once it's not in the self.threads set anymore, regardless of whether
        # the thread has actually ended/joined, so anything we do after that
        # could be cut short by the main thread ending. So we need to close
        # the DB connection before the thread is discarded from the set.
        class TDDSet(set):
            def discard(self, element: Any) -> None:
                DBConnectionManager.close_connection_of_thread()
                return super().discard(element)

        self.threads = TDDSet()
        return

    def shutdown(self, cancel_pending: bool = True, timeout: int = 5) -> bool:
        print()
        LOGGER.info('Shutting down MIND')
        result = super().shutdown(cancel_pending, timeout)
        return result


def handle_start_type(start_type: StartType) -> None:
    """Do special actions needed based on restart version.

    Args:
        start_type (StartType): The restart version.
    """
    if start_type == StartType.RESTART_HOSTING_CHANGES:
        LOGGER.info("Starting timer for hosting changes")
        Server().revert_hosting_timer.start()

    elif start_type == StartType.RESTART_DB_CHANGES:
        LOGGER.info("Starting timer for database import")
        Server().revert_db_timer.start()

    return


def diffuse_timers() -> None:
    """Stop any timers running after doing a special restart."""

    SERVER = Server()

    if SERVER.revert_hosting_timer.is_alive():
        LOGGER.info("Timer for hosting changes diffused")
        SERVER.revert_hosting_timer.cancel()

    elif SERVER.revert_db_timer.is_alive():
        LOGGER.info("Timer for database import diffused")
        SERVER.revert_db_timer.cancel()
        revert_db_import(swap=False)

    return


class Server(metaclass=Singleton):
    api_prefix = "/api"
    admin_api_extension = "/admin"
    admin_prefix = "/api/admin"
    url_prefix = ''

    def __init__(self) -> None:
        self.start_type = None

        self.revert_db_timer = self.get_db_timer_thread(
            Constants.DB_REVERT_TIME,
            revert_db_import,
            "DatabaseImportHandler",
            kwargs={"swap": True}
        )

        self.revert_hosting_timer = self.get_db_timer_thread(
            Constants.HOSTING_REVERT_TIME,
            self.restore_hosting_settings,
            "HostingHandler"
        )

        return

    def create_app(self) -> None:
        """Creates an flask app instance that can be used to start a web server"""

        from frontend.api import admin_api, api
        from frontend.ui import render, ui

        app = Flask(
            __name__,
            template_folder=folder_path('frontend', 'templates'),
            static_folder=folder_path('frontend', 'static'),
            static_url_path='/static'
        )
        app.config['SECRET_KEY'] = urandom(32)
        app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
        app.config['JSON_SORT_KEYS'] = False

        # Add error handlers
        @app.errorhandler(400)
        def bad_request(e):
            return {'error': "BadRequest", "result": {}}, 400

        @app.errorhandler(404)
        def not_found(e):
            if request.path.startswith((self.api_prefix, self.admin_prefix)):
                return {'error': "NotFound", "result": {}}, 404
            return render("page_not_found.html")

        @app.errorhandler(405)
        def method_not_allowed(e):
            return {'error': "MethodNotAllowed", "result": {}}, 405

        @app.errorhandler(500)
        def internal_error(e):
            return {'error': "InternalError", "result": {}}, 500

        # Add endpoints
        app.register_blueprint(ui)
        app.register_blueprint(api, url_prefix=self.api_prefix)
        app.register_blueprint(admin_api, url_prefix=self.admin_prefix)

        # Setup db handling
        app.teardown_appcontext(close_db)

        self.app = app
        return

    def set_url_prefix(self, url_prefix: str) -> None:
        """Change the URL prefix of the server.

        Args:
            url_prefix (str): The desired URL prefix to set it to.
        """
        self.app.config["APPLICATION_ROOT"] = url_prefix
        self.app.wsgi_app = DispatcherMiddleware( # type: ignore
            Flask(__name__),
            {url_prefix: self.app.wsgi_app}
        )
        self.url_prefix = url_prefix
        return

    def __create_waitress_server(
        self,
        host: str,
        port: int
    ) -> Union[MultiSocketServer, BaseWSGIServer]:
        """From the `Flask` instance created in `self.create_app()`, create
        a waitress server instance.

        Args:
            host (str): Where to host the server on (e.g. `0.0.0.0`).
            port (int): The port to host the server on (e.g. `5656`).

        Returns:
            Union[MultiSocketServer, BaseWSGIServer]: The waitress server instance.
        """
        dispatcher = ThreadedTaskDispatcher()
        dispatcher.set_thread_count(Constants.HOSTING_THREADS)

        server = create_server(
            self.app,
            _dispatcher=dispatcher,
            host=host,
            port=port,
            threads=Constants.HOSTING_THREADS
        )
        return server

    def run(self, host: str, port: int) -> None:
        """Start the webserver.

        Args:
            host (str): Where to host the server on (e.g. `0.0.0.0`).
            port (int): The port to host the server on (e.g. `5656`).
        """
        self.server = self.__create_waitress_server(host, port)
        LOGGER.info(f'MIND running on http://{host}:{port}{self.url_prefix}')
        self.server.run()

        return

    def __shutdown_thread_function(self) -> None:
        """Shutdown waitress server. Intended to be run in a thread.
        """
        if not hasattr(self, 'server'):
            return

        self.server.task_dispatcher.shutdown()
        self.server.close()
        self.server._map.clear() # type: ignore
        return

    def shutdown(self) -> None:
        """
        Stop the waitress server. Starts a thread that shuts down the server.
        """
        self.get_db_timer_thread(
            1.0,
            self.__shutdown_thread_function,
            "InternalStateHandler"
        ).start()
        return

    def restart(
        self,
        start_type: StartType = StartType.STARTUP
    ) -> None:
        """Same as `self.shutdown()`, but restart instead of shutting down.

        Args:
            start_type (StartType, optional): Why Kapowarr should
            restart.
                Defaults to StartType.STARTUP.
        """
        self.start_type = start_type
        self.shutdown()
        return

    def restore_hosting_settings(self) -> None:
        "Restore the hosting settings from the backup, and restart."
        settings = Settings()
        values = settings.get_settings()
        main_settings = {
            'host': values.backup_host,
            'port': values.backup_port,
            'url_prefix': values.backup_url_prefix
        }
        settings.update(main_settings)
        self.restart()
        return

    def get_db_timer_thread(
        self,
        interval: float,
        target: Callable[..., object],
        name: Union[str, None] = None,
        args: Iterable[Any] = (),
        kwargs: Mapping[str, Any] = {}
    ) -> Timer:
        """Create a timer thread that runs under Flask app context.

        Args:
            interval (float): The time to wait before running the target.

            target (Callable[..., object]): The function to run in the thread.

            name (Union[str, None], optional): The name of the thread.
                Defaults to None.

            args (Iterable[Any], optional): The arguments to pass to the function.
                Defaults to ().

            kwargs (Mapping[str, Any], optional): The keyword arguments to pass
            to the function.
                Defaults to {}.

        Returns:
            Timer: The timer thread instance.
        """
        def db_thread(*args, **kwargs) -> None:
            with self.app.app_context():
                target(*args, **kwargs)

            DBConnectionManager.close_connection_of_thread()
            return

        t = Timer(
            interval=interval,
            function=db_thread,
            args=args,
            kwargs=kwargs
        )
        if name:
            t.name = name
        return t
