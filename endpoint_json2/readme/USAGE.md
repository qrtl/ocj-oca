### Calling an Endpoint

Send a POST request with a JSON body to the endpoint's route:

```bash
curl -X POST https://your-odoo.com/json2/contacts/get_partners \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"domain": [["is_company", "=", true]], "limit": 10}'
```

### Incremental Sync

To fetch only records modified since a given timestamp, include a
`write_date` filter in the domain and add `write_date` to the allowed
fields:

```json
{"domain": [["write_date", ">=", "2026-05-23 00:00:00"]]}
```

Use the latest `write_date` from the response as the starting point for
the next sync to avoid clock drift between client and server.

### API Documentation

Auto-generated documentation for all JSON2 endpoints is available at
`/json2/doc`.
