# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command

from odoo.addons.base.tests.common import BaseCommon


class TestSummaryInvoiceMailingPartner(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "test company",
                "currency_id": cls.env.ref("base.JPY").id,
                "country_id": cls.env.ref("base.jp").id,
                "tax_calculation_rounding_method": "round_globally",
            }
        )
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=[cls.company.id])
        )
        account_receivable = cls.env["account.account"].create(
            {
                "code": "test2",
                "name": "receivable",
                "reconcile": True,
                "account_type": "asset_receivable",
            }
        )
        cls.account_income = cls.env["account.account"].create(
            {"code": "test1", "name": "income", "account_type": "income"}
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "property_account_receivable_id": account_receivable.id,
            }
        )
        cls.head_office = cls.env["res.partner"].create(
            {"name": "Head Office", "parent_id": cls.partner.id, "type": "other"}
        )
        cls.accounting_firm = cls.env["res.partner"].create({"name": "Accounting Firm"})
        cls.product = cls.env["product.product"].create({"name": "Test Product"})
        tax_group = cls.env["account.tax.group"].create({"name": "Tax Group"})
        cls.tax_10 = cls.env["account.tax"].create(
            {
                "name": "Test Tax 10%",
                "amount": 10.0,
                "type_tax_use": "sale",
                "company_id": cls.company.id,
                "tax_group_id": tax_group.id,
            }
        )
        cls.env["account.journal"].create(
            {"code": "test", "name": "test", "type": "sale"}
        )

    def _create_invoice(self, amount, mailing_partner=None):
        invoice = (
            self.env["account.move"]
            .with_company(self.company)
            .create(
                {
                    "move_type": "out_invoice",
                    "partner_id": self.partner.id,
                    "currency_id": self.company.currency_id.id,
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "product_id": self.product.id,
                                "account_id": self.account_income.id,
                                "quantity": 1,
                                "price_unit": amount,
                                "tax_ids": [Command.set(self.tax_10.ids)],
                            }
                        )
                    ],
                }
            )
        )
        if mailing_partner is not None:
            invoice.invoice_mailing_partner_id = mailing_partner
        invoice.action_post()
        return invoice

    def test_01_billing_defaults_mailing_partner_from_partner(self):
        self.partner.invoice_mailing_partner_id = self.head_office
        billing = self.env["account.billing"].create({"partner_id": self.partner.id})
        self.assertEqual(billing.invoice_mailing_partner_id, self.head_office)

    def test_02_get_moves_filters_other_mailing_partner(self):
        self.partner.invoice_mailing_partner_id = self.head_office
        invoice_head_office = self._create_invoice(100)
        invoice_firm = self._create_invoice(200, mailing_partner=self.accounting_firm)
        billing = self.env["account.billing"].create(
            {"partner_id": self.partner.id, "bill_type": "out_invoice"}
        )
        billing.compute_lines()
        billed_moves = billing.billing_line_ids.move_id
        self.assertIn(invoice_head_office, billed_moves)
        self.assertNotIn(invoice_firm, billed_moves)

    def test_03_constrains_mailing_partner_conflict(self):
        invoice = self._create_invoice(100, mailing_partner=self.accounting_firm)
        with self.assertRaises(ValidationError):
            self.env["account.billing"].create(
                {
                    "partner_id": self.partner.id,
                    "invoice_mailing_partner_id": self.head_office.id,
                    "billing_line_ids": [Command.create({"move_id": invoice.id})],
                }
            )

    def test_04_create_billing_takes_mailing_partner_from_invoices(self):
        invoice_1 = self._create_invoice(100, mailing_partner=self.accounting_firm)
        invoice_2 = self._create_invoice(200, mailing_partner=self.accounting_firm)
        action = (invoice_1 | invoice_2).action_create_billing()
        billing = self.env["account.billing"].browse(action["res_id"])
        self.assertEqual(billing.invoice_mailing_partner_id, self.accounting_firm)

    def test_05_create_billing_rejects_mixed_mailing_partners(self):
        invoice_1 = self._create_invoice(100, mailing_partner=self.accounting_firm)
        invoice_2 = self._create_invoice(200, mailing_partner=self.head_office)
        with self.assertRaises(UserError):
            (invoice_1 | invoice_2).action_create_billing()

    def test_06_report_partner_is_the_mailing_partner(self):
        report = self.env.ref("l10n_jp_summary_invoice.report_jp_summary_invoice")
        billing = self.env["account.billing"].create({"partner_id": self.partner.id})
        self.assertEqual(report._get_report_partner(billing), self.partner)
        billing.invoice_mailing_partner_id = self.accounting_firm
        self.assertEqual(report._get_report_partner(billing), self.accounting_firm)
