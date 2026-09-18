# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models


class QueueJob(models.Model):
    _inherit = "queue.job"

    def write(self, vals):
        res = super().write(vals)
        if vals.get("state") == "failed":
            self._settle_failed_import_units()
        return res

    def _settle_failed_import_units(self):
        """Settle the unit of an import job that ended in failure.

        A failing job leaves nothing behind: its transaction, and with it any
        error row it wrote, is rolled back before the failure is recorded. The
        failure is recorded in a separate environment, which is where this runs
        and where the unit can be accounted for.
        """
        for job in self:
            if job.model_name != "data.import.log" or job.method_name != "_run_unit":
                continue
            log = job.records
            if len(log) != 1 or log.state != "processing":
                continue
            log._settle_failed_unit(job.kwargs.get("unit_key"), job.exc_info or "")
