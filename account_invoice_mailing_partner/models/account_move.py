# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_mailing_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Invoice Mailing Address",
        compute="_compute_invoice_mailing_partner_id",
        store=True,
        readonly=False,
        check_company=True,
        ondelete="restrict",
        tracking=True,
        help="Contact the invoice document should be addressed to, when it differs "
        "from the billing partner. It is only used to print the recipient address; "
        "the invoice itself is still issued to the billing partner.",
    )
    report_partner_id = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_report_partner_id",
        help="Technical field holding the contact the invoice document is addressed "
        "to, used by the report to fall back to the billing partner.",
    )

    # The dependency is intentionally not dotted: changing the mailing address on the
    # partner should not retroactively update the invoices already issued.
    @api.depends("partner_id")
    def _compute_invoice_mailing_partner_id(self):
        for move in self:
            if not move.partner_id:
                move.invoice_mailing_partner_id = False
                continue
            move.invoice_mailing_partner_id = (
                move.partner_id._get_invoice_mailing_partner()
            )

    @api.depends("invoice_mailing_partner_id", "partner_id")
    def _compute_report_partner_id(self):
        for move in self:
            move.report_partner_id = move.invoice_mailing_partner_id or move.partner_id

    def _get_invoice_mailing_partner(self):
        """Return the invoice mailing address shared by all the invoices in self."""
        mailing_partner = self[:1].invoice_mailing_partner_id
        if any(move.invoice_mailing_partner_id != mailing_partner for move in self):
            raise UserError(
                self.env._(
                    "Please select invoices with the same invoice mailing address."
                )
            )
        return mailing_partner
