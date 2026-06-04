# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        res = super().button_validate()
        for picking in self.filtered(
            lambda p: p.state == "done" and p.picking_type_code == "incoming"
        ):
            picking._auto_create_vendor_bill()
        return res

    def _auto_create_vendor_bill(self):
        self.ensure_one()
        purchase = self.purchase_id
        if not purchase or purchase.block_auto_bill:
            return
        purchase._auto_bill_for_picking(self)
