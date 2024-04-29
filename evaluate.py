#!/usr/bin/env python3
""" The jpamb evaluator
"""

from io import StringIO
from typing import TextIO, TypeVar
from collections import defaultdict
import click
import subprocess
import re
import sys
from dataclasses import dataclass

prim = bool | int


W = TypeVar("W", bound=TextIO)


def gettargets():
    return tuple(sorted(("divide by zero", "*", "assertion error", "ok")))


def print_prim(i: prim, file: W = sys.stdout) -> W:
    if isinstance(i, bool):
        if i:
            file.write("true")
        else:
            file.write("false")
    else:
        print(i, file=file, end="")
    return file


@dataclass(frozen=True)
class Input:
    val: tuple[prim, ...]

    @staticmethod
    def parse(string: str) -> "Input":
        if not (m := re.match(r"\(([^)]*)\)", string)):
            raise ValueError(f"Invalid inputs: {string!r}")
        parsed_args = []
        for i in m.group(1).split(","):
            i = i.strip()
            if not i:
                continue
            if i == "true":
                parsed_args.append(True)
            elif i == "false":
                parsed_args.append(False)
            else:
                parsed_args.append(int(i))
        return Input(tuple(parsed_args))

    def __str__(self) -> str:
        return self.print(StringIO()).getvalue()

    def print(self, file: W = sys.stdout) -> W:
        open, close = "()"
        file.write(open)
        if self.val:
            print_prim(self.val[0], file=file)
            for i in self.val[1:]:
                file.write(", ")
                print_prim(i, file=file)
        file.write(close)
        return file


@dataclass(frozen=True)
class Case:
    methodid: str
    input: Input
    result: str


@dataclass(frozen=True)
class Prediction:
    wager: float

    @staticmethod
    def parse(string: str) -> "Prediction":
        if m := re.match(r"([^%]*)\%", string):
            p = float(m.group(1)) / 100
            return Prediction.from_probability(p)
        else:
            return Prediction(float(string))

    @staticmethod
    def from_probability(p: float) -> "Prediction":
        negate = False
        if p < 0.5:
            p = 1 - p
            negate = True
        if p == 1:
            x = float("inf")
        else:
            x = ((1 - p) / p) * 0.5
        return Prediction(-x if negate else x)

    def score(self, happens: bool):
        wager = (-1 if not happens else 1) * self.wager
        if wager > 0:
            if wager == float("inf"):
                return 1
            else:
                return 1 - 1 / (wager + 1)
        else:
            return wager


def runtime(args, enable_assertions=False, **kwargs):
    pargs = ["java", "-cp", "target/classes/"]

    if enable_assertions:
        pargs += ["-ea"]

    pargs += ["jpamb.Runtime"]
    pargs += args

    return subprocess.check_output(pargs, text=True, **kwargs)


def run_cmd(cmd, /, timeout, verbose=True, **kwargs):
    import time

    if verbose:
        stderr = sys.stdout
        sys.stdout.flush()
    else:
        stderr = subprocess.DEVNULL
    try:
        start = time.time()
        cp = subprocess.run(
            cmd,
            text=True,
            stderr=stderr,
            stdout=subprocess.PIPE,
            timeout=timeout,
            check=True,
            **kwargs,
        )
        stop = time.time()
        result = cp.stdout.strip()
        if verbose:
            print()
        return (result, stop - start)
    except subprocess.CalledProcessError:
        if verbose:
            print()
        raise
    except subprocess.TimeoutExpired:
        if verbose:
            print()
        raise


def getcases():
    import csv

    cases = csv.reader(runtime([]).splitlines(), delimiter=" ", skipinitialspace=True)
    for r in sorted(cases):
        args, res = r[1].split(" -> ")
        yield Case(r[0], Input.parse(args), res)


def cases_by_methodid() -> dict[str, list[Case]]:
    cases_by_id = defaultdict(list)

    for c in getcases():
        cases_by_id[c.methodid].append(c)

    return cases_by_id


@click.group
def cli():
    """The jpamb evaluator"""


@cli.command
def rebuild():
    """Rebuild the test-suite."""
    subprocess.call(["mvn", "compile"])


@cli.command
def cases():
    """Get a list of cases to test"""
    import json

    for c in getcases():
        json.dump(c.__dict__, sys.stdout)
        print()


@cli.command
@click.option("--timeout", default=0.5)
@click.argument(
    "CMD",
    nargs=-1,
)
def test(cmd, timeout):
    """Check that all cases are valid"""
    if not cmd:
        cmd = ["java", "-cp", "target/classes", "-ea", "jpamb.Runtime"]

    cases = list(getcases())
    failed = []
    for c in cases:
        print(f"=" * 80)
        pretty_inputs = str(c.input)
        print(f"{c.methodid} with {pretty_inputs}")
        print()

        try:
            result, time = run_cmd(cmd + [c.methodid, pretty_inputs], timeout=timeout)
            success = result == c.result
            print(f"Got {result!r} in {time} which is {success}")
        except subprocess.CalledProcessError:
            success = False
            print(f"Process failed.")
        except subprocess.TimeoutExpired:
            success = "*" == c.result
            print(f"Timed out after {timeout}s which is {success}")
        if not success:
            failed += [c]
        print(f"=" * 80)
        print()

    if failed:
        print(f"Failed on {len(failed)}/{len(cases)}")
    else:
        print(f"Sucessfully handled {len(cases)} cases")


@cli.command
@click.option("--timeout", default=0.5)
@click.option("-v", "verbosity", is_flag=True)
@click.option("--target", "targets", multiple=True)
@click.argument(
    "CMD",
    nargs=-1,
)
def evaluate(cmd, timeout, targets, verbosity):
    """Given an command check if it can predict the results."""

    if not cmd:
        click.UsageError("Expected a command to evaluate")
    cmd = list(cmd)

    if not targets:
        targets = gettargets()
    resulting_targets = []
    for target in targets:
        resulting_targets.extend(target.split(","))
    targets = resulting_targets

    cases_by_method = defaultdict(list)
    for c in getcases():
        cases_by_method[c.methodid].append(c)

    results = []

    for m, cases in cases_by_method.items():
        for t in targets:
            try:
                prediction, time = run_cmd(
                    cmd + [m, t], timeout=timeout, verbose=verbosity
                )
                print(prediction)
                prediction = Prediction.parse(prediction)

                sometimes = any(c.result == t for c in cases)
                score = prediction.score(sometimes)

                result = [m, t, prediction.wager, score, time]
            except subprocess.CalledProcessError:
                result = [m, t, 0, 0, 0]
            except subprocess.TimeoutExpired:
                result = [m, t, 0, 0, timeout]
            results.append(result)

    import csv

    w = csv.writer(sys.stdout)
    w.writerow(["methodid", "target", "wager", "score", "time"])
    w.writerows(
        [r[:2] + [f"{r[2]:0.2f}", f"{r[3]:0.2f}", f"{r[4]:0.3f}"] for r in results]
    )
    w.writerow(
        [
            "-",
            "-",
            f"{sum(abs(r[2]) for r in results):0.2f}",
            f"{sum(r[3] for r in results):0.2f}",
            f"{sum(r[4] for r in results):0.2f}",
        ]
    )


@cli.command
def stats():
    methods = []

    targets = list(gettargets())

    for mid, cases in sorted(cases_by_methodid().items()):
        methods.append(
            [mid] + list(1 if any(c.result == t for c in cases) else 0 for t in targets)
        )

    import csv

    w = csv.writer(sys.stdout)
    w.writerow(["methodid"] + targets)
    w.writerows(methods)
    w.writerow(
        ["-"]
        + [
            f"{sum(m[i + 1] for m in methods) / (len(methods) * len(targets)):0.1%}"
            for i, _ in enumerate(targets)
        ]
    )


if __name__ == "__main__":
    cli()
