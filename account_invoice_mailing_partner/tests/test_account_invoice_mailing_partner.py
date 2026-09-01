# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountInvoiceMailingPartner(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.partner_a
        cls.mailing_partner = cls.env["res.partner"].create(
            {"name": "Head Office", "parent_id": cls.customer.id, "type": "other"}
        )
        cls.child_contact = cls.env["res.partner"].create(
            {"name": "Branch", "parent_id": cls.customer.id, "type": "invoice"}
        )

    def _create_invoice(self, partner):
        return self.env["account.move"].create(
            {"move_type": "out_invoice", "partner_id": partner.id}
        )

    def test_01_no_mailing_partner_falls_back_to_partner(self):
        invoice = self._create_invoice(self.customer)
        self.assertFalse(invoice.invoice_mailing_partner_id)
        self.assertEqual(invoice.report_partner_id, self.customer)

    def test_02_mailing_partner_defaults_from_partner(self):
        self.customer.invoice_mailing_partner_id = self.mailing_partner
        invoice = self._create_invoice(self.customer)
        self.assertEqual(invoice.invoice_mailing_partner_id, self.mailing_partner)
        self.assertEqual(invoice.report_partner_id, self.mailing_partner)

    def test_03_child_contact_falls_back_to_commercial_partner(self):
        self.customer.invoice_mailing_partner_id = self.mailing_partner
        invoice = self._create_invoice(self.child_contact)
        self.assertEqual(invoice.invoice_mailing_partner_id, self.mailing_partner)

    def test_04_partner_change_is_not_retroactive(self):
        invoice = self._create_invoice(self.customer)
        self.assertFalse(invoice.invoice_mailing_partner_id)
        self.customer.invoice_mailing_partner_id = self.mailing_partner
        self.assertFalse(
            invoice.invoice_mailing_partner_id,
            "Setting the default on the partner must not update existing invoices.",
        )

    def test_05_manual_override_is_kept(self):
        self.customer.invoice_mailing_partner_id = self.mailing_partner
        invoice = self._create_invoice(self.customer)
        invoice.invoice_mailing_partner_id = self.child_contact
        invoice.invalidate_recordset()
        self.assertEqual(invoice.invoice_mailing_partner_id, self.child_contact)

    def test_06_common_mailing_partner_of_invoices(self):
        self.customer.invoice_mailing_partner_id = self.mailing_partner
        invoice_1 = self._create_invoice(self.customer)
        invoice_2 = self._create_invoice(self.customer)
        invoices = invoice_1 | invoice_2
        self.assertEqual(invoices._get_invoice_mailing_partner(), self.mailing_partner)
        invoice_2.invoice_mailing_partner_id = self.child_contact
        with self.assertRaises(UserError):
            invoices._get_invoice_mailing_partner()
