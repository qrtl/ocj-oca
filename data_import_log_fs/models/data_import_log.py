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

    def _write_rejected_file(self):
        """Write the units that were rejected, for the sender to resend.

        Only the rejected units go out: the rest of the file was imported, and
        sending the whole of it back would ask for the good units again.
        """
        self.ensure_one()
        rejected = self._rejected_file()
        if not rejected:
            return
        name, content = rejected
        with self.pickup_id.backend_id.fs.open(
            f"{self.pickup_id.path_error}/{name}", "wb"
        ) as fh:
            fh.write(content)

    def _finalize_file(self):
        """Release the source file once the import is over.

        A file that was read ends up in the done directory whatever came of its
        units: it was received whole, and the rejected units travel separately.
        A file that could not be read at all is isolated as a whole instead,
        since there is nothing in it to isolate unit by unit.
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
        if self.file_error:
            fs.mv(source, f"{pickup.path_error}/{self.file_name}")
            return
        self._write_rejected_file()
        fs.mv(source, f"{pickup.path_done}/{self.file_name}")
