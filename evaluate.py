#!/usr/bin/env python3
""" The jpamb evaluator
"""

import click
import subprocess
import sys
from dataclasses import dataclass

prim = bool | int


@dataclass
class Case:
    methodid: str
    input: str
    result: str


def rebuild():
    subprocess.call(["mvn", "compile"])


def runtime(args, enable_assertions=False, **kwargs):
    pargs = ["java", "-cp", "target/classes/"]

    if enable_assertions:
        pargs += ["-ea"]

    pargs += ["jpamb.Runtime"]
    pargs += args

    return subprocess.check_output(pargs, text=True, **kwargs)


def getcases():
    import csv

    for r in sorted(
        csv.reader(runtime([]).splitlines(), delimiter=" ", skipinitialspace=True)
    ):
        yield Case(r[0], *r[1].split(" -> "))


@click.group
def cli():
    """The jpamb evaluator"""


@cli.command
def cases():
    """Get a list of cases to test"""
    for c in getcases():
        print(c)


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

    rebuild()

    cases = list(getcases())
    failed = []
    for c in cases:
        print(f"=" * 80)
        print(f"{c.methodid} with {c.input}")
        print()
        sys.stdout.flush()

        try:
            cp = subprocess.run(
                cmd + [c.methodid, c.input],
                text=True,
                stderr=sys.stdout,
                stdout=subprocess.PIPE,
                timeout=timeout,
                check=True,
            )
            result = cp.stdout.strip()
            success = result == c.result
            print()
            print(f"Got {result} which is {success}")
        except subprocess.CalledProcessError:
            print()
            print(f"Process failed.")
            success = False
        except subprocess.TimeoutExpired:
            success = "*" == c.result
            print()
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
def evaluate():
    """Check that all cases are valid"""
    for c in getcases():
        try:
            result = runtime(
                [c.methodid, c.input],
                enable_assertions=True,
                timeout=0.5,
            ).strip()
        except subprocess.TimeoutExpired:
            result = "*"
        print(c, result == c.result)


if __name__ == "__main__":
    cli()
