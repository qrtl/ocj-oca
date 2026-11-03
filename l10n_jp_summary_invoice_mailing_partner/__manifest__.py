# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Japan Summary Invoice - Mailing Partner",
    "summary": "Address the summary invoice to a contact other than the "
    "billing partner",
    "version": "19.0.1.0.0",
    "category": "Japanese Localization",
    "author": "Quartile, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-japan",
    "license": "AGPL-3",
    "depends": ["account_invoice_mailing_partner", "l10n_jp_summary_invoice"],
    "data": [
        "views/account_billing_views.xml",
    ],
    "development_status": "Alpha",
    "maintainers": ["yostashiro"],
    "installable": True,
}
