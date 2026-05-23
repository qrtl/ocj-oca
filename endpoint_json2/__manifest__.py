# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Endpoint JSON2",
    "summary": "Declarative JSON2-RPC endpoints on the endpoint stack.",
    "version": "19.0.1.0.0",
    "license": "LGPL-3",
    "development_status": "Beta",
    "author": "Quartile, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/web-api",
    "category": "Technical",
    "depends": ["endpoint"],
    "data": [
        "security/ir.model.access.csv",
        "views/endpoint_json2_view.xml",
    ],
    "demo": ["demo/endpoint_json2_demo.xml"],
    "installable": True,
}
