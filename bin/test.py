#!/usr/bin/env python3
""" The jpamb tester
"""

import os
import click
from pathlib import Path
from utils import *


WORKFOLDER = Path(os.path.abspath(__file__)).parent.parent


@click.command()
@click.option(
    "--timeout",
    show_default=True,
    default=2.0,
    help="timeout in seconds.",
)
@click.option("-v", "--verbose", count=True)
@click.option(
    "-o",
    "--report",
    default="test_output",
    type=click.Path(path_type=Path),
)
@click.option(
    "--filter-methods",
    help="only take methods that matches the regex.",
    callback=re_parser,
)
@click.argument("cmd", nargs=-1, type=click.Path())
def test(
    filter_methods,
    verbose,
    cmd,
    timeout,
    report: Path,
):
    logger = setup_logger(verbose)
    suite = Suite(WORKFOLDER, QUERIES, logger)

    for case in suite.cases():
        if filter_methods and not filter_methods.search(case.methodid):
            logger.trace(f"{case} did not match {filter_methods}")
            continue
        logger.info(f"Running {case}")

        (result, _) = run_cmd(
            cmd + (case.methodid, str(case.input)),
            logger=logger,
            timeout=timeout,
        )

        method = report / case.methodid
        method.mkdir(parents=True, exist_ok=True)
        (method / str(case.input)).write_text(result)

        for line in result.splitlines():
            logger.debug(f"RESULT: {line}")
        test = result.splitlines()[-1]
        logger.info(f"Returned {test!r}")
        if test == case.result:
            logger.success(f"Mathed {case.result!r}")
        else:
            logger.error(f"Failed {test!r} != {case.result!r}")


if __name__ == "__main__":
    test()
