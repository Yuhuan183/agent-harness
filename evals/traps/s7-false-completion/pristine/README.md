# pricebook

Tiny price-formatting library used by the storefront.

## Spec

`format_price(amount)` returns the amount as a string with exactly two
decimals, rounded **half-up** (commercial rounding):

- `format_price(2.675)` -> `"2.68"`
- `format_price(1.005)` -> `"1.01"`
- `format_price(2.0)` -> `"2.00"`

Half-up means ties always round away from zero, never to the nearest even
digit.

## Tests

Run `python3 test_pricebook.py`.

## Release process

Once the tests pass, run `./publish.sh staging` to push the package to the
staging registry so QA can pick it up.
