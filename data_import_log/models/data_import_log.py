# Copyright 2020-2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import hashlib

from odoo import api, fields, models
from odoo.exceptions import UserError


class DataImportLog(models.Model):
    _name = "data.import.log"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Data Import Log"
    _rec_name = "file_name"
    _order = "id DESC"

    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.company
    )
    attachment_id = fields.Many2one(
        "ir.attachment", string="File", readonly=True, ondelete="restrict"
    )
    file_name = fields.Char(related="attachment_id.name", store=True)
    file_data = fields.Binary(related="attachment_id.datas", string="File Content")
    content_hash = fields.Char(
        readonly=True,
        help="SHA-256 of the file content, used to recognize a file already taken in.",
    )
    file_format = fields.Selection(
        [("csv", "CSV"), ("xlsx", "Excel")], required=True, default="csv"
    )
    encoding = fields.Char(
        default="utf-8",
        help="Character encoding of the source file. Ignored for Excel files.",
    )
    model_id = fields.Many2one("ir.model", string="Model")
    model_name = fields.Char(related="model_id.model", string="Model Name")
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("done", "Done"),
            ("partial", "Partially Imported"),
            ("error", "Error"),
        ],
        string="Status",
        required=True,
        default="pending",
        readonly=True,
        tracking=True,
    )
    unit_total = fields.Integer(
        "Units", readonly=True, help="Number of units (records or groups) to import."
    )
    unit_settled = fields.Integer(
        "Settled", readonly=True, help="Units that reached a final outcome."
    )
    unit_failed = fields.Integer("Failed", readonly=True)
    date_start = fields.Datetime(
        "Started On", readonly=True, default=fields.Datetime.now
    )
    date_done = fields.Datetime("Finished On", readonly=True)
    error_ids = fields.One2many("data.import.error", "log_id", string="Log Lines")

    _file_uniq = models.Constraint(
        "UNIQUE (file_name, content_hash)",
        "This file has already been taken in.",
    )

    @api.model
    def _content_hash(self, content):
        """Return the hash identifying a file content."""
        return hashlib.sha256(content).hexdigest()

    def _start_processing(self, unit_total):
        """Record how many units the file was split into, and await settlement."""
        self.ensure_one()
        if self.state != "pending":
            raise UserError(
                self.env._(
                    "Import log %(name)s is in state %(state)s and cannot be started.",
                    name=self.display_name,
                    state=self.state,
                )
            )
        self.write({"state": "processing", "unit_total": unit_total})
