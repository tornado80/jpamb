#!/usr/bin/env python3
""" The jpamb evaluator
"""

from io import StringIO
from typing import TextIO, TypeVar
from pathlib import Path
from collections import Counter, defaultdict
import click
import csv
import subprocess
import re
import sys
from dataclasses import dataclass

import os


prim = bool | int


W = TypeVar("W", bound=TextIO)


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

    def check(self, cmd, timeout, verbose=False):
        pretty_inputs = str(self.input)
        try:
            result, time = run_cmd(
                cmd + [self.methodid, pretty_inputs], timeout=timeout, verbose=verbose
            )
            success = result == self.result
            if verbose:
                print(f"Got {result!r} in {time} which is {success}")
        except subprocess.CalledProcessError:
            success = False
            if verbose:
                print(f"Process failed.")
        except subprocess.TimeoutExpired:
            success = "*" == self.result
            if verbose:
                print(f"Timed out after {timeout}s which is {success}")
        return success

    @staticmethod
    def from_spec(line):
        if not (m := re.match(r"([^ ]*) +(\([^)]*\)) -> (.*)", line)):
            raise ValueError(f"Unexpected line: {line!r}")
        return Case(m.group(1), Input.parse(m.group(2)), m.group(3))

    def __str__(self) -> str:
        name = self.methodid.split(":")[0]
        return f"{name}:{self.input} -> {self.result}"


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
            x = -((1 - p) / p - 1) / 2
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


def read_cases(workfolder):
    with open(workfolder / "stats" / "cases.txt", "r") as f:
        for r in f.readlines():
            yield Case.from_spec(r[:-1])


def read_cases_by_methodid(workfolder) -> dict[str, list[Case]]:
    cases_by_id = defaultdict(list)

    for c in read_cases(workfolder):
        cases_by_id[c.methodid].append(c)

    return cases_by_id


TARGETS = [
    "*",
    "assertion error",
    "divide by zero",
    "ok",
]


def add_targets(m):
    def validate(ctx_, param_, targets):
        resulting_targets = []
        for target in targets:
            resulting_targets.extend(target.split(","))
        targets = resulting_targets
        return targets

    return click.option(
        "--target",
        "targets",
        multiple=True,
        show_default=True,
        default=TARGETS,
        callback=validate,
    )(m)


WORKFOLDER = Path(os.path.abspath(__file__)).parent


def add_workfolder(m):
    return click.option(
        "--workfolder",
        type=click.types.Path(),
        show_default=True,
        default=WORKFOLDER,
        callback=lambda _ctx, _parm, value: Path(value),
    )(m)


@click.group
def cli():
    """The jpamb evaluator"""


@cli.command
@add_workfolder
def cases(workfolder):
    """Get a list of cases to test"""
    import json

    for c in read_cases(workfolder):
        json.dump(c.__dict__, sys.stdout)
        print()


@cli.command
@click.option("--check/--no-check", default=True)
@add_targets
@add_workfolder
def rebuild(check, targets, workfolder):
    """Rebuild the benchmark-suite."""
    subprocess.call(["mvn", "compile"])

    if not check:
        return

    stats = workfolder / "stats"
    stats.mkdir(parents=True, exist_ok=True)

    cases = runtime([])
    with open(stats / "cases.txt", "w") as f:
        f.write(cases)

    failed = []
    cases_by_id = defaultdict(list)
    for case in cases.splitlines():
        case = Case.from_spec(case)

        cmd = ["java", "-cp", "target/classes", "-ea", "jpamb.Runtime"]
        print(f"Test {case!s:<74}: ", end="")
        sys.stdout.flush()
        success = case.check(cmd, timeout=0.5, verbose=False)
        print(success)
        if not success:
            failed.append(case)
        cases_by_id[case.methodid].append(case)

    if failed:
        print("Failed checks:")
        for f in failed:
            print(f)
        sys.exit(-1)

    print("Successfully verified all cases.")

    with open(stats / "distribution.csv", "w") as f:
        w = csv.writer(f)
        w.writerow(["methodid"] + targets)

        sums = Counter()
        total = 0

        for mid, cases in sorted(cases_by_id.items()):
            occ = []
            for t in targets:
                if any(c.result == t for c in cases):
                    occ.append(1)
                    sums[t] += 1
                else:
                    occ.append(0)
                total += 1

            w.writerow([mid] + occ)

        w.writerow(["-"] + [f"{sums[t] / total:0.2%}" for t in targets])


@cli.command
@click.option("--timeout", default=0.5)
@add_workfolder
@click.argument(
    "CMD",
    nargs=-1,
)
def test(cmd, timeout, workfolder):
    """Check that all cases are valid"""
    if not cmd:
        cmd = ["java", "-cp", "target/classes", "-ea", "jpamb.Runtime"]

    counter = 0
    failed = []
    for c in read_cases(workfolder):
        counter += 1
        print(f"=" * 80)
        pretty_inputs = str(c.input)
        print(f"{c.methodid} with {pretty_inputs}")
        print()

        success = c.check(cmd, timeout=timeout, verbose=True)

        if not success:
            failed += [c]

        print(f"=" * 80)
        print()

    if failed:
        print(f"Failed on {len(failed)}/{counter}")
    else:
        print(f"Sucessfully handled {counter} cases")


@cli.command
@click.option("--timeout", default=0.5)
@click.option("-v", "verbosity", is_flag=True)
@add_targets
@add_workfolder
@click.argument(
    "CMD",
    nargs=-1,
)
def evaluate(cmd, timeout, targets, verbosity, workfolder):
    """Given an command check if it can predict the results."""

    if not cmd:
        raise click.UsageError("Expected a command to evaluate")
    cmd = list(cmd)

    results = []
    for m, cases in read_cases_by_methodid(workfolder).items():
        for t in targets:
            try:
                prediction, time = run_cmd(
                    cmd + [m, t], timeout=timeout, verbose=verbosity
                )
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


if __name__ == "__main__":
    cli()
