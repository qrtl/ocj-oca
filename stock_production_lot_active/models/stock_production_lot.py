# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class StockLot(models.Model):
    _inherit = "stock.lot"

    active = fields.Boolean(default=True)

    @api.constrains("name", "product_id", "company_id")
    def _check_unique_lot(self):
        """Check that there is no other lot with the same name, company and product

        To avoid allowing duplicate lot/company/name combinations when there is
        another inactive entry we have to set the active_test flag to False.
        """
        return super(StockLot, self.with_context(active_test=False))._check_unique_lot()

    def write(self, vals):
        if (
            "active" in vals
            and not vals["active"]
            and not self.env.context.get("do_not_check_quant")
        ):
            self._check_no_stock_on_hand()
        return super().write(vals)

    def _check_no_stock_on_hand(self):
        """Refuse when any of the lots has quantity in an internal location."""
        quants = self.env["stock.quant"].search(
            [
                ("lot_id", "in", self.ids),
                ("location_id.usage", "=", "internal"),
                "|",
                ("quantity", "!=", 0),
                ("reserved_quantity", "!=", 0),
            ]
        )
        if quants:
            raise UserError(
                self.env._(
                    "You cannot archive a lot that still has stock on hand. "
                    "Move it out first:\n%(lines)s",
                    lines="\n".join(
                        f"{quant.lot_id.name}: {quant.location_id.display_name}"
                        for quant in quants
                    ),
                )
            )
