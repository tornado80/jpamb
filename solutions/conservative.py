#!/usr/bin/env python3
""" The conservative solution.

Simply answer don't know (50%) to all questions.

"""
import sys

print(f"Got {sys.argv[1:]}", file=sys.stderr)
print("50%")
