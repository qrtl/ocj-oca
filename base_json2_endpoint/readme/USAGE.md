Example: configure an endpoint named `get_partners` in the `contacts` domain that
calls `search_read` on `res.partner` with allowed fields `name,email`.

Call it with:

```
POST /json2/endpoint/contacts/get_partners
Content-Type: application/json
Authorization: Bearer <api_key>

{"domain": [["is_company", "=", true]]}
```

Browse available endpoints:

```
GET /json2/endpoint/doc
Authorization: Bearer <api_key>
```
