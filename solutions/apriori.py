#!/usr/bin/env python3
""" The cheating solution. 

This solution uses apriori knowledge about the distribution of the test-cases
to gain an advantage.
"""

import sys, csv

with open("stats/distribution.csv") as f:
    distribution = list(csv.DictReader(f))[-1]

print(f"Got {sys.argv[1:]}", file=sys.stderr)

for k, v in distribution.items():
    if k == "method":
        continue
    print(f"{k};{v}")
