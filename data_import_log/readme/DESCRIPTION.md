This module provides the log models for data imports that run unattended, as a
scheduled feed of files rather than a user driving a wizard:

- `data.import.log`, one record per imported file, carrying the file itself,
  the hash of its content, its format and its character encoding.
- `data.import.error`, one record per rejected unit, linked to its log.

A file is imported as one job per unit, so that a unit is a transaction: a
rejected unit is isolated instead of costing the rest of the file. Each unit
accounts for itself, whatever its outcome, and the file is closed once they
all have — including when a unit crashes, or when a job disappears and nothing
would otherwise settle it.

It is not useful by itself, and is expected to be used as a dependency of
modules that implement a specific import.
