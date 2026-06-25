# Copyright 2026 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class Commission(models.Model):
    _inherit = "commission"

    commission_type = fields.Selection(
        selection_add=[("product_fixed", "Fixed amount per product")],
        ondelete={"product_fixed": "set default"},
    )
    product_line_ids = fields.One2many(
        comodel_name="commission.product.line",
        inverse_name="commission_id",
        string="Product amounts",
        copy=True,
    )

    def _get_product_fixed_line(self, product):
        """Return the product amount line matching the given product (or empty)."""
        self.ensure_one()
        return self.product_line_ids.filtered(lambda x: x.product_id == product)[:1]


class CommissionProductLine(models.Model):
    _name = "commission.product.line"
    _description = "Fixed commission amount per product"
    _rec_name = "product_id"

    _unique_product = models.Constraint(
        "UNIQUE(commission_id, product_id)",
        "You can only set one amount per product in a commission.",
    )

    commission_id = fields.Many2one(
        comodel_name="commission",
        required=True,
        ondelete="cascade",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        required=True,
    )
    amount = fields.Monetary(
        string="Commission Amount",
        required=True,
        help="Fixed commission amount granted per unit of the product.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id",
    )
