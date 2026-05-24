Go to *Settings > Technical > Endpoints* and create a new endpoint with **Exec Mode**
set to **JSON-2 API**.

## Basic Setup

- **Route Group** and **Name**: Together these determine the endpoint URL, which is
  automatically computed as `/json2/{route_group}/{name}`. For example, a route group
  `contacts` with name `get_partners` produces `/json2/contacts/get_partners`. The
  route group also organizes endpoints in the API documentation at
  `/json2/doc/{route_group}`.
- **Model**: The Odoo model to operate on (e.g. `res.partner`).
- **Method**: A public model method (e.g. `search_read`). Alternatively, provide a
  **Code Snippet** for custom logic — these two fields are mutually exclusive.
- **Response Fields**: One field per line. Optionally follow with an alias to rename
  the key in the response. Use dotted notation (one level) for relational fields
  (Many2one, Many2many, One2many). Leave empty to return all fields. Example:

  ```
  name
  email
  country_id.name country
  write_date last_modified
  ```
- **Default Domain**: A JSON-formatted domain filter applied to every request
  (e.g. `[["active", "=", true]]`).
- **Parameters**: Define named parameters with types, defaults, and required flags.
  These are validated before the method is called.

## Access Control

All endpoint execution is wrapped in `sudo()`, allowing API users to operate with
minimal Odoo privileges. Access is controlled at two levels:

- **Auth Type**: Select the authentication method for the endpoint (e.g. **Bearer**
  for API key authentication).
- **Allowed Groups**: Restrict endpoint access to specific user groups. Create
  integration-specific groups (e.g. "Hospital System", "WMS") and assign them to
  the corresponding API users. Each endpoint declares which groups may call it.
  Leave empty to allow any authenticated user.

## Code Snippets

As an alternative to a model method, a code snippet can be used for quick, ad-hoc
logic. Available variables:

- `Model`: The target model (with `sudo()`).
- `params`: Validated parameters from the request.
- `env`: The Odoo environment.
- `Command`: Odoo's `Command` helper for relational field writes.
- `json`: Safe JSON module for serialization.
- `exceptions`: Werkzeug exceptions (`BadRequest`, `NotFound`, etc.).
- `log`: Log messages to the `ir.logging` table.

The snippet must set a `result` variable with the response data.
