# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Json2Endpoint(models.Model):
    _name = "json2.endpoint"
    _description = "JSON2 Endpoint"
    _order = "domain_name, name"

    name = fields.Char(required=True)
    domain_name = fields.Char(
        string="Domain",
        required=True,
        help="Logical grouping for the API facade model (e.g. sales, inventory).",
    )
    description = fields.Text(help="Displayed in the API documentation endpoint.")
    model_id = fields.Many2one(
        "ir.model",
        required=True,
        ondelete="cascade",
        domain=[("transient", "=", False)],
    )
    model_name = fields.Char(string="Model Name", related="model_id.model", store=True)
    method = fields.Char(
        required=True,
        help="Public method name on the target model.",
    )
    allowed_fields = fields.Char(
        help="Comma-separated list of field names the API may return. "
        "Leave empty to allow all fields readable by the API user.",
    )
    default_domain = fields.Char(
        default="[]",
        help="Default domain filter applied before calling the method (JSON format).",
    )
    group_ids = fields.Many2many(
        "res.groups",
        string="Allowed Groups",
        help="Groups allowed to call this endpoint. "
        "Leave empty to allow any authenticated API user.",
    )
    active = fields.Boolean(default=True)
    param_ids = fields.One2many(
        "json2.endpoint.param",
        "endpoint_id",
        string="Parameters",
    )

    _unique_domain_name = models.Constraint(
        "UNIQUE(domain_name, name)",
        "Endpoint name must be unique within a domain.",
    )

    @api.constrains("method")
    def _check_method(self):
        for rec in self:
            if rec.method.startswith("_"):
                raise ValidationError(
                    self.env._("Private methods (starting with '_') cannot be exposed.")
                )

    @api.constrains("default_domain")
    def _check_default_domain(self):
        for rec in self:
            try:
                domain = json.loads(rec.default_domain or "[]")
                if not isinstance(domain, list):
                    raise ValueError
            except (json.JSONDecodeError, ValueError):
                raise ValidationError(
                    self.env._("Default domain must be a valid JSON list.")
                ) from None

    @api.constrains("allowed_fields", "model_id")
    def _check_allowed_fields(self):
        for rec in self:
            if not rec.allowed_fields or not rec.model_name:
                continue
            if rec.model_name not in self.env:
                continue
            Model = self.env[rec.model_name]
            field_names = [f.strip() for f in rec.allowed_fields.split(",")]
            invalid = [f for f in field_names if f not in Model._fields]
            if invalid:
                raise ValidationError(
                    self.env._(
                        "Invalid field(s) for %(model)s: %(fields)s",
                        model=rec.model_name,
                        fields=", ".join(invalid),
                    )
                )

    def _get_allowed_field_list(self):
        self.ensure_one()
        if not self.allowed_fields:
            return []
        return [f.strip() for f in self.allowed_fields.split(",")]


class Json2EndpointParam(models.Model):
    _name = "json2.endpoint.param"
    _description = "JSON2 Endpoint Parameter"
    _order = "sequence, id"

    endpoint_id = fields.Many2one(
        "json2.endpoint",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(required=True, help="Parameter name as sent in the JSON body.")
    description = fields.Char(help="Displayed in the API documentation.")
    param_type = fields.Selection(
        [
            ("string", "String"),
            ("integer", "Integer"),
            ("float", "Float"),
            ("boolean", "Boolean"),
            ("list", "List"),
            ("dict", "Dict"),
        ],
        string="Type",
        required=True,
        default="string",
    )
    required = fields.Boolean()
    default_value = fields.Char(
        help="Default value (JSON-encoded) when the parameter is not provided.",
    )
    sequence = fields.Integer(default=10)

    @api.constrains("default_value")
    def _check_default_value(self):
        for rec in self:
            if not rec.default_value:
                continue
            try:
                json.loads(rec.default_value)
            except json.JSONDecodeError:
                raise ValidationError(
                    self.env._(
                        "Default value must be valid JSON: %(value)s",
                        value=rec.default_value,
                    )
                ) from None
