# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging

from werkzeug.exceptions import Forbidden, NotFound, UnprocessableEntity

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.service.model import get_public_method

_logger = logging.getLogger(__name__)

PARAM_TYPE_MAP = {
    "string": str,
    "integer": int,
    "float": float,
    "boolean": bool,
    "list": list,
    "dict": dict,
}


class Json2EndpointController(http.Controller):
    @http.route(
        "/json2/endpoint/<string:domain>/<string:endpoint_name>",
        methods=["POST"],
        auth="bearer",
        type="json2",
        save_session=False,
    )
    def dispatch(self, domain, endpoint_name, **kwargs):
        endpoint = self._get_endpoint(domain, endpoint_name)
        self._check_group_access(endpoint)
        params = self._validate_params(endpoint, kwargs)
        return self._execute(endpoint, params)

    @http.route(
        "/json2/endpoint/doc",
        methods=["GET"],
        auth="bearer",
        type="json2",
        readonly=True,
        save_session=False,
    )
    def doc_index(self):
        endpoints = self._get_accessible_endpoints()
        result = {}
        for ep in endpoints:
            result.setdefault(ep.domain_name, []).append(
                self._endpoint_to_doc(ep)
            )
        return result

    @http.route(
        "/json2/endpoint/doc/<string:domain>",
        methods=["GET"],
        auth="bearer",
        type="json2",
        readonly=True,
        save_session=False,
    )
    def doc_domain(self, domain):
        endpoints = self._get_accessible_endpoints(
            [("domain_name", "=", domain)]
        )
        if not endpoints:
            raise NotFound(f"No endpoints found for domain {domain!r}")
        return [self._endpoint_to_doc(ep) for ep in endpoints]

    def _get_accessible_endpoints(self, extra_domain=None):
        domain = extra_domain or []
        all_endpoints = (
            request.env["json2.endpoint"].sudo().search(domain)
        )
        user = request.env.user
        return all_endpoints.filtered(
            lambda ep: not ep.group_ids or (ep.group_ids & user.groups_id)
        )

    def _endpoint_to_doc(self, endpoint):
        return {
            "name": endpoint.name,
            "description": endpoint.description or "",
            "method": endpoint.method,
            "model": endpoint.model_name,
            "url": f"/json2/endpoint/{endpoint.domain_name}/{endpoint.name}",
            "parameters": [
                {
                    "name": p.name,
                    "type": p.param_type,
                    "required": p.required,
                    "description": p.description or "",
                    "default": p.default_value,
                }
                for p in endpoint.param_ids
            ],
        }

    def _get_endpoint(self, domain, endpoint_name):
        endpoint = (
            request.env["json2.endpoint"]
            .sudo()
            .search(
                [
                    ("domain_name", "=", domain),
                    ("name", "=", endpoint_name),
                    ("active", "=", True),
                ],
                limit=1,
            )
        )
        if not endpoint:
            raise NotFound(
                f"Endpoint {domain!r}/{endpoint_name!r} not found or inactive"
            )
        return endpoint

    def _check_group_access(self, endpoint):
        if not endpoint.group_ids:
            return
        if not (endpoint.group_ids & request.env.user.groups_id):
            raise Forbidden("User does not belong to any allowed group")

    def _validate_params(self, endpoint, kwargs):
        params = {}
        for param_def in endpoint.param_ids:
            value = kwargs.pop(param_def.name, None)
            if value is None and param_def.default_value:
                value = json.loads(param_def.default_value)
            if value is None and param_def.required:
                raise UnprocessableEntity(
                    f"Missing required parameter: {param_def.name}"
                )
            if value is not None:
                expected_type = PARAM_TYPE_MAP.get(param_def.param_type)
                if expected_type and not self._check_param_type(
                    value, expected_type
                ):
                    raise UnprocessableEntity(
                        f"Parameter {param_def.name!r} must be of type "
                        f"{param_def.param_type}"
                    )
            params[param_def.name] = value
        return params

    @staticmethod
    def _check_param_type(value, expected_type):
        if isinstance(value, bool) and expected_type is not bool:
            return False
        if expected_type is float:
            return isinstance(value, (int, float))
        return isinstance(value, expected_type)

    def _execute(self, endpoint, params):
        Model = request.env[endpoint.model_name].sudo()
        try:
            method = get_public_method(Model, endpoint.method)
        except (AttributeError, AccessError) as exc:
            raise NotFound(str(exc)) from exc
        default_domain = json.loads(endpoint.default_domain or "[]")
        if default_domain:
            params["domain"] = default_domain + (params.get("domain") or [])
        result = method(Model, **params)
        return self._filter_result(result, endpoint._get_allowed_field_list())

    @staticmethod
    def _filter_result(result, allowed_fields):
        if not allowed_fields:
            return result
        if isinstance(result, list):
            return [
                {k: v for k, v in row.items() if k in allowed_fields}
                if isinstance(row, dict)
                else row
                for row in result
            ]
        if isinstance(result, dict):
            return {
                k: v for k, v in result.items() if k in allowed_fields
            }
        return result
