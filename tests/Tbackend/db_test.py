import unittest
from os.path import join

from flask import Flask

from backend.base.helpers import folder_path
from backend.internals.db import Constants, DBConnection, close_db


class Test_DB(unittest.TestCase):
    def test_foreign_key_and_wal(self):
        app = Flask(__name__)
        app.teardown_appcontext(close_db)

        DBConnection.file = join(
            folder_path(*Constants.DB_FOLDER),
            Constants.DB_NAME
        )
        with app.app_context():
            instance = DBConnection(timeout=Constants.DB_TIMEOUT)
            self.assertEqual(
                instance.cursor().execute(
                    "PRAGMA foreign_keys;"
                ).fetchone()[0],
                1
            )
