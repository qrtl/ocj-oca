# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _create_billing(self, partner):
        # The billing defaults its mailing address from the partner, while the selected
        # invoices may carry a document-level override. Pass it as a default so that it
        # is part of the creation values, before the consistency constraint is checked.
        mailing_partner = self._get_invoice_mailing_partner()
        self = self.with_context(default_invoice_mailing_partner_id=mailing_partner.id)
        return super()._create_billing(partner)
