#-*- coding: utf-8 -*-

import logging


def setup_logging() -> None:
	"Setup the basic config of the logging module"
	logging.basicConfig(
		level=logging.INFO,
		format='[%(asctime)s][%(threadName)s][%(levelname)s] %(message)s',
		datefmt='%Y-%m-%d %H:%M:%S',
		force=True
	)
	return

def set_log_level(level: int) -> None:
	"""Change the logging level

	Args:
		level (int): The level to set the logging to.
			Should be a logging level, like `logging.INFO` or `logging.DEBUG`.
	"""
	logging.debug(f'Setting logging level: {level}')
	logging.getLogger().setLevel(
		level=level
	)
	return
