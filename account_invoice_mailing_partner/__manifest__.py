# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Account Invoice Mailing Partner",
    "summary": "Address the invoice document to a contact other than the "
    "billing partner",
    "version": "19.0.1.0.0",
    "category": "Accounting/Accounting",
    "author": "Quartile, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-invoicing",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": [
        "reports/report_invoice_templates.xml",
        "views/account_move_views.xml",
        "views/res_partner_views.xml",
    ],
    "development_status": "Alpha",
    "maintainers": ["yostashiro"],
    "installable": True,
}
