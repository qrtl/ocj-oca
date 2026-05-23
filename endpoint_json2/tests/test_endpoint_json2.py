# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.exceptions import ValidationError

from .common import CommonEndpointJson2


class TestEndpointJson2(CommonEndpointJson2):
    def test_create_endpoint(self):
        self.assertEqual(self.endpoint.json2_model_name, "res.partner")
        self.assertEqual(
            self.endpoint._json2_get_allowed_field_list(), ["name", "email"]
        )

    def test_route_auto_computed(self):
        self.assertEqual(self.endpoint.route, "/json2/endpoint/contacts/get_partners")

    def test_private_method_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["endpoint.endpoint"].create(
                {
                    "name": "bad_endpoint",
                    "route_group": "test",
                    "exec_mode": "json2",
                    "request_method": "POST",
                    "request_content_type": "application/json",
                    "auth_type": "bearer",
                    "json2_model_id": self.model_partner.id,
                    "json2_method": "_compute_display_name",
                }
            )

    def test_invalid_domain(self):
        with self.assertRaises(ValidationError):
            self.endpoint.json2_default_domain = "not valid json"

    def test_domain_not_list(self):
        with self.assertRaises(ValidationError):
            self.endpoint.json2_default_domain = '{"key": "value"}'

    def test_invalid_allowed_fields(self):
        with self.assertRaises(ValidationError):
            self.endpoint.json2_allowed_fields = "name,nonexistent_field"

    def test_empty_allowed_fields(self):
        self.endpoint.json2_allowed_fields = False
        self.assertEqual(self.endpoint._json2_get_allowed_field_list(), [])

    def test_param_creation(self):
        param = self.env["endpoint.json2.param"].create(
            {
                "endpoint_id": self.endpoint.id,
                "name": "domain",
                "param_type": "list",
                "required": False,
                "default_value": "[]",
            }
        )
        self.assertEqual(param.endpoint_id, self.endpoint)
        self.assertIn(param, self.endpoint.json2_param_ids)

    def test_param_invalid_default_value(self):
        with self.assertRaises(ValidationError):
            self.env["endpoint.json2.param"].create(
                {
                    "endpoint_id": self.endpoint.id,
                    "name": "bad_param",
                    "param_type": "string",
                    "default_value": "not valid json",
                }
            )

    def test_filter_result_dict(self):
        result = {"name": "Test", "email": "a@b.c", "phone": "123"}
        filtered = self.endpoint._json2_filter_result(result, ["name", "email"])
        self.assertEqual(filtered, {"name": "Test", "email": "a@b.c"})

    def test_filter_result_list(self):
        result = [
            {"name": "A", "phone": "1"},
            {"name": "B", "phone": "2"},
        ]
        filtered = self.endpoint._json2_filter_result(result, ["name"])
        self.assertEqual(filtered, [{"name": "A"}, {"name": "B"}])

    def test_filter_result_passthrough(self):
        self.assertEqual(self.endpoint._json2_filter_result(42, ["name"]), 42)

    def test_filter_result_no_filter(self):
        result = {"name": "Test", "phone": "123"}
        self.assertEqual(self.endpoint._json2_filter_result(result, []), result)

    def test_request_method_must_be_post(self):
        with self.assertRaises(ValidationError):
            self.env["endpoint.endpoint"].create(
                {
                    "name": "get_test",
                    "route_group": "test",
                    "exec_mode": "json2",
                    "request_method": "GET",
                    "request_content_type": "application/json",
                    "auth_type": "bearer",
                    "json2_model_id": self.model_partner.id,
                    "json2_method": "search_read",
                }
            )

    def test_content_type_must_be_json(self):
        with self.assertRaises(ValidationError):
            self.env["endpoint.endpoint"].create(
                {
                    "name": "form_test",
                    "route_group": "test",
                    "exec_mode": "json2",
                    "request_method": "POST",
                    "request_content_type": "text/html",
                    "auth_type": "bearer",
                    "json2_model_id": self.model_partner.id,
                    "json2_method": "search_read",
                }
            )

    def test_validate_method_or_snippet_required(self):
        with self.assertRaises(ValidationError):
            self.env["endpoint.endpoint"].create(
                {
                    "name": "no_method_no_snippet",
                    "route_group": "test",
                    "exec_mode": "json2",
                    "request_method": "POST",
                    "request_content_type": "application/json",
                    "auth_type": "bearer",
                    "json2_model_id": self.model_partner.id,
                }
            )

    def test_validate_snippet_without_method_ok(self):
        ep = self.env["endpoint.endpoint"].create(
            {
                "name": "snippet_only",
                "route_group": "test",
                "exec_mode": "json2",
                "request_method": "POST",
                "request_content_type": "application/json",
                "auth_type": "bearer",
                "json2_model_id": self.model_partner.id,
                "json2_code_snippet": "result = []",
            }
        )
        self.assertTrue(ep.json2_code_snippet)
