This module picks import files up from a filesystem storage and logs them.

A pick-up definition is a storage backend, the directories a file travels
through, and the pattern the files are named by. A scheduled scan lists the
incoming directory, skips the files still being written, creates one import log
per file with the file attached, and holds the file aside while it is imported,
so that the next scan does not take it again.

The file itself always ends up in the done directory: it was received whole,
and it is the rejected units that are reported separately. A file offered twice
is recognized by its content and left where it is.

It relies on `data_import_log` for the log and on `fs_storage` for the
transport, which is any filesystem fsspec supports — sftp, S3, or a local
directory.
