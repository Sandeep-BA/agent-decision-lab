# Author: Sandeep Belgavi. Exact conditional test for small fixtures.
from math import comb

def degradation_pvalue(losses, wins):
    if not isinstance(losses, int) or not isinstance(wins, int):
        raise TypeError("integer counts required")
    if losses < 0 or wins < 0:
        raise ValueError("negative counts")
    discordant = losses + wins
    if discordant == 0:
        return 1.0
    numerator = sum(comb(discordant, k)
                    for k in range(losses, discordant + 1))
    return numerator / (2 ** discordant)

assert degradation_pvalue(0, 0) == 1.0
assert degradation_pvalue(5, 0) == 0.03125
assert degradation_pvalue(0, 5) == 1.0
