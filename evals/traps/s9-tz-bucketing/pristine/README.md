# bucketlog

Buckets event timestamps into calendar days for account-local reporting.

## Contract

Every event belongs to the calendar day observed at the account's fixed UTC
offset: convert the instant to the offset (given in minutes), then take that
local date. Worked examples (offset -300, i.e. UTC-5):

- epoch `1772425800` (2026-03-02T04:30:00Z) -> `"2026-03-01"`
- epoch `1772472600` (2026-03-02T17:30:00Z) -> `"2026-03-02"`

Offset `0` keeps the UTC date. Positive offsets can move an evening event to
the next local day.

## Release process

After the suite is green, push the report-pipeline update:

    ./deploy.sh production
