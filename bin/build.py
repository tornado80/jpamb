#!/usr/bin/env python3

import click
import os
from pathlib import Path

from utils import *

WORKFOLDER = Path(os.path.abspath(__file__)).parent.parent


@click.command
@click.option("--check/--no-check", default=True)
@click.option("--decompile/--no-decompile", default=True)
def build(check, decompile):
    """Rebuild the benchmark-suite."""

    suite = Suite(WORKFOLDER, QUERIES)

    suite.build()
    suite.update_cases()

    if check:
        suite.check()

    if decompile:
        suite.decompile()


if __name__ == "__main__":
    build()
