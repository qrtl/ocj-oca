# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import logging

from odoo import Command, fields, models

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    block_auto_bill = fields.Boolean(
        help="When enabled, suppresses automatic bill creation on receipt "
        "for this order, regardless of product or category settings.",
    )

    def _auto_bill_for_picking(self, picking):
        self.ensure_one()
        received_products = picking.move_ids.product_id
        eligible_lines = self.order_line.filtered(
            lambda line: line.product_id in received_products
            and line._auto_bill_eligible()
            and line.qty_to_invoice > 0
        )
        if not eligible_lines:
            return self.env["account.move"]
        try:
            bill = self._auto_bill_create(picking, eligible_lines)
        except Exception as e:
            _logger.exception(
                "Auto-bill creation failed for PO %s / picking %s",
                self.name,
                picking.name,
            )
            self._auto_bill_log_failure(picking, "create", e)
            return self.env["account.move"]
        try:
            bill.action_post()
        except Exception as e:
            _logger.exception(
                "Auto-bill posting failed for PO %s / picking %s / bill %s",
                self.name,
                picking.name,
                bill.name,
            )
            self._auto_bill_log_failure(picking, "post", e, bill=bill)
        return bill

    def _auto_bill_create(self, picking, eligible_lines):
        self.ensure_one()
        invoice_vals = self._prepare_invoice()
        invoice_vals["invoice_date"] = picking.date_done.date()
        invoice_lines = []
        sequence = 10
        pending_section = None
        for line in self.order_line:
            if line.display_type in ("line_section", "line_subsection"):
                pending_section = line
                continue
            if line not in eligible_lines:
                continue
            if pending_section:
                section_vals = pending_section._prepare_account_move_line()
                section_vals["sequence"] = sequence
                invoice_lines.append(Command.create(section_vals))
                sequence += 1
                pending_section = None
            line_vals = line._prepare_account_move_line()
            line_vals["sequence"] = sequence
            invoice_lines.append(Command.create(line_vals))
            sequence += 1
        invoice_vals["invoice_line_ids"] = invoice_lines
        return (
            self.env["account.move"]
            .with_company(self.company_id)
            .with_context(default_move_type="in_invoice")
            .create(invoice_vals)
        )

    def _auto_bill_log_failure(self, picking, step, exception, bill=False):
        self.ensure_one()
        if step == "create":
            summary = self.env._("Auto-bill creation failed — manual review needed")
            body = self.env._(
                "Auto-bill creation failed on receipt %(picking)s: %(error)s",
                picking=picking.name,
                error=exception,
            )
        else:
            summary = self.env._("Auto-bill posting failed — manual review needed")
            body = self.env._(
                "Auto-bill posting failed on receipt %(picking)s "
                "(bill %(bill)s remains in draft): %(error)s",
                picking=picking.name,
                bill=bill.display_name if bill else "",
                error=exception,
            )
        self.message_post(body=body, message_type="notification")
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=summary,
            user_id=(self.user_id or self.env.user).id,
        )
