# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import Command
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestProductInvoiceName(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Customer"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Oxygen Concentrator Rental",
                "default_code": "RE0007",
                "invoice_name": "Rental Fee",
            }
        )
        cls.plain = cls.env["product.product"].create({"name": "Mask"})

    def _move(self, move_type, product):
        return self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner.id,
                "invoice_line_ids": [Command.create({"product_id": product.id})],
            }
        )

    def _line(self, move_type, product):
        return self._move(move_type, product).invoice_line_ids

    def test_customer_invoice_line_uses_the_invoice_name(self):
        self.assertEqual(self._line("out_invoice", self.product).name, "Rental Fee")
        self.assertEqual(self._line("out_refund", self.product).name, "Rental Fee")

    def test_sales_description_follows_the_invoice_name(self):
        self.product.description_sale = "Monthly, billed in advance"
        self.assertEqual(
            self._line("out_invoice", self.product).name,
            "Rental Fee\nMonthly, billed in advance",
        )

    def test_product_without_invoice_name_keeps_the_product_name(self):
        self.assertEqual(
            self._line("out_invoice", self.plain).name, self.plain.display_name
        )

    def test_vendor_bill_keeps_the_product_name(self):
        self.assertEqual(
            self._line("in_invoice", self.product).name, self.product.display_name
        )

    def test_hand_typed_label_survives_a_recompute(self):
        line = self._line("out_invoice", self.product)
        line.name = "Typed by hand"
        line._compute_name()
        self.assertEqual(line.name, "Typed by hand")

    def test_changing_the_product_on_the_form_relabels_the_line(self):
        move = self._move("out_invoice", self.product)
        with Form(move) as form:
            with form.invoice_line_ids.edit(0) as line:
                line.product_id = self.plain
                self.assertEqual(line.name, self.plain.display_name)
                line.product_id = self.product
                self.assertEqual(line.name, "Rental Fee")
