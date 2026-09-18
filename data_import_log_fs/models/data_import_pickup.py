# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
import logging
import re

from odoo import api, fields, models, modules

_logger = logging.getLogger(__name__)

# A file still being written is named so by convention, and is not ours yet.
INCOMPLETE_SUFFIX = ".tmp"
# Fixed, because it has to mean the same thing in every process that takes it.
SCAN_LOCK_KEY = 84213310


class DataImportPickup(models.Model):
    _name = "data.import.pickup"
    _description = "Data Import Pick-up"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.company
    )
    backend_id = fields.Many2one(
        "fs.storage", string="Storage", required=True, ondelete="restrict"
    )
    path_in = fields.Char(
        "Incoming Path",
        required=True,
        default="in",
        help="Directory the files are picked up from, relative to the storage.",
    )
    path_processing = fields.Char(
        "Processing Path",
        required=True,
        default="processing",
        help="Directory a file is held in while it is being imported, so that it "
        "is picked up only once.",
    )
    path_done = fields.Char("Done Path", required=True, default="done")
    path_error = fields.Char(
        "Error Path",
        required=True,
        default="error",
        help="Directory the files reporting rejected units are written to.",
    )
    filename_pattern = fields.Char(
        default=r".*\.csv$",
        help="Only the files whose name matches this regular expression are picked up.",
    )
    file_format = fields.Selection(
        [("csv", "CSV"), ("xlsx", "Excel")], required=True, default="csv"
    )
    encoding = fields.Char(default="utf-8")
    log_ids = fields.One2many("data.import.log", "pickup_id", string="Import Logs")

    _name_uniq = models.Constraint("UNIQUE (name)", "A pick-up name must be unique.")

    def _matching_names(self, names):
        """Return the names to take in, in a stable order."""
        self.ensure_one()
        pattern = re.compile(self.filename_pattern or ".*")
        return sorted(
            name
            for name in names
            if not name.endswith(INCOMPLETE_SUFFIX) and pattern.match(name)
        )

    def _take_in(self, name):
        """Create the log for one file and hold the file while it is imported.

        Returns the log, or an empty recordset when the file turns out to have
        been imported already.
        """
        self.ensure_one()
        fs = self.backend_id.fs
        source = f"{self.path_in}/{name}"
        with fs.open(source, "rb") as fh:
            content = fh.read()
        log_model = self.env["data.import.log"]
        content_hash = log_model._content_hash(content)
        if log_model.search_count(
            [("file_name", "=", name), ("content_hash", "=", content_hash)], limit=1
        ):
            _logger.info("%s was already imported, left in place.", source)
            return log_model
        attachment = self.env["ir.attachment"].create(
            {"name": name, "datas": base64.b64encode(content)}
        )
        log = log_model.create(
            {
                "pickup_id": self.id,
                "attachment_id": attachment.id,
                "content_hash": content_hash,
                "file_format": self.file_format,
                "encoding": self.encoding,
                "company_id": self.company_id.id,
            }
        )
        fs.mv(source, f"{self.path_processing}/{name}")
        return log

    def _scan(self):
        """Take in every file waiting in the incoming directory."""
        logs = self.env["data.import.log"]
        for pickup in self:
            fs = pickup.backend_id.fs
            if not fs.exists(pickup.path_in):
                continue
            names = [
                path.rsplit("/", 1)[-1] for path in fs.ls(pickup.path_in, detail=False)
            ]
            for name in pickup._matching_names(names):
                log = pickup._take_in(name)
                if not log:
                    continue
                logs |= log
                log._enqueue_parse()
                # Commit each file on its own: its source has already moved on
                # the remote filesystem, which no rollback undoes, so a failure
                # on a later file would otherwise leave that file held aside
                # with no log to account for it. This is the recognized case
                # for committing: a cron importing a batch of independent items.
                if not modules.module.current_test:
                    # pylint: disable=invalid-commit
                    self.env.cr.commit()
        return logs

    @api.model
    def _cron_scan(self):
        """Scan every pick-up, unless a previous run is still going.

        The lock is held on the session rather than the transaction, since the
        scan commits every file it takes in and would otherwise release it
        halfway through.
        """
        self.env.cr.execute("SELECT pg_try_advisory_lock(%s)", (SCAN_LOCK_KEY,))
        if not self.env.cr.fetchone()[0]:
            _logger.info("Another scan is running, skipped.")
            return
        try:
            # Pick-ups are configuration: a handful of records, all wanted.
            # pylint: disable=no-search-all
            self.search([])._scan()
        finally:
            self.env.cr.execute("SELECT pg_advisory_unlock(%s)", (SCAN_LOCK_KEY,))
