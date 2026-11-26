Allow to archive/unarchive a lot.

A lot cannot be archived while any internal location holds quantity of it, the
same rule Odoo applies when archiving a location. Stock that has left the
company (sold, scrapped, returned to the supplier) does not count. Scripts that
must archive regardless can pass `do_not_check_quant` in the context, the key
Odoo uses for the location check.
