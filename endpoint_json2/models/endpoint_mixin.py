# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json

import werkzeug

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.service.model import get_public_method
from odoo.tools.safe_eval import json as safe_json
from odoo.tools.safe_eval import safe_eval, wrap_module

PARAM_TYPE_MAP = {
    "string": str,
    "integer": int,
    "float": float,
    "boolean": bool,
    "list": list,
    "dict": dict,
}


class EndpointMixin(models.AbstractModel):
    _inherit = "endpoint.mixin"

    json2_model_id = fields.Many2one(
        "ir.model",
        string="Model",
        ondelete="cascade",
        domain=[("transient", "=", False)],
    )
    json2_model_name = fields.Char(
        related="json2_model_id.model",
        store=True,
    )
    json2_method = fields.Char(
        string="Method",
        help="Public method name on the target model.",
    )
    json2_description = fields.Text(
        string="Description",
        help="Displayed in the API documentation endpoint.",
    )
    json2_allowed_fields = fields.Char(
        string="Allowed Fields",
        help="Comma-separated list of field names the API may return. "
        "Leave empty to allow all fields.",
    )
    json2_default_domain = fields.Char(
        string="Default Domain",
        default="[]",
        help="Default domain filter applied before calling the method (JSON format).",
    )
    json2_group_ids = fields.Many2many(
        "res.groups",
        string="Allowed Groups",
        help="Groups allowed to call this endpoint. "
        "Leave empty to allow any authenticated API user.",
    )
    json2_param_ids = fields.One2many(
        "endpoint.json2.param",
        "endpoint_id",
        string="Parameters",
    )
    json2_code_snippet = fields.Text(
        string="Code Snippet",
        help="Optional Python code executed instead of the model method. "
        "Available variables: Model, params, env, json, exceptions. "
        "Use record.write({...}) for updates. "
        "Set the result in the 'result' variable.",
    )

    def _selection_exec_mode(self):
        return super()._selection_exec_mode() + [("json2", "JSON2-RPC")]

    @api.depends("route", "exec_mode", "route_group", "name")
    def _compute_route(self):
        for rec in self:
            if rec.exec_mode == "json2" and rec.route_group and rec.name:
                rec.route = f"/json2/endpoint/{rec.route_group}/{rec.name}"
            else:
                rec.route = rec._clean_route()

    @api.onchange("exec_mode")
    def _onchange_exec_mode_json2_defaults(self):
        if self.exec_mode == "json2":
            self.request_method = "POST"
            self.request_content_type = "application/json"
            self.auth_type = "bearer"

    # --- Validation ---

    def _validate_exec__json2(self):
        if not self.json2_model_id:
            raise ValidationError(
                self.env._("Exec mode is set to 'JSON2-RPC': you must select a model.")
            )
        if not self.json2_method and not self.json2_code_snippet:
            raise ValidationError(
                self.env._(
                    "Exec mode is set to 'JSON2-RPC': "
                    "you must specify a method or provide a code snippet."
                )
            )

    @api.constrains("request_method", "request_content_type", "exec_mode")
    def _check_json2_request_settings(self):
        for rec in self:
            if rec.exec_mode != "json2":
                continue
            if rec.request_method != "POST":
                raise ValidationError(
                    self.env._(
                        "JSON2-RPC endpoints must use POST "
                        "(parameters are sent as a JSON body)."
                    )
                )
            if rec.request_content_type != "application/json":
                raise ValidationError(
                    self.env._(
                        "JSON2-RPC endpoints must use 'application/json' "
                        "content type."
                    )
                )

    @api.constrains("json2_method")
    def _check_json2_method(self):
        for rec in self:
            if rec.json2_method and rec.json2_method.startswith("_"):
                raise ValidationError(
                    self.env._(
                        "Private methods (starting with '_') cannot be exposed."
                    )
                )

    @api.constrains("json2_default_domain")
    def _check_json2_default_domain(self):
        for rec in self:
            if not rec.json2_default_domain:
                continue
            try:
                domain = json.loads(rec.json2_default_domain)
                if not isinstance(domain, list):
                    raise ValueError
            except (json.JSONDecodeError, ValueError):
                raise ValidationError(
                    self.env._("Default domain must be a valid JSON list.")
                ) from None

    @api.constrains("json2_allowed_fields", "json2_model_id")
    def _check_json2_allowed_fields(self):
        for rec in self:
            if not rec.json2_allowed_fields or not rec.json2_model_name:
                continue
            if rec.json2_model_name not in self.env:
                continue
            Model = self.env[rec.json2_model_name]
            field_names = [f.strip() for f in rec.json2_allowed_fields.split(",")]
            invalid = [f for f in field_names if f not in Model._fields]
            if invalid:
                raise ValidationError(
                    self.env._(
                        "Invalid field(s) for %(model)s: %(fields)s",
                        model=rec.json2_model_name,
                        fields=", ".join(invalid),
                    )
                )

    # --- Execution ---

    def _handle_exec__json2(self, request):
        self._json2_check_group_access(request)
        kwargs = request.get_json_data() or {}
        params = self._json2_validate_params(kwargs)
        Model = request.env[self.json2_model_name].sudo()
        default_domain = json.loads(self.json2_default_domain or "[]")
        if default_domain:
            params["domain"] = default_domain + (params.get("domain") or [])
        if self.json2_code_snippet:
            result = self._json2_exec_code_snippet(Model, params)
        else:
            try:
                method = get_public_method(Model, self.json2_method)
            except (AttributeError, AccessError) as exc:
                raise werkzeug.exceptions.NotFound(str(exc)) from exc
            result = method(Model, **params)
        allowed = self._json2_get_allowed_field_list()
        result = self._json2_filter_result(result, allowed)
        return {"payload": result}

    def _json2_exec_code_snippet(self, Model, params):
        eval_ctx = {
            "Model": Model,
            "params": params,
            "env": Model.env,
            "json": safe_json,
            "exceptions": wrap_module(werkzeug.exceptions, [
                "BadRequest", "Forbidden", "NotFound",
                "UnprocessableEntity", "InternalServerError",
            ]),
        }
        safe_eval(self.json2_code_snippet, eval_ctx, mode="exec")
        if "result" not in eval_ctx:
            raise werkzeug.exceptions.InternalServerError(
                "Code snippet must set a 'result' variable."
            )
        return eval_ctx["result"]

    def _json2_check_group_access(self, request):
        if not self.json2_group_ids:
            return
        if not (self.json2_group_ids & request.env.user.groups_id):
            raise werkzeug.exceptions.Forbidden(
                "User does not belong to any allowed group"
            )

    def _json2_validate_params(self, kwargs):
        params = {}
        for param_def in self.json2_param_ids:
            value = kwargs.pop(param_def.name, None)
            if value is None and param_def.default_value:
                value = json.loads(param_def.default_value)
            if value is None and param_def.required:
                raise werkzeug.exceptions.UnprocessableEntity(
                    f"Missing required parameter: {param_def.name}"
                )
            if value is not None:
                expected_type = PARAM_TYPE_MAP.get(param_def.param_type)
                if expected_type and not self._json2_check_param_type(
                    value, expected_type
                ):
                    raise werkzeug.exceptions.UnprocessableEntity(
                        f"Parameter {param_def.name!r} must be of type "
                        f"{param_def.param_type}"
                    )
            params[param_def.name] = value
        return params

    @staticmethod
    def _json2_check_param_type(value, expected_type):
        if isinstance(value, bool) and expected_type is not bool:
            return False
        if expected_type is float:
            return isinstance(value, (int, float))
        return isinstance(value, expected_type)

    def _json2_get_allowed_field_list(self):
        self.ensure_one()
        if not self.json2_allowed_fields:
            return []
        return [f.strip() for f in self.json2_allowed_fields.split(",")]

    @staticmethod
    def _json2_filter_result(result, allowed_fields):
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
            return {k: v for k, v in result.items() if k in allowed_fields}
        return result
