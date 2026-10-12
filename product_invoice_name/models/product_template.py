# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    invoice_name = fields.Char(
        translate=True,
        help="Printed on customer invoice lines in place of the product name. "
        "Leave it empty to print the product name.",
    )
