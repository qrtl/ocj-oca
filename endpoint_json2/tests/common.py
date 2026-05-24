# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class CommonEndpointJson2(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model_partner = cls.env["ir.model"]._get("res.partner")
        cls.endpoint = cls.env["endpoint.endpoint"].create(
            {
                "name": "get_partners",
                "route_group": "contacts",
                "exec_mode": "json2",
                "request_method": "POST",
                "request_content_type": "application/json",
                "auth_type": "bearer",
                "json2_description": "Return partner records",
                "json2_model_id": cls.model_partner.id,
                "json2_method": "search_read",
                "json2_response_fields": "name\nemail",
                "json2_default_domain": "[]",
            }
        )
