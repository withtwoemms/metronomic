# metronomic

Losslessly regularize noisy, nearly-periodic timestamps.

A sensor that should fire every `P` ticks actually fires at `P ± jitter`.
`metronomic` recovers the underlying grid and expresses each timestamp as

```
timestamp[i] = offset + i * period + residual[i]
```

The grid `(period, offset)` plus the small integer residuals reconstruct the
input **exactly** — regular structure without discarding the jitter. That
makes the decomposition useful for timestamp compression (residuals fit in a
few bits), clock-drift measurement, sensor-health monitoring, and gap/anomaly
detection.

## Implementations

Two implementations share one behavior, pinned by a golden-file conformance
suite:

- **`lossless-regularization.py`** — the Python reference (the original
  prototype). Needs the venv from `make`.
- **`metronomic/`** — the Rust crate: a fast, dependency-free-to-deploy
  binary. `cargo build` in that directory.

Both expose the same CLI:

```
$ metronomic generate --period 10 --count 20 [--seed N]
[10, 22, 30, 40, 49, 59, 68, 81, 90, ...]

$ metronomic generate --period 10 --count 20 | metronomic regularize
period:    10
offset:    10
residuals: [0, 2, 0, 0, -1, -1, -2, 1, 0, ...]
lossless:  True
```

`generate` simulates a jittery sensor by sampling offsets from a discrete
Gaussian kernel (built from the modified Bessel function `iv`, per the
scale-space literature). `regularize` fits the grid by least squares
(rounding half-to-even) and reads timestamps from arguments or stdin —
any text containing integers works.

## Conformance

```
$ tests/run_conformance.sh lossless-regularization-venv/bin/python lossless-regularization.py
$ tests/run_conformance.sh metronomic/target/debug/metronomic
```

Each golden case in `tests/golden/*/` is `input.txt` (timestamps) and
`expected.txt` (exact required output). Rust unit tests (`cargo test`) also
cross-check the kernel against `scipy.special.iv` values and pin the
ties-to-even rounding.
