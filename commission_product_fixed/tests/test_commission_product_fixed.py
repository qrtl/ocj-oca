# Copyright 2026 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestCommissionProductFixed(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_a = cls.env["product.product"].create({"name": "Product A"})
        cls.product_b = cls.env["product.product"].create({"name": "Product B"})
        cls.agent_x = cls.env["res.partner"].create(
            {"name": "Agent X", "agent": True}
        )
        cls.agent_y = cls.env["res.partner"].create(
            {"name": "Agent Y", "agent": True}
        )
        cls.commission_x = cls.env["commission"].create(
            {
                "name": "Agent X scheme",
                "commission_type": "product_fixed",
                "settlement_type": "sale_invoice",
                "product_line_ids": [
                    Command.create({"product_id": cls.product_a.id, "amount": 500}),
                    Command.create({"product_id": cls.product_b.id, "amount": 300}),
                ],
            }
        )
        cls.commission_y = cls.env["commission"].create(
            {
                "name": "Agent Y scheme",
                "commission_type": "product_fixed",
                "settlement_type": "sale_invoice",
                "product_line_ids": [
                    Command.create({"product_id": cls.product_a.id, "amount": 650}),
                ],
            }
        )
        cls.customer = cls.env["res.partner"].create({"name": "Customer"})

    def _create_invoice(self, agent, commission, product, qty):
        return self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.customer.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "quantity": qty,
                            "price_unit": 1000,
                            "agent_ids": [
                                Command.create(
                                    {
                                        "agent_id": agent.id,
                                        "commission_id": commission.id,
                                    }
                                )
                            ],
                        }
                    )
                ],
            }
        )

    def test_fixed_amount_times_quantity(self):
        invoice = self._create_invoice(
            self.agent_x, self.commission_x, self.product_a, 3
        )
        agent_line = invoice.invoice_line_ids.agent_ids
        # 500 (fixed) x 3 (qty), independent of the 1000 price.
        self.assertEqual(agent_line.amount, 1500)

    def test_amount_differs_by_agent(self):
        invoice_x = self._create_invoice(
            self.agent_x, self.commission_x, self.product_a, 1
        )
        invoice_y = self._create_invoice(
            self.agent_y, self.commission_y, self.product_a, 1
        )
        self.assertEqual(invoice_x.invoice_line_ids.agent_ids.amount, 500)
        self.assertEqual(invoice_y.invoice_line_ids.agent_ids.amount, 650)

    def test_post_blocked_when_amount_missing(self):
        # Agent Y has no amount defined for product B.
        invoice = self._create_invoice(
            self.agent_y, self.commission_y, self.product_b, 1
        )
        self.assertEqual(invoice.invoice_line_ids.agent_ids.amount, 0)
        with self.assertRaises(ValidationError):
            invoice.action_post()

    def test_post_allowed_when_amount_defined(self):
        invoice = self._create_invoice(
            self.agent_x, self.commission_x, self.product_b, 2
        )
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(invoice.invoice_line_ids.agent_ids.amount, 600)
