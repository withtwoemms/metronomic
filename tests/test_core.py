from pathlib import Path

import pytest
from click.testing import CliRunner

from metronomic import (
    compute_residuals,
    estimate_grid,
    generate_timestamps,
    parse_timestamps,
    reconstruct,
)
from metronomic.cli import cli
from metronomic.core import discrete_gaussian_kernel, normalize

GOLDEN_DIR = Path(__file__).parent / "golden"
GOLDEN_CASES = sorted(p.name for p in GOLDEN_DIR.iterdir() if p.is_dir())


def test_grid_estimation_recovers_known_period():
    assert estimate_grid([103, 199, 305, 397, 502]) == (100, 102)

def test_grid_estimation_rounds_ties_to_even():
    # the true least-squares slope here is exactly 2.5
    assert estimate_grid([0, 3, 5, 8, 10])[0] == 2

def test_decomposition_is_lossless():
    values = [103, 199, 305, 397, 502]
    period, offset = estimate_grid(values)
    residuals = compute_residuals(values, period, offset)
    assert reconstruct(period, offset, residuals) == values

def test_generated_timestamps_are_reproducible_and_regularizable():
    first = generate_timestamps(period=10, count=20, seed=42)
    assert first == generate_timestamps(period=10, count=20, seed=42)
    period, offset = estimate_grid(first)
    assert period == 10
    assert reconstruct(period, offset, compute_residuals(first, period, offset)) == first

def test_kernel_is_normalized_and_symmetric():
    kernel = normalize(discrete_gaussian_kernel(7))
    assert kernel.sum() == pytest.approx(1.0)
    assert kernel[0] == pytest.approx(kernel[-1])

def test_even_sized_kernels_are_refused():
    with pytest.raises(ValueError):
        discrete_gaussian_kernel(6)

def test_parse_extracts_integers_from_arbitrary_text():
    assert parse_timestamps("[10, -22, 30]\nx7") == [10, -22, 30, 7]

def test_regularize_refuses_fewer_than_two_timestamps():
    result = CliRunner().invoke(cli, ["regularize", "42"])
    assert result.exit_code != 0

@pytest.mark.parametrize("case", GOLDEN_CASES)
def test_golden_conformance(case):
    input_text = (GOLDEN_DIR / case / "input.txt").read_text()
    expected = (GOLDEN_DIR / case / "expected.txt").read_text()
    result = CliRunner().invoke(cli, ["regularize"], input=input_text)
    assert result.exit_code == 0
    assert result.output == expected
