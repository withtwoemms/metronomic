"""The grid decomposition: timestamp[i] = offset + i * period + residual[i].

References:
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.iv.html
- https://en.wikipedia.org/wiki/Scale_space_implementation#The_discrete_Gaussian_kernel
"""
import re

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

def generate_timestamps(period, count, spread=3, seed=None):
    if seed is not None:
        random.seed(seed)
    ndgk = normalize(discrete_gaussian_kernel(len(gen_tolerance_range(period, spread=spread))))
    return [
        int(sample_from_distribution(ndgk, gen_tolerance_range(period, multiplier=i, spread=spread))[-1])
        for i in range(count)
        if i > 0
    ]
