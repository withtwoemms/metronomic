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

## Install

```sh
pip install metronomic       # Python CLI + importable API
cargo install metronomic     # static binary, no runtime
```

Or from a checkout: `make install` (Python, via uv) and
`cargo build --manifest-path rust/Cargo.toml` (Rust).

## Use

```
$ metronomic generate --period 10 --count 20 --seed 42
[10, 22, 30, 40, 49, 59, 68, 81, 90, 100, 108, 122, 131, 139, 149, 159, 170, 180, 190]

$ metronomic generate --period 10 --count 20 | metronomic regularize
period:    10
offset:    10
residuals: [0, 2, 0, 0, -1, -1, -2, 1, 0, 0, -2, 2, 1, -1, -1, -1, 0, 0, 0]
lossless:  True
```

`generate` simulates a jittery sensor by sampling offsets from a discrete
Gaussian kernel (built from the modified Bessel function `iv`, per the
scale-space literature). `regularize` fits the grid by least squares
(rounding half-to-even) and reads timestamps from arguments or stdin —
any text containing integers works.

From Python:

```python
from metronomic import estimate_grid, compute_residuals, reconstruct

period, offset = estimate_grid(timestamps)
residuals = compute_residuals(timestamps, period, offset)
assert reconstruct(period, offset, residuals) == timestamps  # always
```

## Implementations

Two implementations share one behavior, pinned by a golden-file conformance
suite:

- **`src/metronomic/`** — the Python reference: importable API plus the CLI.
- **`rust/`** — the Rust crate: the same CLI as a fast, single-file-deploy
  binary.

```
$ make conformance    # golden suite against BOTH implementations
$ make test           # Python tests with coverage
$ make test-rust      # Rust unit tests
```

Each golden case in `tests/golden/*/` is `input.txt` (timestamps) and
`expected.txt` (exact required output); `tests/run_conformance.sh <command>`
checks any implementation byte-for-byte. Rust unit tests also cross-check
the kernel against `scipy.special.iv` values and pin ties-to-even rounding.

## Status

v0.1.0 handles complete, ordered batch captures. See [ROADMAP.md](ROADMAP.md)
for what's ahead: streaming `watch`, robustness to dropped/duplicated events,
an entropy-coded residual codec, and PyO3 bindings over the Rust core.
