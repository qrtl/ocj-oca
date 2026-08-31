To configure company-level images:

1.  Go to *Settings / Companies*
2.  Open your company record
3.  Navigate to the *Report Images* tab
4.  Add images with position settings:
    - Upload an image - width defaults to 50mm and height is automatically
      calculated to maintain the original aspect ratio
    - *Top (mm)*: Distance from the top of the page
    - *Left (mm)*: Distance from the left edge of the page
    - *Width (mm)*: Width of the image (changing this auto-adjusts height)
    - *Height (mm)*: Height of the image (changing this auto-adjusts width)
    - *Respect Image Ratio*: When enabled (default), changing width or height
      automatically adjusts the other dimension to maintain aspect ratio.
      Uncheck for manual control of both dimensions.
    - *First Page Only*: Check to show only on the first page
    - *Company*: Automatically set to the current company when creating from
      the company form. To create shared images, leave empty.

To configure report-specific images:

1.  Go to *Settings / Technical / Actions / Reports*
2.  Open the report you want to customize
3.  Navigate to the *Report Images* tab
4.  Check *Include Company Images* if you want to show company-level images
    in addition to report-specific images
5.  Add report-specific images in the list with the same position settings
    as above

**Note**: By default, images maintain their aspect ratio. When you upload an
image, it's automatically sized to 50mm width with proportional height. You can
then adjust either dimension and the other will update automatically to prevent
distortion.

To show an image on some records only:

1.  Open the image in the report's or the company's *Report Images* tab
2.  Set *Condition Model* to the model printed by the report, and *Domain* to
    the records that should carry the image

**Note**: The condition applies to the reports rendering the condition model
only. A report on any other model keeps printing the image unconditionally, so
one image can be conditional on one form and always shown on another.
