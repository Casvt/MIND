#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from atexit import register
from os import environ, name
from signal import SIGINT, SIGTERM, signal
from subprocess import Popen
from sys import argv, exit
from typing import NoReturn, Union

from backend.base.custom_exceptions import InvalidKeyValue
from backend.base.definitions import Constants, StartType
from backend.base.helpers import check_min_python_version, get_python_exe
from backend.base.logging import LOGGER, setup_logging
from backend.features.reminder_handler import ReminderHandler
from backend.features.tz_shifter import TimezoneChangeHandler
from backend.internals.db import set_db_location, setup_db
from backend.internals.db_backup_import import DatabaseBackupHandler
from backend.internals.server import Server, StartTypeHandlers
from backend.internals.settings import Settings


def subprocess_main(
    start_type: StartType,
    db_folder: Union[str, None] = None,
    log_folder: Union[str, None] = None,
    host: Union[str, None] = None,
    port: Union[int, None] = None,
    url_prefix: Union[str, None] = None
) -> NoReturn:
    """The main function of the MIND sub-process.

    Args:
        start_type (StartType): The type of (re)start.

        db_folder (Union[str, None], optional): The folder in which the database
            will be stored or in which a database is for MIND to use.
            Defaults to None.

        log_folder (Union[str, None], optional): The folder in which the logs
            from MIND will be stored.
            Defaults to None.

        host (Union[str, None], optional): The host to bind the server to.
            Defaults to None.

        port (Union[int, None], optional): The port to bind the server to.
            Defaults to None.

        url_prefix (Union[str, None], optional): The URL prefix to use for the
            server.
            Defaults to None.

    Raises:
        InvalidKeyValue: One of the hosting arguments has an invalid value.
        ValueError: One of the folder arguments has an invalid value.

    Returns:
        NoReturn: Exit code 0 means to shutdown. Exit code 131 or higher means
            to restart with possibly special reasons.
    """
    setup_logging(log_folder)
    LOGGER.info('Starting up MIND')

    if not check_min_python_version(*Constants.MIN_PYTHON_VERSION):
        exit(1)

    set_db_location(db_folder)

    SERVER = Server()
    with SERVER.app.app_context():
        StartTypeHandlers.start_timer(start_type)
        setup_db()

        s = Settings()

        if host:
            s.update({"host": host})
        if port:
            s.update({"port": port})
        if url_prefix:
            s.update({"url_prefix": url_prefix})

        settings = s.get_settings()

        ReminderHandler.set_reminder_timer()
        DatabaseBackupHandler.set_backup_timer()
        TimezoneChangeHandler.detect_and_handle_timezone_change()
        TimezoneChangeHandler.set_detector_timer()

    restart_type = None
    try:
        # =================
        restart_type = SERVER.run(
            settings.host, settings.port, settings.url_prefix
        )
        # =================

    finally:
        ReminderHandler.stop_reminder_timer()
        DatabaseBackupHandler.stop_backup_timer()
        TimezoneChangeHandler.stop_detector_timer()

        if restart_type is not None:
            LOGGER.info("Restarting MIND")
            exit(restart_type.value)

        exit(0)


def _stop_sub_process(proc: Popen) -> None:
    """Gracefully stop the sub-process unless that fails. Then terminate it.

    Args:
        proc (Popen): The sub-process to stop.
    """
    if proc.returncode is not None:
        return

    try:
        if name != 'nt':
            try:
                proc.send_signal(SIGINT)
            except ProcessLookupError:
                pass
        else:
            import win32api  # type: ignore
            import win32con  # type: ignore
            try:
                win32api.GenerateConsoleCtrlEvent(
                    win32con.CTRL_C_EVENT, proc.pid
                )
            except KeyboardInterrupt:
                pass
    except BaseException:
        proc.terminate()


def _run_sub_process(
    start_type: StartType = StartType.STARTUP
) -> int:
    """Start the sub-process that MIND will be run in.

    Args:
        start_type (StartType, optional): Why MIND was started.
            Defaults to `StartType.STARTUP`.

    Returns:
        int: The return code from the sub-process.
    """
    env = {
        **environ,
        "MIND_RUN_MAIN": "1",
        "MIND_START_TYPE": str(start_type.value)
    }

    py_exe = get_python_exe()
    if not py_exe:
        print("ERROR: Python executable not found")
        return 1

    comm = [py_exe, "-u", __file__] + argv[1:]
    proc = Popen(
        comm,
        env=env
    )
    proc._sigint_wait_secs = Constants.SUB_PROCESS_TIMEOUT # type: ignore
    register(_stop_sub_process, proc=proc)
    signal(SIGTERM, lambda signal_no, frame: _stop_sub_process(proc))

    try:
        return proc.wait()
    except (KeyboardInterrupt, SystemExit, ChildProcessError):
        return 0


def main() -> int:
    """The main function of MIND.

    Returns:
        int: The return code.
    """
    rc = StartType.STARTUP.value
    while rc in StartType._member_map_.values():
        rc = _run_sub_process(
            StartType(rc)
        )

    return rc


if __name__ == "__main__":
    if environ.get("MIND_RUN_MAIN") == "1":

        parser = ArgumentParser(description="""
            MIND is a simple self hosted reminder application that can send push
            notifications to your device. Set the reminder and forget about it!
        """)

        fs = parser.add_argument_group(title="Folders")
        fs.add_argument(
            '-d', '--DatabaseFolder',
            type=str,
            help=("The folder in which the database will be stored or in which "
                "a database is for MIND to use")
        )
        fs.add_argument(
            '-l', '--LogFolder',
            type=str,
            help="The folder in which the logs from MIND will be stored"
        )

        hs = parser.add_argument_group(title="Hosting Settings")
        hs.add_argument(
            '-o', '--Host',
            type=str,
            help="The host to bind the server to"
        )
        hs.add_argument(
            '-p', '--Port',
            type=int,
            help="The port to bind the server to"
        )
        hs.add_argument(
            '-u', '--UrlPrefix',
            type=str,
            help="The URL prefix to use for the server"
        )

        args = parser.parse_args()

        start_type = StartType(int(environ.get(
            "MIND_START_TYPE",
            StartType.STARTUP.value
        )))

        db_folder: Union[str, None] = args.DatabaseFolder
        log_folder: Union[str, None] = args.LogFolder
        host: Union[str, None] = None
        port: Union[int, None] = None
        url_prefix: Union[str, None] = None
        if start_type == StartType.STARTUP:
            host = args.Host
            port = args.Port
            url_prefix = args.UrlPrefix

        try:
            subprocess_main(
                start_type=start_type,
                db_folder=db_folder,
                log_folder=log_folder,
                host=host,
                port=port,
                url_prefix=url_prefix
            )

        except InvalidKeyValue as e:
            if e.key == 'host':
                parser.error(
                    'The value for -h/--Host is not valid'
                )

            elif e.key == 'port':
                parser.error(
                    'The value for -p/--Port is not valid'
                )

            elif e.key == 'url_prefix':
                parser.error(
                    'The value for -u/--UrlPrefix is not valid'
                )

            else:
                raise e

        except ValueError as e:
            if not e.args:
                raise e

            elif 'database' in e.args[0].lower():
                parser.error(
                    'The value for -d/--DatabaseFolder is not a folder'
                )

            elif 'logging' in e.args[0].lower():
                parser.error(
                    'The value for -l/--LogFolder is not a folder'
                )

            else:
                raise e

    else:
        return_code = main()
        exit(return_code)
