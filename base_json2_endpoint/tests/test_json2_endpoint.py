# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestJson2Endpoint(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model_partner = cls.env["ir.model"]._get("res.partner")
        cls.endpoint = cls.env["json2.endpoint"].create(
            {
                "name": "get_partners",
                "domain_name": "contacts",
                "description": "Return partner records",
                "model_id": cls.model_partner.id,
                "method": "search_read",
                "allowed_fields": "name,email",
                "default_domain": "[]",
            }
        )

    def test_create_endpoint(self):
        self.assertEqual(self.endpoint.model_name, "res.partner")
        self.assertEqual(self.endpoint._get_allowed_field_list(), ["name", "email"])

    def test_private_method_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["json2.endpoint"].create(
                {
                    "name": "bad_endpoint",
                    "domain_name": "test",
                    "model_id": self.model_partner.id,
                    "method": "_compute_display_name",
                }
            )

    def test_invalid_domain(self):
        with self.assertRaises(ValidationError):
            self.endpoint.default_domain = "not valid json"

    def test_invalid_allowed_fields(self):
        with self.assertRaises(ValidationError):
            self.endpoint.allowed_fields = "name,nonexistent_field"

    def test_empty_allowed_fields(self):
        self.endpoint.allowed_fields = False
        self.assertEqual(self.endpoint._get_allowed_field_list(), [])

    def test_unique_constraint(self):
        with self.assertRaises(Exception):
            self.env["json2.endpoint"].create(
                {
                    "name": "get_partners",
                    "domain_name": "contacts",
                    "model_id": self.model_partner.id,
                    "method": "read",
                }
            )

    def test_param_creation(self):
        param = self.env["json2.endpoint.param"].create(
            {
                "endpoint_id": self.endpoint.id,
                "name": "domain",
                "param_type": "list",
                "required": False,
                "default_value": "[]",
            }
        )
        self.assertEqual(param.endpoint_id, self.endpoint)
        self.assertIn(param, self.endpoint.param_ids)

    def test_domain_not_list(self):
        with self.assertRaises(ValidationError):
            self.endpoint.default_domain = '{"key": "value"}'
