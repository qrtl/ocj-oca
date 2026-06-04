# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)


from odoo import Command
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestAutoBillOnReceipt(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.picking_type_in = cls.warehouse.in_type_id
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")

        cls.vendor = cls.env["res.partner"].create({"name": "Test Vendor"})

        cls.category_auto = cls.env["product.category"].create(
            {"name": "Auto-bill Category", "auto_bill_on_receipt": True}
        )
        cls.category_plain = cls.env["product.category"].create(
            {"name": "Plain Category", "auto_bill_on_receipt": False}
        )

        cls.product_in_auto_categ = cls._create_product(
            "Storable In Auto Category", cls.category_auto
        )
        cls.product_in_plain_categ = cls._create_product(
            "Storable In Plain Category", cls.category_plain
        )
        cls.product_force_auto = cls._create_product(
            "Force Auto Product", cls.category_plain, auto_bill_on_receipt="auto"
        )
        cls.product_force_no_auto = cls._create_product(
            "Force No-Auto Product", cls.category_auto, auto_bill_on_receipt="no_auto"
        )

    @classmethod
    def _create_product(cls, name, category, **vals):
        return cls.env["product.product"].create(
            {
                "name": name,
                "is_storable": True,
                "standard_price": 10.0,
                "list_price": 20.0,
                "uom_id": cls.uom_unit.id,
                "categ_id": category.id,
                **vals,
            }
        )

    def _line(self, product, qty=1.0, price=10.0):
        return Command.create(
            {
                "product_id": product.id,
                "product_qty": qty,
                "product_uom_id": product.uom_id.id,
                "price_unit": price,
                "tax_ids": [Command.clear()],
            }
        )

    def _section(self, name):
        return Command.create(
            {"display_type": "line_section", "name": name, "product_qty": 0.0}
        )

    def _create_po(self, lines, confirm=True):
        po = self.env["purchase.order"].create(
            {"partner_id": self.vendor.id, "order_line": lines}
        )
        if confirm:
            po.button_confirm()
        return po

    def _receive(self, po, quantity=None):
        pickings = po.picking_ids.filtered(lambda p: p.state != "done")
        if quantity is not None:
            pickings.move_ids.quantity = quantity
        pickings.with_context(skip_backorder=True).button_validate()
        return pickings

    def _validate(self, picking, quantity):
        picking.move_ids.quantity = quantity
        picking.with_context(skip_backorder=True).button_validate()

    def _bills_of(self, po):
        return po.invoice_ids.sorted("id")

    def test_01_category_auto_bill_inherited_by_product(self):
        po = self._create_po([self._line(self.product_in_auto_categ, 5.0)])
        picking = self._receive(po)
        bills = self._bills_of(po)
        self.assertEqual(len(bills), 1)
        self.assertEqual(bills.state, "posted")
        self.assertEqual(bills.invoice_line_ids.quantity, 5.0)
        self.assertEqual(bills.invoice_origin, po.name)
        self.assertEqual(bills.invoice_date, picking.date_done.date())

    def test_02_product_override_auto_in_plain_category(self):
        po = self._create_po([self._line(self.product_force_auto, 3.0)])
        self._receive(po)
        bills = self._bills_of(po)
        self.assertEqual(len(bills), 1)
        self.assertEqual(bills.state, "posted")

    def test_03_product_override_no_auto_in_auto_category(self):
        po = self._create_po([self._line(self.product_force_no_auto, 2.0)])
        self._receive(po)
        self.assertFalse(self._bills_of(po))

    def test_04_block_auto_bill_on_po(self):
        po = self._create_po([self._line(self.product_in_auto_categ, 4.0)])
        po.block_auto_bill = True
        self._receive(po)
        self.assertFalse(self._bills_of(po))

    def test_05_mixed_lines_only_eligible_billed(self):
        po = self._create_po(
            [
                self._line(self.product_in_auto_categ, 2.0),
                self._line(self.product_in_plain_categ, 3.0, price=20.0),
            ]
        )
        self._receive(po)
        bills = self._bills_of(po)
        self.assertEqual(len(bills), 1)
        self.assertEqual(bills.state, "posted")
        self.assertEqual(bills.invoice_line_ids.product_id, self.product_in_auto_categ)
        self.assertEqual(bills.invoice_line_ids.quantity, 2.0)

    def test_06_partial_receipt_creates_one_bill_per_receipt(self):
        po = self._create_po([self._line(self.product_in_auto_categ, 10.0)])
        first_picking = po.picking_ids
        self._validate(first_picking, 4.0)
        bills = self._bills_of(po)
        self.assertEqual(len(bills), 1)
        self.assertEqual(bills.invoice_line_ids.quantity, 4.0)
        self.assertEqual(bills.state, "posted")

        backorder = po.picking_ids - first_picking
        self.assertEqual(len(backorder), 1)
        self._validate(backorder, 6.0)
        bills = self._bills_of(po)
        self.assertEqual(len(bills), 2)
        second_bill = bills - bills[0]
        self.assertEqual(second_bill.invoice_line_ids.quantity, 6.0)
        self.assertEqual(second_bill.state, "posted")

    def test_07_receipt_without_po_does_nothing(self):
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_in.id,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": self.product_in_auto_categ.id,
                            "product_uom_qty": 1.0,
                            "product_uom": self.product_in_auto_categ.uom_id.id,
                            "location_id": self.supplier_location.id,
                            "location_dest_id": self.stock_location.id,
                        }
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.move_ids.quantity = 1.0
        picking.move_ids.picked = True
        picking.button_validate()
        self.assertFalse(
            self.env["account.move"].search(
                [
                    ("move_type", "=", "in_invoice"),
                    ("invoice_origin", "like", picking.name),
                ]
            )
        )

    def test_08_idempotent_on_second_call(self):
        po = self._create_po([self._line(self.product_in_auto_categ, 5.0)])
        self._receive(po)
        self.assertEqual(len(self._bills_of(po)), 1)
        po.picking_ids._auto_create_vendor_bill()
        self.assertEqual(len(self._bills_of(po)), 1)

    def test_09_sections_carried_over_only_when_needed(self):
        po = self._create_po(
            [
                self._section("Billed Section"),
                self._line(self.product_in_auto_categ, 2.0),
                self._section("Skipped Section"),
                self._line(self.product_in_plain_categ, 3.0, price=20.0),
            ]
        )
        self._receive(po)
        bills = self._bills_of(po)
        self.assertEqual(len(bills), 1)

        sections = bills.invoice_line_ids.filtered(
            lambda line: line.display_type == "line_section"
        )
        # Only the section preceding an eligible line is carried over.
        self.assertEqual(sections.name, "Billed Section")

        product_lines = bills.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
        )
        self.assertEqual(product_lines.product_id, self.product_in_auto_categ)
        # Section header keeps its place above its product line.
        self.assertLess(sections.sequence, product_lines.sequence)
