# Copyright 2026 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        self._check_product_fixed_commission()
        return super().action_post()

    def _check_product_fixed_commission(self):
        """Block posting when a product/agent fixed commission is not defined.

        For every commission of type ``product_fixed`` assigned on an invoice
        line, the corresponding product must have an amount configured in the
        commission. Otherwise the commission cannot be determined and the
        invoice must not be posted.
        """
        missing = []
        for move in self.filtered(lambda m: m.move_type[:3] == "out"):
            for line in move.invoice_line_ids:
                if line.commission_free or not line.product_id:
                    continue
                for agent in line.agent_ids:
                    commission = agent.commission_id
                    if commission.commission_type != "product_fixed":
                        continue
                    if not commission._get_product_fixed_line(line.product_id):
                        missing.append(
                            self.env._(
                                "%(agent)s / %(product)s (commission: %(commission)s)",
                                agent=agent.agent_id.display_name,
                                product=line.product_id.display_name,
                                commission=commission.display_name,
                            )
                        )
        if missing:
            raise ValidationError(
                self.env._(
                    "No fixed commission amount is defined for the following "
                    "agent / product combinations:\n%s",
                    "\n".join("- %s" % m for m in missing),
                )
            )
