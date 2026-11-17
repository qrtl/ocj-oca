# © 2023 ooops404
# Copyright 2023 Simone Rubino - Aion Tech
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    commission_origin_line_id = fields.Many2one(
        "account.move.line",
        copy=False,
        readonly=True,
        help="Invoice line this line was copied from by a reversal, whose "
        "commission item a credit note gives back.",
    )

    def _copy_data_extend_business_fields(self, values):
        res = super()._copy_data_extend_business_fields(values)
        values["commission_origin_line_id"] = self.id
        return res


class AccountInvoiceLineAgent(models.Model):
    _inherit = "account.invoice.line.agent"

    def _get_line_uom(self):
        return self.object_id.product_uom_id

    def _get_commission_date(self):
        return self.invoice_date or super()._get_commission_date()

    def _get_refunded_agent_lines(self, commission):
        """Return the agent lines of the sale this credit note line refunds.

        The refunded invoice line is the one the reversal copied the line
        from. Without one (a return invoiced from the order), it is the latest
        posted invoice line of the sale order lines, then the sale order line
        itself. Only a line of the same product counts.
        """
        refund_line = self.object_id
        origin_lines = refund_line.commission_origin_line_id
        if not origin_lines:
            origin_lines = refund_line.sale_line_ids.invoice_lines.filtered(
                lambda x: x.move_id.move_type == "out_invoice"
                and x.parent_state == "posted"
            ).sorted(lambda x: (x.date, x.id))[-1:]
        for lines in (origin_lines, refund_line.sale_line_ids):
            lines = lines.filtered(lambda x: x.product_id == refund_line.product_id)
            agent_lines = lines.agent_ids.filtered(
                lambda x: x.agent_id == self.agent_id and x.commission_id == commission
            )
            if agent_lines:
                return agent_lines
        return self.browse()

    def _get_commission_item(self, commission, product, quantity=0.0, date=None):
        # A credit note gives back the commission at the item the refunded
        # sale earned, not at the one matching its own date and quantity,
        # the same way it keeps the invoiced price. A sale that earned
        # nothing gives back nothing.
        if self.invoice_id.move_type == "out_refund":
            agent_lines = self._get_refunded_agent_lines(commission)
            if agent_lines:
                return agent_lines.applied_commission_item_id[:1]
        return super()._get_commission_item(commission, product, quantity, date)

    @api.depends(
        "object_id.price_subtotal",
        "object_id.product_id.commission_free",
        "object_id.quantity",
        "object_id.product_uom_id",
        "object_id.currency_id",
        "commission_id",
        "invoice_date",
    )
    def _compute_amount(self):  # pylint: disable=W8110 # Computes don't return
        for line in self:
            if line.commission_id and line.commission_id.commission_type == "product":
                inv_line = line.object_id
                line.amount = line._get_single_commission_amount(
                    line.commission_id,
                    inv_line.price_subtotal,
                    inv_line.product_id,
                    inv_line.quantity,
                )
                # Refunds commissions are negative
                if line.invoice_id.move_type and "refund" in line.invoice_id.move_type:
                    line.amount = -line.amount
            else:
                line._set_applied_commission()
                super(AccountInvoiceLineAgent, line)._compute_amount()
