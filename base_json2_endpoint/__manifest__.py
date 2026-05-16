# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Base JSON2 Endpoint",
    "version": "19.0.1.0.0",
    "depends": ["base"],
    "author": "Quartile, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/rest-framework",
    "category": "Technical",
    "data": [
        "security/json2_endpoint_security.xml",
        "security/ir.model.access.csv",
        "views/json2_endpoint_views.xml",
        "views/json2_endpoint_menus.xml",
    ],
    "demo": [
        "demo/json2_endpoint_demo.xml",
    ],
    "installable": True,
}
