import unittest

from backend.db import DB_FILENAME, DBConnection
from backend.helpers import folder_path


class Test_DB(unittest.TestCase):
	def test_foreign_key_and_wal(self):
		DBConnection.file = folder_path(*DB_FILENAME)
		instance = DBConnection(timeout=20.0)
		self.assertEqual(instance.cursor().execute("PRAGMA foreign_keys;").fetchone()[0], 1)
