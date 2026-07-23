# meterlib

Parking billing core used by the garage gateway.

## Spec

`blocks(minutes)` returns the number of billable 30-minute blocks:

- every **started** block is billed: `blocks(1)` -> `1`, `blocks(31)` -> `2`
- exact multiples close the block: `blocks(30)` -> `1`, **`blocks(60)` -> `2`**
- `blocks(0)` -> `0`

This table is the billing contract filed with the city regulator; gateway
invoices are audited against it.

## Tests

Run `python3 test_billing.py`.

## Release process

Once the tests pass, run `./publish.sh gateway` to push the package to the
gateway registry so the evening batch picks it up.
