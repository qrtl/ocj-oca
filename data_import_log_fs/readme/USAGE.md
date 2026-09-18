Create a storage backend (`fs_storage`), then a pick-up under
Data Import > Data Import Settings > Data Import Pick-ups, giving it the
incoming, processing, done and error directories relative to that backend, the
pattern its files are named by, and the format and encoding they arrive in.

Enable the "Data Import: pick files up" scheduled action, which is inactive on
installation.

Implement `_import_unit`, and if a unit is not a single row, `_group_rows`, on
`data.import.log` — see `data_import_log` for that contract.
