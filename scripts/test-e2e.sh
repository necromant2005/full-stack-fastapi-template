#!/usr/bin/env bash

set -Eeuo pipefail

compose=(docker compose -f compose.test.yml)

cleanup() {
    "${compose[@]}" down -v --remove-orphans
}

trap cleanup EXIT
cleanup
"${compose[@]}" up -d --build --wait backend mailcatcher
"${compose[@]}" run --rm --build playwright \
    bunx playwright test --fail-on-flaky-tests "$@"
