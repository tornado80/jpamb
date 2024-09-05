#!/usr/bin/env python3

from json import JSONDecodeError, encoder
import click
from datetime import datetime
from collections import defaultdict
import utils
import math
import numpy as np
import pandas as pd


@click.command()
@click.option("-v", "--verbose", count=True)
# @click.option(
#     "-o", "--stats", default="-", type=click.Path(writable=True, allow_dash=True)
# )
@click.option("-o", "--report", type=click.Path(writable=True))
@click.argument("FILES", nargs=-1, type=click.Path(exists=True, readable=True))
def stats(files, report, verbose):
    """A program for calculating and presenting the stats of
    a collection of experiments.
    """

    import json

    logger = utils.setup_logger(verbose)

    # swriter = csv.DictWriter(
    #     click.open_file(stats, "w"),
    #     fieldnames=["group", "version", "tool", "score", "absolute", "relative"],
    # )
    # swriter.writeheader()

    results = []

    for file in files:
        logger.info(f"Analysing {file!r}")

        try:
            with open(file, encoding="utf-8-sig") as fp:
                experiment = json.load(fp)
        except UnicodeDecodeError:
            with open(file, encoding="utf-16") as fp:
                experiment = json.load(fp)

        for tool, ctx in experiment["tools"].items():
            per_method = defaultdict(dict)

            for r in ctx["results"]:
                m = per_method[r["method"]]
                absolute = r["time"] / 1_000_000
                relative = math.log10(r["relative"])
                score = r["score"]
                m.setdefault("absolute", []).append(absolute)
                m.setdefault("relative", []).append(relative)
                m.setdefault("score", []).append(score)

            rows = []
            for m, k in sorted(per_method.items()):
                rows.append(
                    {
                        "method": m,
                        "absolute/mean": np.mean(k["absolute"]),
                        "absolute/std": np.std(k["absolute"]),
                        "relative/mean": np.mean(k["relative"]),
                        "relative/std": np.std(k["relative"]),
                        "score": np.mean(k["score"]),
                    }
                )

            is_syntactic = "syntactic" in ctx["technologies"]
            is_static = "static" in ctx["technologies"]
            is_dynamic = "dynamic" in ctx["technologies"]

            kind = None

            if is_static:
                kind = "static"

            if is_dynamic:
                kind = "dynamic"

            if is_syntactic:
                kind = "syntactic"

            if is_static and is_dynamic:
                kind = "hybrid"

            if kind is None:
                kind = "adhoc"

            df = pd.DataFrame(rows)
            result = {
                "group": experiment["group_name"],
                "version": datetime.fromtimestamp(experiment["timestamp"] / 1000),
                "tool": tool,
                "kind": kind,
                "technologies": ctx["technologies"],
                "score": df["score"].sum(),
                "absolute": df["absolute/mean"].sum(),
                "relative": math.pow(10, df["relative/mean"].mean()),
            }

            results.append(result)
            # swriter.writerow(result)

    logger.success(f"Analysed {len(files)} file")

    df = pd.DataFrame(results)
    df = df.loc[df.groupby(["group", "tool"])["version"].idxmax()]

    if report:
        import plotly.express as px

        fig = px.scatter(
            df,
            x="relative",
            y="score",
            color="kind",
            symbol="kind",
            log_x=True,
            hover_data=["group", "version", "tool", "technologies"],
        )

        fig.update_layout(template="seaborn")
        fig.update_traces(marker_size=10)

        fig.write_html(report)
        logger.success(f"Written report to {report!r}")

    print(df.set_index(["group", "tool"]))


if __name__ == "__main__":
    stats()
