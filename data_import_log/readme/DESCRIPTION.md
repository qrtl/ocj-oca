This module provides generic logging models for data imports:

- `data.import.log`, one record per imported file, with the file attached.
- `data.import.error`, one record per rejected row, linked to its log.

It is not useful by itself, and is expected to be used as a dependency of
modules that implement a specific import.
