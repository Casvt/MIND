import unittest

from backend.db import DBConnection
from backend.helpers import folder_path
from MIND import DB_FILENAME


class Test_DB(unittest.TestCase):
	def test_foreign_key(self):
		DBConnection.file = folder_path(*DB_FILENAME)
		instance = DBConnection(timeout=20.0)
		self.assertEqual(instance.cursor().execute("PRAGMA foreign_keys;").fetchone()[0], 1)
