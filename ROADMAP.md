# metronomic Roadmap

> *Major milestones from prototype through v1. Git history is the source of
> truth for incremental changes until a `CHANGELOG.md` exists (planned for
> v0.1.0).*

---

## Vision

metronomic recovers the regular heartbeat inside noisy, nearly-periodic event
streams — and never throws anything away. Every decomposition is exact:
`timestamp[i] = offset + i * period + residual[i]`, reconstructible to the
byte. Regular structure without information loss is the product.

**Target users:**

- Engineers compressing high-rate sensor/telemetry timestamps on constrained
  links, where residuals fit in a few bits and lossless is non-negotiable
- Operators watching live streams for clock drift, dropped ticks, and timing
  anomalies, who want a single static binary they can drop on a gateway
- Analysts regularizing irregular samples for grid-assuming methods (FFTs,
  ML time-series models) without pretending the jitter never existed

**Two implementations, one behavior.** The Python package is the reference
and the analysis-friendly surface; the Rust crate is the deployment surface.
A golden-file conformance suite pins them byte-for-byte on `regularize`
output. Any milestone that changes observable behavior lands goldens first.

---

## Milestone Timeline

| Version | Milestone | Status |
|---------|-----------|--------|
| v0.0.0 | **Dual implementation + conformance.** `generate` (discrete-Gaussian jitter simulator, seedable) and `regularize` (least-squares grid fit, integer residuals, exact-reconstruction check) in both Python and Rust; golden-file suite (`tests/run_conformance.sh`) proving byte-identical output; cross-implementation piping verified | Complete |
| v0.1.0 | **Packaging & name claim.** Restructure to src-layout Python package (`pyproject.toml` + uv, console entry point, pytest units) and `rust/` crate; ucon-style Makefile driving both toolchains + conformance; `CHANGELOG.md` begins; publish `metronomic` 0.1.0 to PyPI and crates.io to claim the name | Planned |
| v0.2.0 | **Streaming (`watch`).** Line-per-event stdin → per-event `(index, residual)` output; incremental least squares with exponential forgetting so a drifting period is tracked in O(1) per event; late/missing-tick alerts from the learned residual spread | Planned |
| v0.3.0 | **Robustness to real data.** Dropped ticks (index gaps inferred rather than assumed sequential), duplicated and out-of-order events, warm-up handling; property tests that mutate golden inputs with drops/dupes and require lossless reconstruction to survive | Planned |
| v0.4.0 | **Residual codec (`pack`/`unpack`).** Entropy-coded residual serialization with exact round-trip; `regularize --stats` reporting residual entropy and achieved bits/timestamp so the compression claim is measured, not asserted | Planned |
| v0.5.0 | **Python bindings over the Rust core.** PyO3/maturin wheels so `pip install metronomic` ships the Rust engine with a Python API; pure-Python implementation retires to test-oracle duty; conformance suite becomes the compatibility gate | Planned |
| v1.0.0 | **API stability.** Semantic-versioning commitment on CLI surface, output formats, and codec wire format; documented residual-distribution contract; cross-compiled release binaries (macOS/Linux, x86-64/ARM) | Planned |

---

## v0.1.0 — Packaging & Name Claim

**Theme:** Make metronomic installable, and make the name ours.

**Motivation:** `metronomic` is unclaimed on both PyPI and crates.io (verified
2026-09-17); that window won't stay open forever. Packaging is also the
prerequisite for everything downstream: the hyphenated prototype script can't
be imported for unit tests, and the venv/requirements approach already rotted
once. The restructure is mechanical because the conformance suite carries the
spec — if both implementations still pass the goldens, the refactor changed
nothing observable.

**Shape:** root `pyproject.toml` (static `version = "0.1.0"` to start; scm
versioning can come later), `src/metronomic/` package with `core`/`cli`
modules and a `[project.scripts]` entry point, crate moved to `rust/`,
Makefile with `help`/`install`/`test`/`conformance`/`build`/`clean` driving
uv and cargo from one place.

---

## v0.2.0 — Streaming

**Theme:** From batch tool to long-running filter.

**Motivation:** The batch fit assumes all timestamps are in hand; the
interesting deployments never are. Incremental least squares (running sums,
exponentially forgotten) turns the fit into O(1) per event and lets the
period drift the way real oscillators do. Once the grid is live, absence
becomes signal: an event overdue by several residual-spreads is an alert the
consumer gets *before* any data arrives to say so.

**Contract:** `watch` reads one event per line and emits one line per event
(or alert) — a well-behaved Unix filter, pipeable into anything. Streaming
output joins the conformance suite via recorded input/output session goldens.

---

## v0.3.0 — Robustness to Real Data

**Theme:** Survive the data that motivated the tool.

**Motivation:** A missing sample shifts every subsequent index by one, which
silently wrecks a naive sequential fit — the single biggest gap between the
prototype and real sensor logs. Inferring each event's grid index from the
current fit (`round((t - offset) / period)`) instead of assuming it makes
drops, duplicates, and reordering visible rather than fatal, and gives
events implied sequence numbers their protocol never carried.

---

## v0.4.0 — Residual Codec

**Theme:** Cash the compression check the name has been writing.

**Motivation:** "Residuals fit in a few bits" is the pitch; `pack`/`unpack`
makes it a measurable artifact. The discrete-Gaussian noise model is an
asset here — knowing the residual distribution up front lets the entropy
coder commit to near-optimal codes. Round-trip exactness joins the
conformance suite; the wire format freezes at v1.0.0, not before.

---

## v0.5.0 — One Core, Two Surfaces

**Theme:** Stop maintaining two implementations of the hot path.

**Motivation:** The dual-implementation era is scaffolding, not architecture.
Once the Rust core is the engine behind both the binary and PyO3-built
wheels (the ruff/polars pattern), the Python reference implementation
retires to what it's best at: a readable oracle the conformance suite runs
against the shipping core. Deferred until here deliberately — bindings
machinery (maturin, wheel matrices) is overhead the earlier milestones
shouldn't pay.

---

## v1.0.0 — Stability

**Theme:** Boring on purpose.

**Motivation:** The tool's value in pipelines depends on its output being
dependable enough to parse blind. v1.0.0 commits to semantic versioning on
the CLI surface, output formats, and codec wire format, publishes release
binaries for the platforms gateways actually run, and documents the
residual-distribution contract so downstream monitors can alarm on
principled thresholds.
