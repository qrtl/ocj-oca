# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from psycopg2 import IntegrityError

from odoo.exceptions import UserError
from odoo.tools import mute_logger

from .common import DataImportCase


class TestDataImportLog(DataImportCase):
    def test_new_log_is_pending(self):
        log = self._create_log()
        self.assertEqual(log.state, "pending")
        self.assertEqual(log.file_name, "feed.csv")
        self.assertTrue(log.date_start)
        self.assertFalse(log.date_done)

    def test_same_file_twice_is_rejected(self):
        self._create_log()
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self._create_log()
            self.env.flush_all()

    def test_same_name_different_content_is_accepted(self):
        self._create_log()
        other = self._create_log(content=b"a,b\n3,4\n")
        self.env.flush_all()
        self.assertEqual(other.state, "pending")

    def test_start_processing_sets_units(self):
        log = self._create_log()
        log._start_processing(3)
        self.assertEqual(log.state, "processing")
        self.assertEqual(log.unit_total, 3)
        self.assertEqual(log.unit_settled, 0)

    def test_start_processing_twice_is_rejected(self):
        log = self._create_log()
        log._start_processing(3)
        with self.assertRaises(UserError):
            log._start_processing(3)
