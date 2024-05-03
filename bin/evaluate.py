#!/usr/bin/env python3
""" The jpamb evaluator
"""

from pathlib import Path
import click
import os
import subprocess
import sys

from utils import *

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("jpamb")


# def add_queries(m):
#     def validate(ctx_, param_, queries):
#         resulting_queries = []
#         for queries in queries:
#             resulting_queries.extend(queries.split(","))
#         queries = resulting_queries
#         return queries
#
#     return click.option(
#         "--queries",
#         "queries",
#         multiple=True,
#         show_default=True,
#         default=QUERIES,
#         callback=validate,
#     )(m)


def add_timeout(m):
    return m


WORKFOLDER = Path(os.path.abspath(__file__)).parent.parent


def tool_parser(ctx_, parms_, tools):
    resulting_tools = []
    for tool in tools:
        nameandtool = tool.split("=")
        if len(nameandtool) > 1:
            name, tool = nameandtool
            tool = Path(tool).absolute()
        else:
            tool = Path(nameandtool[0]).absolute()
            name = tool.with_suffix("").name
        resulting_tools.append((name, tool))
    return resulting_tools


@click.command
@click.option(
    "--timeout",
    show_default=True,
    default=2.0,
    help="timeout in seconds.",
)
@click.option(
    "-N",
    "--iterations",
    show_default=True,
    default=1,
    help="number of iterations.",
)
@click.argument("TOOLS", nargs=-1, callback=tool_parser)
def evaluate(tools, timeout, iterations):
    """Given an command check if it can predict the results."""
    import random, itertools, csv

    suite = Suite(WORKFOLDER, QUERIES)

    if not tools:
        raise click.UsageError("Expected a command to evaluate")

    w = csv.writer(sys.stdout)

    w.writerow(
        ["tool_name", "method", "query", "iter", "wager", "prob", "score", "time"]
    )
    for (m, cases), q, n in itertools.product(
        Case.by_methodid(suite.cases()), suite.queries, range(iterations)
    ):
        log.info("Running %s with query %s, iteration %s", m, q, n)
        sometimes = any(c.result == q for c in cases)
        for tool_name, cmd in random.sample(tools, k=len(tools)):
            try:
                fpred, time = run_cmd(
                    [cmd, m, q],
                    timeout=timeout,
                    logger=log.getChild(summary64([tool_name, m, q])),
                )
                prediction = Prediction.parse(fpred)
                wager = prediction.wager
                prob = prediction.to_probability()

                log.info("Responded %s, wager=%s, probability=%s", fpred, wager, prob)
                # sys.exit(-1)
                score = prediction.score(sometimes)
            except subprocess.CalledProcessError:
                if fail_fast:
                    sys.exit(-1)
                wager, prob, score, time = 0, 0.5, 0, 0
            except subprocess.TimeoutExpired:
                wager, prob, score, time = 0, 0.5, 0, float("NaN")

            w.writerow(
                [
                    tool_name,
                    m,
                    q,
                    n,
                    wager,
                    prob,
                    score,
                    time,
                ]
            )


if __name__ == "__main__":
    evaluate()
