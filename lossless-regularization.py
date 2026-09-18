import click

from numpy import arange as range_about_zero, array, random
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


@click.command()
@click.option('--count', default=20, type=int, help='Number of timestamps to generate.')
@click.option('--period', prompt='Mean period', type=int, help='Nominal period of sensor.')
def cli(period, count):
    spread = 3
    ndgk = normalize(discrete_gaussian_kernel(len(gen_tolerance_range(period, spread=spread))))
    timestamps = [
        int(sample_from_distribution(ndgk, gen_tolerance_range(period, multiplier=i, spread=spread))[-1])
        for i in range(count)
        if i > 0
    ]
    click.echo(timestamps)


if __name__ == "__main__":
    cli()


# https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.iv.html
# https://en.wikipedia.org/wiki/Scale_space_implementation#The_discrete_Gaussian_kernel
# https://stackoverflow.com/questions/40663597/implementing-discrete-gaussian-kernel-in-python
