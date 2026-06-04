# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    auto_bill_on_receipt = fields.Selection(
        selection=[
            ("auto", "Auto Bill on Receipt"),
            ("no_auto", "No Auto Bill"),
        ],
        help="Override the product category setting. "
        "Leave empty to inherit from the product category.",
    )
