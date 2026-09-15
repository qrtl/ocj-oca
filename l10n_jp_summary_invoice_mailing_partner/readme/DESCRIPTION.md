This module extends Japan Summary Invoice so that the summary invoice can be
addressed to a contact other than the billing partner, for instance a head
office that collects the invoices of its branches or an outsourced accounting
firm.

It adds an **Invoice Mailing Address** field to billings, defaulted from the
partner, and makes every report rendered with the alternative layout print that
address instead of the billing partner's one.

Invoices are gathered in a billing only when they share its mailing address, so
that a customer whose invoices go to different destinations gets one summary
invoice per destination.
