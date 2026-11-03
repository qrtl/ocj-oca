# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _get_report_partner(self, record):
        """Address the document to the mailing address when the record carries one.

        This covers every report rendered with the alternative layout (i.e. the
        summary invoice, but also the invoice itself), as the address block is built
        from this method.
        """
        if (
            "invoice_mailing_partner_id" in record._fields
            and record.invoice_mailing_partner_id
        ):
            return record.invoice_mailing_partner_id
        return super()._get_report_partner(record)
