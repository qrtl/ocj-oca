# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    invoice_mailing_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Invoice Mailing Address",
        check_company=True,
        ondelete="restrict",
        help="Contact the invoice document should be addressed to, when it differs "
        "from the billing partner. It is only used to print the recipient address; "
        "the invoice itself is still issued to the billing partner.",
    )

    def _get_invoice_mailing_partner(self):
        """Return the invoice mailing address to default on documents of this partner.

        The setting is looked up on the partner itself first, so that a specific
        contact of a company can be given its own mailing address, and falls back to
        the commercial partner.
        """
        self.ensure_one()
        return (
            self.invoice_mailing_partner_id
            or self.commercial_partner_id.invoice_mailing_partner_id
        )
