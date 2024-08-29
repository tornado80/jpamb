#!/usr/bin/env python3
""" The jpamb evaluator
"""

from collections import defaultdict
from datetime import datetime
from pathlib import Path
import click
import os
import subprocess

from utils import *


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


def experiment_parser(ctx_, parms_, experiment):
    import yaml

    with open(experiment) as f:
        experiment = yaml.safe_load(f)

    context = "badly formated experiment: "
    if not "group_name" in experiment:
        raise click.UsageError(context + "no 'group_name'")

    if not "tools" in experiment:
        raise click.UsageError(context + "no 'tools'")

    if not isinstance(experiment["tools"], dict):
        raise click.UsageError(context + "'tools' should be a dictionary")

    for tn, t in experiment["tools"].items():
        if not ("technologies" in t and isinstance(t["technologies"], list)):
            raise click.UsageError(
                context + f"'tools.{tn}.technologies' should be a list"
            )

        if not ("executable" in t and Path(t["executable"]).is_file()):
            raise click.UsageError(
                context
                + f"'tools.{tn}.executable' should be a path to an existing file"
            )

    if not "machine" in experiment:
        raise click.UsageError(context + "no 'machine'")

    for k in ["os", "processor", "memory"]:
        if not experiment["machine"][k]:
            raise click.UsageError(context + f"no 'machine.{k}'")

    if not "for_science" in experiment:
        raise click.UsageError(context + "no 'for_science'")

    if not isinstance(experiment["for_science"], bool):
        raise click.UsageError(context + "'for_science' should be true or false")

    return experiment


def re_parser(ctx_, parms_, expr):
    import re

    if expr:
        return re.compile(expr)


@click.command
@click.option(
    "--timeout",
    show_default=True,
    default=2.0,
    help="timeout in seconds.",
)
@click.option(
    "--filter-tools",
    help="only take tools that matches the regex.",
    callback=re_parser,
)
@click.option(
    "--filter-methods",
    help="only take methods that matches the regex.",
    callback=re_parser,
)
@click.option(
    "-N",
    "--iterations",
    show_default=True,
    default=1,
    help="number of iterations.",
)
@click.option("-v", "--verbose", count=True)
@click.argument("EXPERIMENT", callback=experiment_parser)
def evaluate(experiment, timeout, iterations, verbose, filter_methods, filter_tools):
    """Given an command check if it can predict the results."""
    import random, itertools

    logger = setup_logger(verbose)

    logger.debug(f"{experiment}")

    suite = Suite(WORKFOLDER, QUERIES)

    if not (tools := experiment["tools"]):
        raise click.UsageError("Expected a tool to evaluate")

    by_tool = defaultdict(list)

    logger.debug(tools)

    for (m, cases), n in itertools.product(
        Case.by_methodid(suite.cases()), range(iterations)
    ):
        if filter_methods and not filter_methods.match(m):
            continue
        logger.info(f"Running {m}, iteration {n}")
        for tool_name, tool in random.sample(sorted(tools.items()), k=len(tools)):
            if filter_tools and not filter_tools.match(tool_name):
                logger.debug(f"{tool_name} did not match {filter_tools}")
                continue
            logger.info(f"Testing {tool_name!r}")
            try:
                fpred, time = run_cmd(
                    [tool["executable"], m], timeout=timeout, logger=logger
                )

                predictions = {}
                for line in fpred.splitlines():
                    try:
                        query, pred = line.split("\t")
                    except ValueError:
                        logger.warning("Tool produced bad output")
                        logger.warning(line)
                        continue

                    predictions[query] = Prediction.parse(pred)

            except subprocess.CalledProcessError as e:
                logger.warning(f"Tool {tool_name!r} failed with {e}")
                predictions, time = {}, 0.0
            except subprocess.TimeoutExpired:
                logger.warning(f"Tool {tool_name!r} timedout")
                predictions, time = {}, float("NaN")

            pretty = ", ".join(
                f"{k} ({str(p)})" for k, p in sorted(predictions.items())
            )

            total = 0
            for q in QUERIES:
                sometimes = any(q == c.result for c in cases)
                logger.debug(f"Check query {q!r}: {sometimes}")
                if prediction := predictions.get(q, None):
                    score = prediction.score(sometimes)
                    logger.debug(
                        f"Predicted {prediction.to_probability()}, got {score}"
                    )
                    total += score
                else:
                    logger.debug(f"No prediction")

            logger.info(f"Scored {total:0.2f} in {time:0.3}s with {pretty}")

            by_tool[tool_name].append(
                {
                    "method": m,
                    "iteration": n,
                    "wagers": {k: p.wager for k, p in predictions.items()},
                    "time": time,
                    "score": total,
                }
            )

    for k, t in by_tool.items():
        score = sum(r["score"] for r in t) + 0.0
        time = float("NaN")
        if t:
            time = sum(r["time"] for r in t) / len(t) + 0.0
        tools[k]["results"] = t
        tools[k]["score"] = score
        tools[k]["time"] = time

        logger.info(f"Tested {k}: score {score:0.2f} in avg {time:0.3f}s")

    for k in list(tools):
        if k not in tools:
            del tools[k]

    experiment["timestamp"] = int(datetime.now().timestamp() * 1000)

    print(json.dumps(experiment))


if __name__ == "__main__":
    evaluate()
