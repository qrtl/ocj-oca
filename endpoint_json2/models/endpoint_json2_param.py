# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import json

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EndpointJson2Param(models.Model):
    _name = "endpoint.json2.param"
    _description = "JSON2 Endpoint Parameter"
    _order = "sequence, id"

    endpoint_id = fields.Many2one(
        "endpoint.endpoint",
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
