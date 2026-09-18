# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class DataImportLog(models.Model):
    _inherit = "data.import.log"

    pickup_id = fields.Many2one(
        "data.import.pickup", string="Pick-up", readonly=True, ondelete="restrict"
    )

    def _finalize_file(self):
        """Release the source file once the import is over.

        The file always ends up in the done directory: it was received whole,
        and it is the rejected units that are reported separately.
        """
        super()._finalize_file()
        pickup = self.pickup_id
        if not pickup:
            return
        fs = pickup.backend_id.fs
        source = f"{pickup.path_processing}/{self.file_name}"
        if not fs.exists(source):
            _logger.warning("%s is gone, nothing to move.", source)
            return
        fs.mv(source, f"{pickup.path_done}/{self.file_name}")
