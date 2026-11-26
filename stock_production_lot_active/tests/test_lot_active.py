# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError, ValidationError

from odoo.addons.base.tests.common import BaseCommon


class TestLotActive(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product Lot Active",
                "tracking": "lot",
            }
        )
        cls.warehouse = cls.env.ref("stock.warehouse0")

    def test_duplicate_inactive_lot(self):
        self.env["stock.lot"].create(
            {
                "name": "stock_production_lot_active lot",
                "product_id": self.product.id,
                "company_id": self.warehouse.company_id.id,
                "active": False,
            }
        )
        # it should not be possible to create a new lot with the same name and company
        # for the same product even when the first lot is inactive
        with self.assertRaises(ValidationError):
            self.env["stock.lot"].create(
                {
                    "name": "stock_production_lot_active lot",
                    "product_id": self.product.id,
                    "company_id": self.warehouse.company_id.id,
                    "active": True,
                }
            )

    def test_archive_waits_until_the_stock_has_left(self):
        # Only internal locations count: a lot sold to a customer can be archived.
        product = self.env["product.product"].create(
            {"name": "Storable Lot Product", "is_storable": True, "tracking": "lot"}
        )
        lot = self.env["stock.lot"].create(
            {"name": "lot with stock", "product_id": product.id}
        )
        Quant = self.env["stock.quant"]
        stock = self.warehouse.lot_stock_id
        customers = self.env.ref("stock.stock_location_customers")
        Quant._update_available_quantity(product, stock, 1, lot_id=lot)
        with self.assertRaises(UserError):
            lot.action_archive()
        Quant._update_available_quantity(product, stock, -1, lot_id=lot)
        Quant._update_available_quantity(product, customers, 1, lot_id=lot)
        lot.action_archive()
        self.assertFalse(lot.active)
