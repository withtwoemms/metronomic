#!/usr/bin/env bash
# Run any implementation against the golden conformance cases.
#
#   tests/run_conformance.sh <command...>
#
# <command...> must accept a `regularize` subcommand reading timestamps
# from stdin, e.g.:
#
#   tests/run_conformance.sh .venv/bin/metronomic
#   tests/run_conformance.sh rust/target/debug/metronomic
set -euo pipefail

golden_dir="$(cd "$(dirname "$0")/golden" && pwd)"
fail=0

for case_dir in "$golden_dir"/*/; do
    name="$(basename "$case_dir")"
    actual="$("$@" regularize < "$case_dir/input.txt")"
    if diff <(printf '%s\n' "$actual") "$case_dir/expected.txt" > /dev/null; then
        echo "PASS $name"
    else
        echo "FAIL $name"
        diff <(printf '%s\n' "$actual") "$case_dir/expected.txt" || true
        fail=1
    fi
done

exit $fail
