1. Assign the **JSON2 Endpoint / Manager** group to the user who will configure
   endpoints (under *Settings > Users > JSON2 Endpoint*).
2. Navigate to **JSON2 Endpoints > Configuration > Endpoints**.
3. Create endpoint records specifying the domain name (logical grouping), endpoint
   name, target model, and method.
4. Optionally define parameters with type validation and default values.
5. Optionally restrict access to specific groups via the **Allowed Groups** field.
   When set, only users belonging to at least one of the listed groups can call the
   endpoint.
6. Create a dedicated Odoo user for each external system that will consume the API.
7. Assign the **JSON2 Endpoint / User** group to the user (under *Settings > Users >
   JSON2 Endpoint*). If certain endpoints are restricted via **Allowed Groups**, ensure
   the user also belongs to the relevant groups.
8. Generate an API key (scope: rpc) for the user under *Settings > Users > API Keys*.

Endpoints are accessible at:

    POST /json2/endpoint/<domain>/<endpoint_name>

API documentation is available at:

    GET /json2/endpoint/doc
    GET /json2/endpoint/doc/<domain>
