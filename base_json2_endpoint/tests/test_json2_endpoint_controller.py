# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from datetime import datetime, timedelta

from odoo.tests import new_test_user, tagged
from odoo.tests.common import HttpCase

CT_JSON = {"Content-Type": "application/json; charset=utf-8"}


@tagged("-at_install", "post_install")
class TestJson2EndpointController(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api_user = new_test_user(
            cls.env,
            "json2_api_user",
            groups="base.group_user,base_json2_endpoint.group_json2_endpoint_user",
        )
        key = (
            cls.api_user.with_user(cls.api_user)
            .env["res.users.apikeys"]
            ._generate(
                scope="rpc",
                name="test",
                expiration_date=datetime.now() + timedelta(days=1),
            )
        )
        cls.bearer = {"Authorization": f"Bearer {key}"}
        cls.model_partner = cls.env["ir.model"]._get("res.partner")
        cls.endpoint = cls.env["json2.endpoint"].create(
            {
                "name": "get_partners",
                "domain_name": "contacts",
                "description": "Return partner records",
                "model_id": cls.model_partner.id,
                "method": "search_read",
                "allowed_fields": "name,email",
                "default_domain": '[["is_company", "=", true]]',
            }
        )
        cls.env["json2.endpoint.param"].create(
            [
                {
                    "endpoint_id": cls.endpoint.id,
                    "name": "domain",
                    "param_type": "list",
                    "required": False,
                    "default_value": "[]",
                    "sequence": 10,
                },
                {
                    "endpoint_id": cls.endpoint.id,
                    "name": "limit",
                    "param_type": "integer",
                    "required": False,
                    "default_value": "10",
                    "sequence": 20,
                },
                {
                    "endpoint_id": cls.endpoint.id,
                    "name": "fields",
                    "param_type": "list",
                    "required": False,
                    "sequence": 30,
                },
            ]
        )

    def _call(self, domain, endpoint_name, payload=None, method="POST"):
        url = f"/json2/endpoint/{domain}/{endpoint_name}"
        return self.url_open(
            url,
            data=json.dumps(payload or {}),
            headers=CT_JSON | self.bearer,
        )

    def _call_doc(self, path=""):
        url = f"/json2/endpoint/doc{path}"
        return self.url_open(
            url,
            data="{}",
            headers=CT_JSON | self.bearer,
            allow_redirects=False,
        )

    def test_dispatch_happy_path(self):
        res = self._call("contacts", "get_partners")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        for row in data:
            self.assertIn("name", row)
            self.assertNotIn("phone", row)

    def test_dispatch_with_limit(self):
        res = self._call("contacts", "get_partners", {"limit": 2})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertLessEqual(len(data), 2)

    def test_dispatch_not_found(self):
        res = self._call("contacts", "nonexistent")
        self.assertEqual(res.status_code, 404)

    def test_dispatch_unknown_domain(self):
        res = self._call("unknown_domain", "get_partners")
        self.assertEqual(res.status_code, 404)

    def test_dispatch_inactive_endpoint(self):
        endpoint = self.env["json2.endpoint"].create(
            {
                "name": "inactive_test",
                "domain_name": "test",
                "model_id": self.model_partner.id,
                "method": "search_read",
                "active": False,
            }
        )
        res = self._call("test", endpoint.name)
        self.assertEqual(res.status_code, 404)

    def test_dispatch_required_param_missing(self):
        endpoint = self.env["json2.endpoint"].create(
            {
                "name": "get_required",
                "domain_name": "test",
                "model_id": self.model_partner.id,
                "method": "search_read",
            }
        )
        self.env["json2.endpoint.param"].create(
            {
                "endpoint_id": endpoint.id,
                "name": "domain",
                "param_type": "list",
                "required": True,
            }
        )
        res = self._call("test", "get_required")
        self.assertEqual(res.status_code, 422)

    def test_dispatch_wrong_param_type(self):
        res = self._call("contacts", "get_partners", {"limit": "not_an_int"})
        self.assertEqual(res.status_code, 422)

    def test_dispatch_bool_rejected_for_int(self):
        res = self._call("contacts", "get_partners", {"limit": True})
        self.assertEqual(res.status_code, 422)

    def test_dispatch_int_accepted_for_float(self):
        endpoint = self.env["json2.endpoint"].create(
            {
                "name": "float_test",
                "domain_name": "test",
                "model_id": self.model_partner.id,
                "method": "search_read",
            }
        )
        self.env["json2.endpoint.param"].create(
            {
                "endpoint_id": endpoint.id,
                "name": "limit",
                "param_type": "float",
            }
        )
        res = self._call("test", "float_test", {"limit": 5})
        self.assertEqual(res.status_code, 200)

    def test_dispatch_default_domain_applied(self):
        self.env["res.partner"].create(
            {"name": "Test Individual", "is_company": False}
        )
        res = self._call("contacts", "get_partners")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data)
        names = [row["name"] for row in data]
        self.assertNotIn("Test Individual", names)

    def test_dispatch_group_access_denied(self):
        group = self.env["res.groups"].create({"name": "Secret API Group"})
        endpoint = self.env["json2.endpoint"].create(
            {
                "name": "restricted",
                "domain_name": "test",
                "model_id": self.model_partner.id,
                "method": "search_read",
                "group_ids": [(4, group.id)],
            }
        )
        res = self._call("test", "restricted")
        self.assertEqual(res.status_code, 403)

    def test_doc_index(self):
        res = self._call_doc()
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, dict)
        self.assertIn("contacts", data)
        names = [ep["name"] for ep in data["contacts"]]
        self.assertIn("get_partners", names)

    def test_doc_domain_filter(self):
        res = self._call_doc("/contacts")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertTrue(data)
        urls = [ep["url"] for ep in data]
        self.assertTrue(
            all(url.startswith("/json2/endpoint/contacts/") for url in urls)
        )

    def test_doc_unknown_domain(self):
        res = self._call_doc("/nonexistent")
        self.assertEqual(res.status_code, 404)

    def test_doc_excludes_restricted_endpoints(self):
        group = self.env["res.groups"].create({"name": "Hidden Group"})
        self.env["json2.endpoint"].create(
            {
                "name": "hidden",
                "domain_name": "secret",
                "model_id": self.model_partner.id,
                "method": "search_read",
                "group_ids": [(4, group.id)],
            }
        )
        res = self._call_doc()
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertNotIn("secret", data)

    def test_filter_result_dict(self):
        from odoo.addons.base_json2_endpoint.controllers.main import (
            Json2EndpointController,
        )

        ctrl = Json2EndpointController()
        result = {"name": "Test", "email": "a@b.c", "phone": "123"}
        filtered = ctrl._filter_result(result, ["name", "email"])
        self.assertEqual(filtered, {"name": "Test", "email": "a@b.c"})

    def test_filter_result_list(self):
        from odoo.addons.base_json2_endpoint.controllers.main import (
            Json2EndpointController,
        )

        ctrl = Json2EndpointController()
        result = [
            {"name": "A", "phone": "1"},
            {"name": "B", "phone": "2"},
        ]
        filtered = ctrl._filter_result(result, ["name"])
        self.assertEqual(filtered, [{"name": "A"}, {"name": "B"}])

    def test_filter_result_passthrough(self):
        from odoo.addons.base_json2_endpoint.controllers.main import (
            Json2EndpointController,
        )

        ctrl = Json2EndpointController()
        self.assertEqual(ctrl._filter_result(42, ["name"]), 42)
