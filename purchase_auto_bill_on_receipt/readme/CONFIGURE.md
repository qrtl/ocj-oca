Three configuration levels control whether a Purchase Order line is
auto-billed when the related receipt is validated. They are evaluated per line
at receipt time:

1. **Product Category** → *Auto Bill on Receipt* (boolean). Sets the baseline
   for all products in the category.
2. **Product** → *Auto Bill on Receipt* (selection: *Auto* / *No Auto* /
   empty). Leave empty to inherit from the product category. *Auto* or
   *No Auto* overrides the category setting for this product.
3. **Purchase Order** → *Block Auto Bill* (boolean, on the *Other
   Information* tab). When ticked, suppresses auto-billing for the whole
   order regardless of product or category settings.
