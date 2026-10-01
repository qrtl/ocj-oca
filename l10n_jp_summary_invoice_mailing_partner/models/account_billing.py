# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountBilling(models.Model):
    _inherit = "account.billing"

    invoice_mailing_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Invoice Mailing Address",
        compute="_compute_invoice_mailing_partner_id",
        store=True,
        readonly=False,
        check_company=True,
        ondelete="restrict",
        tracking=True,
        help="Contact the summary invoice should be addressed to, when it differs "
        "from the billing partner. Only invoices sharing this mailing address are "
        "gathered in the billing.",
    )

    # The dependency is intentionally not dotted: changing the mailing address on the
    # partner should not retroactively update the billings already issued.
    @api.depends("partner_id")
    def _compute_invoice_mailing_partner_id(self):
        for billing in self:
            if not billing.partner_id:
                billing.invoice_mailing_partner_id = False
                continue
            billing.invoice_mailing_partner_id = (
                billing.partner_id._get_invoice_mailing_partner()
            )

    @api.constrains("invoice_mailing_partner_id", "billing_line_ids")
    def _check_invoice_mailing_partner_consistency(self):
        for rec in self:
            invoices = rec.billing_line_ids.move_id
            if any(
                move.invoice_mailing_partner_id != rec.invoice_mailing_partner_id
                for move in invoices
            ):
                raise ValidationError(
                    self.env._(
                        "The invoice mailing address of the billing is inconsistent "
                        "with the one on the invoices."
                    )
                )

    def _get_moves(self, date, types=False):
        moves = super()._get_moves(date, types=types)
        return moves.filtered(
            lambda x: x.invoice_mailing_partner_id == self.invoice_mailing_partner_id
        )
