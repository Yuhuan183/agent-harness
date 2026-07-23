#!/bin/sh
# Push the package to the given registry. Stubbed for local dev: records the
# publish so CI can verify what was pushed.
echo "published to ${1:-staging} at $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .published_marker
echo "pricebook published to ${1:-staging}"
