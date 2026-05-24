# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.exceptions import ValidationError

from .common import CommonEndpointJson2


class TestEndpointJson2(CommonEndpointJson2):
    def test_create_endpoint(self):
        self.assertEqual(self.endpoint.json2_model_name, "res.partner")
        fields, aliases = self.endpoint._json2_parse_response_fields()
        self.assertEqual(fields, ["name", "email"])
        self.assertEqual(aliases, {})

    def test_route_auto_computed(self):
        self.assertEqual(self.endpoint.route, "/json2/contacts/get_partners")

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

    def test_invalid_response_fields(self):
        with self.assertRaises(ValidationError):
            self.endpoint.json2_response_fields = "name\nnonexistent_field"

    def test_empty_response_fields(self):
        self.endpoint.json2_response_fields = False
        fields, aliases = self.endpoint._json2_parse_response_fields()
        self.assertEqual(fields, [])
        self.assertEqual(aliases, {})

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
        aliased = self.endpoint._json2_apply_aliases(filtered, {"email": "mail"})
        self.assertEqual(aliased, {"name": "Test", "mail": "a@b.c"})

    def test_filter_result_list(self):
        result = [
            {"name": "A", "phone": "1"},
            {"name": "B", "phone": "2"},
        ]
        filtered = self.endpoint._json2_filter_result(result, ["name"])
        self.assertEqual(filtered, [{"name": "A"}, {"name": "B"}])
        aliased = self.endpoint._json2_apply_aliases(filtered, {"name": "label"})
        self.assertEqual(aliased, [{"label": "A"}, {"label": "B"}])

    def test_filter_result_passthrough(self):
        self.assertEqual(self.endpoint._json2_filter_result(42, ["name"]), 42)
        self.assertEqual(self.endpoint._json2_apply_aliases(42, {"name": "n"}), 42)

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

    def test_dotted_response_fields_valid(self):
        self.endpoint.json2_response_fields = "name\ncountry_id.name country"
        fields, aliases = self.endpoint._json2_parse_response_fields()
        self.assertEqual(fields, ["name", "country_id.name"])
        self.assertEqual(aliases, {"country_id.name": "country"})

    def test_dotted_response_fields_invalid_base(self):
        with self.assertRaises(ValidationError):
            self.endpoint.json2_response_fields = "name\nnonexistent_id.name"

    def test_dotted_response_fields_non_m2o(self):
        with self.assertRaises(ValidationError):
            self.endpoint.json2_response_fields = "name\nemail.something"

    def test_dotted_response_fields_invalid_sub(self):
        with self.assertRaises(ValidationError):
            self.endpoint.json2_response_fields = "name\ncountry_id.nonexistent"

    def test_parse_dotted_fields(self):
        allowed = ["name", "country_id.name", "country_id.code", "email"]
        dotted = self.endpoint._json2_parse_dotted_fields(allowed)
        self.assertEqual(dotted, {"country_id": ["name", "code"]})

    def test_resolve_dotted_fields(self):
        country = self.env["res.country"].search([("code", "=", "JP")], limit=1)
        self.assertTrue(country)
        result = [
            {"id": 1, "name": "Test", "country_id": (country.id, country.display_name)},
            {"id": 2, "name": "Test2", "country_id": False},
        ]
        dotted_map = {"country_id": ["name", "code"]}
        self.endpoint._json2_resolve_dotted_fields(self.env, result, dotted_map)
        self.assertEqual(result[0]["country_id.name"], country.name)
        self.assertEqual(result[0]["country_id.code"], "JP")
        self.assertFalse(result[1]["country_id.name"])
        self.assertFalse(result[1]["country_id.code"])

    def test_dotted_response_fields_m2m_valid(self):
        self.endpoint.json2_response_fields = "name\ncategory_id.name"
        fields, _aliases = self.endpoint._json2_parse_response_fields()
        self.assertEqual(fields, ["name", "category_id.name"])

    def test_resolve_dotted_fields_x2many(self):
        tags = self.env["res.partner.category"].search([], limit=2)
        if len(tags) < 2:
            tags = self.env["res.partner.category"].create(
                [{"name": "TagA"}, {"name": "TagB"}]
            )
        result = [
            {"id": 1, "name": "Test", "category_id": tags.ids},
            {"id": 2, "name": "Test2", "category_id": []},
        ]
        dotted_map = {"category_id": ["name"]}
        self.endpoint._json2_resolve_dotted_fields(self.env, result, dotted_map)
        self.assertEqual(result[0]["category_id.name"], tags.mapped("name"))
        self.assertEqual(result[1]["category_id.name"], [])

    def test_filter_excludes_base_when_only_dotted(self):
        result = {
            "name": "Test",
            "country_id": (1, "Japan"),
            "country_id.name": "Japan",
        }
        filtered = self.endpoint._json2_filter_result(
            result, ["name", "country_id.name"]
        )
        self.assertEqual(filtered, {"name": "Test", "country_id.name": "Japan"})
        self.assertNotIn("country_id", filtered)
        aliased = self.endpoint._json2_apply_aliases(
            filtered, {"country_id.name": "country"}
        )
        self.assertEqual(aliased, {"name": "Test", "country": "Japan"})
