import random
import bisect

"""Randomly choose an item from a list, given the probabilities.

Source:
http://stackoverflow.com/a/4113516
"""


def cdf(weights):
    """Inverse cumulative distribution function"""
    total = sum(weights)
    result = []
    cummulative_sum = 0
    for w in weights:
        cummulative_sum += w
        result.append(cummulative_sum / total)
    return result


def choice(items, weights):
    assert len(items) == len(weights)
    cdf_vals = cdf(weights)
    x = random.random()
    idx = bisect.bisect(cdf_vals, x)
    return items[idx]
