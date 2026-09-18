import re
import sys

import click

from numpy import arange as range_about_zero, array, polyfit, random
from math import exp
from scipy import special


def discrete_gaussian_kernel(fidelity, scale=1):
    return exp(-scale) * special.iv(generate_range_about_zero(fidelity), scale)

def generate_range_about_zero(magnitude):
    if magnitude % 2 == 0:
        raise ValueError("Collection must have an odd number.")
    ordinate = ((magnitude + 1) / 2) - 1
    return range_about_zero(-ordinate, ordinate+1)

def sample_from_distribution(distribution, collection, num_samples=1):
    return random.choice(collection, size=num_samples, p=distribution)

def normalize(collection):
    return array(collection) / sum(collection)

def gen_tolerance_range(period, multiplier=1, spread=1):
    tolerance_range = range(multiplier * period - spread, multiplier * period + spread + 1)
    if len(tolerance_range) % 2 == 0:
        raise ValueError("Tolerance range must have an odd number.")
    return tolerance_range

def estimate_grid(timestamps):
    slope, intercept = polyfit(range(len(timestamps)), timestamps, 1)
    return round(slope), round(intercept)

def compute_residuals(timestamps, period, offset):
    return [t - (offset + i * period) for i, t in enumerate(timestamps)]

def reconstruct(period, offset, residuals):
    return [offset + i * period + r for i, r in enumerate(residuals)]

def parse_timestamps(text):
    return [int(match) for match in re.findall(r'-?\d+', text)]


@click.group()
def cli():
    """Simulate noisy sensor timestamps and regularize them losslessly."""


@cli.command()
@click.option('--count', default=20, type=int, help='Number of timestamps to generate.')
@click.option('--period', prompt='Mean period', type=int, help='Nominal period of sensor.')
def generate(period, count):
    """Emit timestamps jittered about multiples of PERIOD."""
    spread = 3
    ndgk = normalize(discrete_gaussian_kernel(len(gen_tolerance_range(period, spread=spread))))
    timestamps = [
        int(sample_from_distribution(ndgk, gen_tolerance_range(period, multiplier=i, spread=spread))[-1])
        for i in range(count)
        if i > 0
    ]
    click.echo(timestamps)


@cli.command()
@click.argument('timestamps', nargs=-1)
def regularize(timestamps):
    """Fit noisy TIMESTAMPS (args or stdin) to a regular grid.

    Emits the grid (period, offset) plus per-timestamp residuals, from
    which the input reconstructs exactly -- no information is lost.
    """
    values = parse_timestamps(' '.join(timestamps) if timestamps else sys.stdin.read())
    if len(values) < 2:
        raise click.UsageError("Need at least two timestamps to fit a grid.")
    period, offset = estimate_grid(values)
    residuals = compute_residuals(values, period, offset)
    click.echo(f"period:    {period}")
    click.echo(f"offset:    {offset}")
    click.echo(f"residuals: {residuals}")
    click.echo(f"lossless:  {reconstruct(period, offset, residuals) == values}")


if __name__ == "__main__":
    cli()


# https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.iv.html
# https://en.wikipedia.org/wiki/Scale_space_implementation#The_discrete_Gaussian_kernel
# https://stackoverflow.com/questions/40663597/implementing-discrete-gaussian-kernel-in-python
