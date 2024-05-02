#!/usr/bin/env python3
""" This is the analysis script.
"""

import click
import numpy as np


def difftime(time, base_tool):
    logtime = np.log10(time)
    logtime = logtime.unstack("tool_name")

    return logtime.add(-logtime[base_tool], axis=0).stack(0)


def mean_stddev(array):
    return np.power(np.power(array, 2).mean(), 1 / 2)


def format_number_with_unsertainty(a):
    return "{:0.4f} ± {:0.4f}".format(a["mean"], a["std"])


def format_lognumber_with_unsertainty(a):
    return "{:0.4f} ⋇ {:0.4f}".format(10 ** a["mean"], 10 ** a["std"])


def draw_diagram(logtime, score):
    import matplotlib.pyplot as plt
    import matplotlib.axes as axes

    ax: axes.Axes
    _, ax = plt.subplots(1)  # pyright: ignore

    ax.set_yscale("log")  # type: ignore
    lm = logtime["mean"]
    ls = logtime["std"]

    ax.errorbar(
        score,
        10**lm,
        yerr=[10**lm - 10 ** (lm - ls), 10 ** (lm + ls) - 10**lm],
        fmt="o",
    )

    plt.show()


@click.command
@click.argument("file", type=click.File("r"))
def analyze(file):
    import pandas as pd

    df = pd.read_csv(file, index_col=["method", "query", "iter", "tool_name"])

    base_tool = df.index[0][-1]

    idx = pd.IndexSlice
    print(df.loc[idx[:, "*", :, :], :])

    logtime = (
        difftime(df.time, base_tool)
        .groupby(["tool_name", "query"])
        .aggregate(["mean", "std"])
    )

    score = (
        df.groupby(["method", "query", "tool_name"])["score"]
        .min()
        .groupby(["tool_name", "query"])
        .sum()
    )

    print(
        pd.concat(
            [score, logtime.apply(format_lognumber_with_unsertainty, axis=1)],
            keys=["score", "time"],
            axis=1,
        )
    )


if __name__ == "__main__":
    analyze()
