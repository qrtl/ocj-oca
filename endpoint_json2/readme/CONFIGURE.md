Go to *Settings > Technical > Endpoints* and create a new endpoint with
**Exec Mode** set to **JSON2-RPC**.

### Basic Setup

- **Model**: The Odoo model to operate on (e.g. `res.partner`).
- **Method**: A public model method (e.g. `search_read`). Alternatively,
  provide a **Code Snippet** for custom logic — these two fields are
  mutually exclusive.
- **Allowed Fields**: Comma-separated list of fields the API may return.
  Use dotted notation for relational fields (e.g.
  `name,email,country_id.name,category_id.name`). Dotted fields work
  with Many2one, Many2many, and One2many relations. Leave empty to allow
  all fields.
- **Default Domain**: A JSON-formatted domain filter applied to every
  request (e.g. `[["active", "=", true]]`).
- **Parameters**: Define named parameters with types, defaults, and
  required flags. These are validated before the method is called.

### Access Control

All endpoint execution is wrapped in `sudo()`, allowing API users to
operate with minimal Odoo privileges. Access is controlled at two levels:

- **Auth Type**: Set to **Bearer** to require an API key for
  authentication.
- **Allowed Groups**: Restrict endpoint access to specific user groups.
  Create integration-specific groups (e.g. "Hospital System", "WMS") and
  assign them to the corresponding API users. Each endpoint declares
  which groups may call it. Leave empty to allow any authenticated user.
- **Allowed Fields**: Controls which data fields are exposed in the
  response, regardless of what the underlying model method returns.

### Code Snippets

For operations that go beyond a single model method call, use a code
snippet instead of the method field. Available variables:

- `Model`: The target model (with `sudo()`).
- `params`: Validated parameters from the request.
- `env`: The Odoo environment.
- `Command`: Odoo's `Command` helper for relational field writes.
- `exceptions`: Werkzeug exceptions (`BadRequest`, `NotFound`, etc.).

The snippet must set a `result` variable with the response data.
