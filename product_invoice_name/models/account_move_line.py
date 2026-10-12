# Copyright 2026 Quartile (https://www.quartile.co)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _compute_name(self):
        # Odoo relabels a line only while its label is the one the product
        # would give, so a label typed by hand survives a recompute. Mirror that
        # with the invoice name: relabel where the line carries the standard
        # label (the super() call just set it) or where its saved label is the
        # invoice-name label of the product it had, which is what a product
        # change on a saved line looks like from the form.
        res = super()._compute_name()
        for line in self:
            if not line._product_for_invoice_name():
                continue
            origin = line._origin
            if line.name == line._invoice_label(standard=True) or (
                origin and origin.name == origin._invoice_label()
            ):
                line.name = line._invoice_label()
        return res

    def _product_for_invoice_name(self):
        """Return the line's product in the partner's language, or nothing
        when the invoice name does not apply to the line."""
        self.ensure_one()
        if (
            not self.product_id
            or self.journal_id.type != "sale"
            or self.display_type in ("line_section", "line_subsection", "line_note")
            or self.move_id.inalterable_hash is not False
        ):
            return self.env["product.product"]
        lang = self.move_id.partner_id.lang or self.partner_id.lang
        return self.product_id.with_context(lang=lang) if lang else self.product_id

    def _invoice_label(self, standard=False):
        """Return the label the line's product gives it: the invoice name when
        there is one, or the display name, each with the sales description
        under it. ``standard`` asks for the display name regardless."""
        product = self._product_for_invoice_name()
        if not product:
            return False
        name = product.display_name
        if not standard and product.invoice_name:
            name = product.invoice_name
        return "\n".join(part for part in (name, product.description_sale) if part)
