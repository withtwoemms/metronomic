import sys

import click

from metronomic.core import (
    compute_residuals,
    estimate_grid,
    generate_timestamps,
    parse_timestamps,
    reconstruct,
)


@click.group()
def cli():
    """Simulate noisy sensor timestamps and regularize them losslessly."""


@cli.command()
@click.option('--count', default=20, type=int, help='Number of timestamps to generate.')
@click.option('--period', prompt='Mean period', type=int, help='Nominal period of sensor.')
@click.option('--seed', default=None, type=int, help='Seed the RNG for reproducible output.')
def generate(period, count, seed):
    """Emit timestamps jittered about multiples of PERIOD."""
    click.echo(generate_timestamps(period, count, seed=seed))


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
