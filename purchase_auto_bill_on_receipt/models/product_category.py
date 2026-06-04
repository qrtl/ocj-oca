# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    auto_bill_on_receipt = fields.Boolean(
        help="When enabled, products in this category will automatically "
        "generate a Vendor Bill when goods are received.",
    )
