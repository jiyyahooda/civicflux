# Windows CI path fingerprint fix

The Windows PR job 122260713826 loaded all nine components and passed the four
available prediction/abstention smoke checks, then failed the API inventory
readiness assertion with `Artifact changed after fresh-process check`.

The fingerprint hashed native path strings, and portable-artifact hash dictionaries
also used native relative path strings. Windows backslashes differed from the
committed macOS forward-slash evidence even when file bytes were identical.
Both now use `relative_to(root).as_posix()`. Actual byte/hash checks are preserved.
All nine fresh-process reports were regenerated; no trained artifact was modified.

Added two regression tests that simulate Windows relative-path spelling and run
in both CI jobs. Local verification: 105 tests passed (one existing warning),
all nine fresh-process reports passed, and scripts/ci_smoke.py passed. SHA-256
checks confirm all 273 original artifact/notebook files remain unchanged.
Native GitHub Windows rerun is required to confirm the fix on the hosted runner.
