# -*- coding: utf-8 -*-

"""
Setting up, running and shutting down the webserver.
Also handling startup types.
"""

from __future__ import annotations

from os import urandom
from threading import Timer
from typing import Any, Callable, Iterable, Mapping, Union

from flask import Flask, request
from flask.json.provider import DefaultJSONProvider
from waitress.server import create_server
from waitress.task import ThreadedTaskDispatcher as TTD
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from backend.base.custom_exceptions import (BadRequest, InternalError,
                                            LogUnauthMindException,
                                            MethodNotAllowed, NotFound)
from backend.base.definitions import (Constants, MindException,
                                      StartType, StartTypeHandler)
from backend.base.helpers import Singleton, folder_path, return_api
from backend.base.logging import LOGGER
from backend.internals.db import DBConnectionManager, close_db
from backend.internals.db_backup_import import revert_db_import
from backend.internals.settings import Settings


# region Thread Manager
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


# region Server
class Server(metaclass=Singleton):
    url_prefix = ''

    def __init__(self) -> None:
        self.__start_type = None
        self.app = self._create_app()
        return

    @staticmethod
    def _create_app() -> Flask:
        """Creates a flask app instance that can be used to start a web server.

        Returns:
            Flask: The instance.
        """
        from frontend.api import admin_api, api
        from frontend.ui import render, ui

        app = Flask(
            __name__,
            template_folder=folder_path('frontend', 'templates'),
            static_folder=folder_path('frontend', 'static'),
            static_url_path='/static'
        )
        app.config['SECRET_KEY'] = urandom(32)

        json_provider = DefaultJSONProvider(app)
        json_provider.sort_keys = False
        json_provider.compact = False
        app.json = json_provider

        # Add error handlers
        @app.errorhandler(400)
        def bad_request(e):
            return return_api(**BadRequest().api_response)

        @app.errorhandler(404)
        def not_found(e):
            if request.path.startswith(
                (Constants.API_PREFIX, Constants.ADMIN_PREFIX)
            ):
                return return_api(**NotFound().api_response)
            return render("page_not_found.html")

        @app.errorhandler(405)
        def method_not_allowed(e):
            return return_api(**MethodNotAllowed().api_response)

        @app.errorhandler(500)
        def internal_error(e):
            return return_api(**InternalError().api_response)

        @app.errorhandler(MindException)
        def mind_exception(e: MindException):
            if isinstance(e, LogUnauthMindException):
                ip = request.environ.get(
                    'HTTP_X_FORWARDED_FOR',
                    request.remote_addr
                )
                LOGGER.warning(f'Unauthorised request from {ip}')

            return return_api(**e.api_response)

        # Add endpoints
        app.register_blueprint(ui)
        app.register_blueprint(api, url_prefix=Constants.API_PREFIX)
        app.register_blueprint(admin_api, url_prefix=Constants.ADMIN_PREFIX)

        # Setup db handling
        app.teardown_appcontext(close_db)

        return app

    def run(
        self,
        host: str,
        port: int,
        url_prefix: str
    ) -> Union[StartType, None]:
        """Start the webserver.

        Args:
            host (str): IP address to bind to, or `0.0.0.0` for all.
            port (int): The port to listen on.
            url_prefix (str): The url prefix/base to host the endpoints on, or
                an empty string for no prefix.

        Returns:
            Union[StartType, None]: `None` on shutdown, `StartType` on restart.
        """
        self.app.config["APPLICATION_ROOT"] = url_prefix
        self.app.wsgi_app = DispatcherMiddleware( # type: ignore
            Flask(__name__),
            {url_prefix: self.app.wsgi_app}
        )
        self.__class__.url_prefix = url_prefix

        dispatcher = ThreadedTaskDispatcher()
        dispatcher.set_thread_count(Constants.HOSTING_THREADS)

        self.server = create_server(
            self.app,
            _dispatcher=dispatcher,
            host=host,
            port=port,
            threads=Constants.HOSTING_THREADS
        )

        LOGGER.info(f'MIND running on http://{host}:{port}{self.url_prefix}')
        self.server.run()

        return self.__start_type

    def __trigger_server_shutdown(self) -> None:
        """Shutdown waitress server. Intended to be run in a thread."""
        if not hasattr(self, 'server'):
            return

        self.server.task_dispatcher.shutdown()
        self.server.close()
        self.server._map.clear() # type: ignore
        return

    def shutdown(self) -> None:
        """
        Stop the waitress server. Starts a thread that will trigger the server
        shutdown after one second.
        """
        self.get_db_timer_thread(
            1.0,
            self.__trigger_server_shutdown,
            "InternalStateHandler"
        ).start()
        return

    def restart(
        self,
        start_type: StartType = StartType.RESTART
    ) -> None:
        """Same as `self.shutdown()`, but restart instead of shutting down.

        Args:
            start_type (StartType, optional): Why Kapowarr should
                restart.
                Defaults to StartType.RESTART.
        """
        self.__start_type = start_type
        self.shutdown()
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


# region StartType Handling
class StartTypeHandlers:
    handlers: dict[StartType, StartTypeHandler] = {}
    timeout_thread: Union[Timer, None] = None
    running_handler: Union[StartType, None] = None

    @classmethod
    def register_handler(cls, start_type: StartType):
        """Class decorator to register a StartTypeHandler for a certain start
        type.

        ```
        @StartTypeHandlers.register_handler(example_type)
        class ExampleHandler(StartTypeHandler):
            ...
        ```

        Args:
            start_type (StartType): The start type that the StartTypeHandler is
                for.
        """
        def wrapper(
            handler_class: type[StartTypeHandler]
        ) -> type[StartTypeHandler]:
            cls.handlers[start_type] = handler_class()
            return handler_class
        return wrapper

    @staticmethod
    def _on_timeout_wrapper(
        on_timeout: Callable[[], None],
        restart_on_timeout: bool
    ) -> None:
        on_timeout()
        if restart_on_timeout:
            Server().restart()
        return

    @classmethod
    def start_timer(cls, start_type: StartType) -> None:
        """Start the timer for a start type.

        Args:
            start_type (StartType): The start type to start the timer for.
        """
        if start_type not in cls.handlers:
            return

        if cls.timeout_thread and cls.timeout_thread.is_alive():
            cls.timeout_thread.cancel()

        handler = cls.handlers[start_type]
        cls.running_handler = start_type
        cls.timeout_thread = Server().get_db_timer_thread(
            interval=handler.timeout,
            target=cls._on_timeout_wrapper,
            name="StartTypeHandler",
            args=(handler.on_timeout, handler.restart_on_timeout)
        )
        cls.timeout_thread.start()
        LOGGER.info(
            "Starting timer for %s (%d seconds)",
            handler.description, handler.timeout
        )
        return

    @classmethod
    def diffuse_timer(cls, start_type: StartType) -> None:
        """Stop/Diffuse the timer for a start type.

        Args:
            start_type (StartType): The start type to stop the timer for.
        """
        if cls.running_handler != start_type:
            return

        if cls.timeout_thread and cls.timeout_thread.is_alive():
            handler = cls.handlers[start_type]
            LOGGER.info(
                "Timer for %s diffused",
                handler.description
            )
            cls.timeout_thread.cancel()
            cls.timeout_thread = None
            cls.running_handler = None
            handler.on_diffuse()
        return


@StartTypeHandlers.register_handler(StartType.RESTART_HOSTING_CHANGES)
class HostingChangesHandler(StartTypeHandler):
    description = "hosting changes"
    timeout = Constants.HOSTING_REVERT_TIME
    restart_on_timeout = True

    def on_timeout(self) -> None:
        Settings().restore_hosting_settings()
        return

    def on_diffuse(self) -> None:
        return


@StartTypeHandlers.register_handler(StartType.RESTART_DB_CHANGES)
class DatabaseChangesHandler(StartTypeHandler):
    description = "database import"
    timeout = Constants.DB_REVERT_TIME
    restart_on_timeout = True

    def on_timeout(self) -> None:
        revert_db_import(swap=True)
        return

    def on_diffuse(self) -> None:
        revert_db_import(swap=False)
        return
