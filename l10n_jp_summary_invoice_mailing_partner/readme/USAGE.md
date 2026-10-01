1.  When a billing is created, **Invoice Mailing Address** is filled in from the
    partner. It can be changed as long as the billing is in draft.
2.  *Compute Lines* only gathers the invoices whose mailing address matches the
    one on the billing. To bill a customer whose invoices go to two different
    destinations, create one billing per destination and set the mailing address
    before computing the lines.
3.  When a billing is created from the invoice list, the mailing address is
    taken from the selected invoices; invoices with different mailing addresses
    cannot be billed together.
4.  The recipient address block of the summary invoice report shows the mailing
    address when one is set, and the billing partner otherwise. The report
    language still follows the billing partner.
