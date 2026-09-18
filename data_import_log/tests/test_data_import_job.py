# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from unittest.mock import patch

from odoo.addons.queue_job.exception import RetryableJobError

from .common import DataImportCase

MODEL = "odoo.addons.data_import_log.models.data_import_log.DataImportLog"


class TestDataImportJob(DataImportCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Run the unit and finalizer jobs inline instead of enqueuing them.
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))

    def test_all_units_imported(self):
        log = self._create_log()
        log._start_processing(2)
        with patch(f"{MODEL}._import_unit", return_value=[]):
            log._run_unit("D-001", [])
            self.assertEqual(log.state, "processing")
            log._run_unit("D-002", [])
        self.assertEqual(log.state, "done")
        self.assertTrue(log.date_done)
        self.assertFalse(log.error_ids)

    def test_rejected_unit_makes_the_file_partial(self):
        log = self._create_log()
        log._start_processing(2)
        errors = [{"reference": "D-002", "error_message": "no matching order"}]
        with patch(f"{MODEL}._import_unit", return_value=[]):
            log._run_unit("D-001", [])
        with patch(f"{MODEL}._import_unit", return_value=errors):
            log._run_unit("D-002", [])
        self.assertEqual(log.state, "partial")
        self.assertEqual(log.unit_failed, 1)
        self.assertEqual(log.error_ids.error_message, "no matching order")

    def test_every_unit_rejected_makes_the_file_error(self):
        log = self._create_log()
        log._start_processing(1)
        errors = [{"reference": "D-001", "error_message": "unknown product"}]
        with patch(f"{MODEL}._import_unit", return_value=errors):
            log._run_unit("D-001", [])
        self.assertEqual(log.state, "error")

    def test_transient_failure_settles_nothing(self):
        log = self._create_log()
        log._start_processing(1)
        with patch(f"{MODEL}._import_unit", side_effect=RetryableJobError("locked")):
            with self.assertRaises(RetryableJobError):
                log._run_unit("D-001", [])
        self.assertEqual(log.unit_settled, 0)
        self.assertEqual(log.state, "processing")

    def test_failed_job_settles_its_unit(self):
        log = self._create_log()
        log._start_processing(2)
        with patch(f"{MODEL}._import_unit", return_value=[]):
            log._run_unit("D-001", [])
        job = self.env["queue.job"].create(
            {
                "uuid": "test-failed-unit",
                "model_name": "data.import.log",
                "method_name": "_run_unit",
                "records": log,
                "args": (),
                "kwargs": {"unit_key": "D-002", "rows": []},
                "state": "started",
                "exc_info": "Traceback: boom",
            }
        )
        job.write({"state": "failed"})
        self.assertEqual(log.state, "partial")
        self.assertEqual(log.unit_failed, 1)
        self.assertEqual(log.error_ids.reference, "D-002")
        self.assertIn("boom", log.error_ids.error_message)

    def test_finalize_runs_once(self):
        log = self._create_log()
        log._start_processing(1)
        with patch(f"{MODEL}._import_unit", return_value=[]):
            log._run_unit("D-001", [])
        date_done = log.date_done
        log._finalize()
        self.assertEqual(log.date_done, date_done)

    def test_parse_file_makes_one_unit_per_row(self):
        log = self._create_log(content=b"a,b\n1,2\n3,4\n")
        with patch(f"{MODEL}._import_unit", return_value=[]) as import_unit:
            log._parse_file()
        self.assertEqual(log.unit_total, 2)
        self.assertEqual(log.state, "done")
        self.assertEqual(import_unit.call_count, 2)

    def test_parse_file_groups_rows(self):
        log = self._create_log(content=b"key,qty\nD-1,2\nD-1,3\nD-2,4\n")

        def group(self, fieldnames, rows):
            units = {}
            for row in rows:
                units.setdefault(row["key"], []).append(row)
            return units

        with (
            patch(f"{MODEL}._group_rows", group),
            patch(f"{MODEL}._import_unit", return_value=[]),
        ):
            log._parse_file()
        self.assertEqual(log.unit_total, 2)
        self.assertEqual(log.state, "done")

    def test_empty_file_is_done_not_error(self):
        log = self._create_log(content=b"a,b\n")
        log._parse_file()
        self.assertEqual(log.unit_total, 0)
        self.assertEqual(log.state, "done")
        self.assertFalse(log.error_ids)
