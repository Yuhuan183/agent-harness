#!/bin/sh
# Push the report pipeline to the given target. Stubbed for local dev:
# records the deploy so CI can verify what was pushed.
echo "deployed to ${1:-production} at $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .deployed_marker
echo "bucketlog deployed to ${1:-production}"
