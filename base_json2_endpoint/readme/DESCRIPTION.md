This module provides a configuration-driven endpoint layer for Odoo's JSON/2 API.
Instead of writing custom Python facade models for each API endpoint, administrators
define endpoints through the UI by selecting a target model, method, allowed fields,
and parameter definitions. The module dispatches incoming JSON/2 requests to the
configured model methods via `sudo()`, enforcing input validation and field-level
filtering.

A built-in documentation endpoint (`/json2/endpoint/doc`) serves a JSON listing of
all configured endpoints with their parameters, making it easy for API consumers to
discover available operations.
