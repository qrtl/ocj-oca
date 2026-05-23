# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
import os
from datetime import datetime, timedelta
from unittest import skipIf

from odoo.tests import new_test_user, tagged
from odoo.tests.common import HttpCase

CT_JSON = {"Content-Type": "application/json"}


@skipIf(os.getenv("SKIP_HTTP_CASE"), "HttpCase skipped")
@tagged("-at_install", "post_install")
class TestEndpointJson2Controller(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api_user = new_test_user(
            cls.env,
            "json2_api_user",
            groups="base.group_user",
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
                "json2_allowed_fields": "name,email",
                "json2_default_domain": '[["is_company", "=", true]]',
            }
        )
        cls.env["endpoint.json2.param"].create(
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
        cls.env["endpoint.endpoint"].search([])._handle_registry_sync()

    def tearDown(self):
        self.env.registry.clear_cache("routing")
        super().tearDown()

    def _call(self, route_group, endpoint_name, payload=None):
        url = f"/json2/{route_group}/{endpoint_name}"
        return self.url_open(
            url,
            data=json.dumps(payload or {}),
            headers=CT_JSON | self.bearer,
        )

    def _call_doc(self, path=""):
        url = f"/json2/doc{path}"
        return self.url_open(
            url,
            headers=self.bearer,
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
        endpoint = self.env["endpoint.endpoint"].create(
            {
                "name": "inactive_test",
                "route_group": "test",
                "exec_mode": "json2",
                "request_method": "POST",
                "request_content_type": "application/json",
                "auth_type": "bearer",
                "json2_model_id": self.model_partner.id,
                "json2_method": "search_read",
                "active": False,
            }
        )
        endpoint._handle_registry_sync()
        res = self._call("test", endpoint.name)
        self.assertEqual(res.status_code, 404)

    def test_dispatch_required_param_missing(self):
        endpoint = self.env["endpoint.endpoint"].create(
            {
                "name": "get_required",
                "route_group": "test",
                "exec_mode": "json2",
                "request_method": "POST",
                "request_content_type": "application/json",
                "auth_type": "bearer",
                "json2_model_id": self.model_partner.id,
                "json2_method": "search_read",
            }
        )
        self.env["endpoint.json2.param"].create(
            {
                "endpoint_id": endpoint.id,
                "name": "domain",
                "param_type": "list",
                "required": True,
            }
        )
        endpoint._handle_registry_sync()
        res = self._call("test", "get_required")
        self.assertEqual(res.status_code, 422)

    def test_dispatch_wrong_param_type(self):
        res = self._call("contacts", "get_partners", {"limit": "not_an_int"})
        self.assertEqual(res.status_code, 422)

    def test_dispatch_bool_rejected_for_int(self):
        res = self._call("contacts", "get_partners", {"limit": True})
        self.assertEqual(res.status_code, 422)

    def test_dispatch_int_accepted_for_float(self):
        endpoint = self.env["endpoint.endpoint"].create(
            {
                "name": "float_test",
                "route_group": "test",
                "exec_mode": "json2",
                "request_method": "POST",
                "request_content_type": "application/json",
                "auth_type": "bearer",
                "json2_model_id": self.model_partner.id,
                "json2_method": "search_read",
            }
        )
        self.env["endpoint.json2.param"].create(
            {
                "endpoint_id": endpoint.id,
                "name": "limit",
                "param_type": "float",
            }
        )
        endpoint._handle_registry_sync()
        res = self._call("test", "float_test", {"limit": 5})
        self.assertEqual(res.status_code, 200)

    def test_dispatch_default_domain_applied(self):
        self.env["res.partner"].create({"name": "Test Individual", "is_company": False})
        res = self._call("contacts", "get_partners")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        names = [row["name"] for row in data]
        self.assertNotIn("Test Individual", names)

    def test_dispatch_group_access_denied(self):
        group = self.env["res.groups"].create({"name": "Secret API Group"})
        endpoint = self.env["endpoint.endpoint"].create(
            {
                "name": "restricted",
                "route_group": "test",
                "exec_mode": "json2",
                "request_method": "POST",
                "request_content_type": "application/json",
                "auth_type": "bearer",
                "json2_model_id": self.model_partner.id,
                "json2_method": "search_read",
                "json2_group_ids": [(4, group.id)],
            }
        )
        endpoint._handle_registry_sync()
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

    def test_doc_unknown_domain(self):
        res = self._call_doc("/nonexistent")
        self.assertEqual(res.status_code, 404)

    def test_dispatch_code_snippet(self):
        partner = self.env["res.partner"].create(
            {"name": "Original Name", "ref": "SNIPPET_TEST"}
        )
        endpoint = self.env["endpoint.endpoint"].create(
            {
                "name": "update_name",
                "route_group": "test",
                "exec_mode": "json2",
                "request_method": "POST",
                "request_content_type": "application/json",
                "auth_type": "bearer",
                "json2_model_id": self.model_partner.id,
                "json2_code_snippet": (
                    'p = Model.search([("ref", "=", params["ref"])], limit=1)\n'
                    "if not p:\n"
                    '    raise exceptions.NotFound("Not found")\n'
                    'p.write({"name": params["new_name"]})\n'
                    'result = {"ref": p.ref, "name": p.name}\n'
                ),
            }
        )
        self.env["endpoint.json2.param"].create(
            [
                {
                    "endpoint_id": endpoint.id,
                    "name": "ref",
                    "param_type": "string",
                    "required": True,
                    "sequence": 10,
                },
                {
                    "endpoint_id": endpoint.id,
                    "name": "new_name",
                    "param_type": "string",
                    "required": True,
                    "sequence": 20,
                },
            ]
        )
        endpoint._handle_registry_sync()
        res = self._call(
            "test",
            "update_name",
            {"ref": "SNIPPET_TEST", "new_name": "Updated Name"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["name"], "Updated Name")
        partner.invalidate_recordset()
        self.assertEqual(partner.name, "Updated Name")

    def test_dispatch_code_snippet_missing_result(self):
        endpoint = self.env["endpoint.endpoint"].create(
            {
                "name": "bad_snippet",
                "route_group": "test",
                "exec_mode": "json2",
                "request_method": "POST",
                "request_content_type": "application/json",
                "auth_type": "bearer",
                "json2_model_id": self.model_partner.id,
                "json2_code_snippet": "x = 1",
            }
        )
        endpoint._handle_registry_sync()
        res = self._call("test", "bad_snippet")
        self.assertEqual(res.status_code, 500)

    def test_doc_excludes_restricted_endpoints(self):
        group = self.env["res.groups"].create({"name": "Hidden Group"})
        self.env["endpoint.endpoint"].create(
            {
                "name": "hidden",
                "route_group": "secret",
                "exec_mode": "json2",
                "request_method": "POST",
                "request_content_type": "application/json",
                "auth_type": "bearer",
                "json2_model_id": self.model_partner.id,
                "json2_method": "search_read",
                "json2_group_ids": [(4, group.id)],
            }
        )
        res = self._call_doc()
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertNotIn("secret", data)
