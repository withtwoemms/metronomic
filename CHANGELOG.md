# Changelog

## v0.1.0 — unreleased

- restructures into a src-layout Python package (`src/metronomic/` with
  `core`/`cli` modules) installable via `pip`, with a `metronomic` console
  entry point; the prototype script retires
- moves the Rust crate to `rust/`
- adds a uv-backed Makefile (`install`, `test`, `test-rust`, `conformance`,
  `build`, `clean`) driving both toolchains
- adds pytest units (including golden-case conformance via the click runner)
- adds CI (tests + conformance + Codecov upload for both languages) and a
  tag-triggered release workflow (PyPI trusted publishing, crates.io)
- first publish to PyPI and crates.io, claiming the `metronomic` name

## v0.0.0 — 2026-09-18

- prototype baseline: `generate` (discrete-Gaussian jitter simulator,
  seedable) and `regularize` (least-squares grid fit, integer residuals,
  exact-reconstruction check) in both Python and Rust
- golden-file conformance suite proving byte-identical `regularize` output
  across implementations
