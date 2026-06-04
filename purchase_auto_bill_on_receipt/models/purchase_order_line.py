# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _auto_bill_eligible(self):
        self.ensure_one()
        product_setting = self.product_id.auto_bill_on_receipt
        if product_setting == "auto":
            return True
        if product_setting == "no_auto":
            return False
        return self.product_id.categ_id.auto_bill_on_receipt
