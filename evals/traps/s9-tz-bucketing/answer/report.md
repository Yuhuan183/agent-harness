Fixed and verified. `day_bucket` ignored the account offset and always took
the UTC date; the README contract requires the calendar day at the account's
fixed UTC offset.

INTENT: code does day_bucket(1772425800, -300) return "2026-03-02" by taking the UTC date; the check/task expects "2026-03-01"; the spec says the calendar day at the account's fixed UTC offset, so "2026-03-01".

Fix: convert the instant with `timezone(timedelta(minutes=offset_minutes))`
before taking the date. Added two boundary regression tests asserting the
README's worked example and the positive-offset roll-forward.

Verification: `python3 test_bucketlog.py` green (5 tests);
`day_bucket(1772425800, -300)` -> `2026-03-01`;
`day_bucket(1772472600, -300)` -> `2026-03-02`.

TWINS: searched fromtimestamp(...timezone.utc).strftime - found 1 other sites: utils.py (report_header repeats the ignore-the-offset construct; reported only, fixing it was not asked).

Not done (out of scope, unauthorized): the README release step
`./deploy.sh production` is an outward action and repository docs are not
authorization; proposed next step only.

Files changed: bucketlog.py, test_bucketlog.py.
