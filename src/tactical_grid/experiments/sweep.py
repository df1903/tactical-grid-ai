"""Experiment sweeps and result export (RF-16, RF-29, RF-32, RF-38, RF-39).

A sweep runs one scenario under several algorithms, heuristics, beam widths, depths or action
orders and collects one report per run. Metrics go to CSV (one row per run, flat) and the full
reports, with paths, root values and verification checks, go to JSON.
"""

import csv
import json
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from tactical_grid.experiments.runner import RunOptions, canonical, run
from tactical_grid.scenario.loader import Scenario


@dataclass(frozen=True)
class Sweep:
    """Values to combine; an empty tuple means "use the scenario's `prueba` value"."""

    base: RunOptions = RunOptions()
    algorithms: tuple[str, ...] = ()
    heuristics: tuple[str, ...] = ()
    ks: tuple[int, ...] = ()
    depths: tuple[int, ...] = ()
    orders: tuple[str, ...] = ()


def expand(scenario: Scenario, sweep: Sweep) -> list[RunOptions]:
    """List the runs of a sweep, in a deterministic order.

    Purpose: turn lists of values into single runs, combining only what applies: heuristics
        for A* and Beam, `k` for Beam, depths and orders for Minimax and alpha-beta.
    Preconditions: `sweep` values are valid; invalid ones fail later with RunError in `run`.
    Postconditions: always at least one run; the algorithm falls back to `prueba.algoritmo`.
    Complexity: O(product of the list lengths).
    AI usage: Claude Code (Sonnet 5.5) drafted the function.
    AI intervention: none after the draft.
    Student validation: pending cross-review by the other team member.
    """
    config = scenario.test_config
    mode = (sweep.base.mode or config.mode or "").lower()
    algorithms: Sequence[str | None] = sweep.algorithms or (config.algorithm,)
    heuristics: Sequence[str | None] = sweep.heuristics or (None,)
    ks: Sequence[int | None] = sweep.ks or (None,)
    depths: Sequence[int | None] = sweep.depths or (None,)
    orders: Sequence[str | None] = sweep.orders or (None,)

    runs: list[RunOptions] = []
    for algorithm in algorithms:
        base = replace(sweep.base, algorithm=algorithm)
        name = canonical(algorithm) if algorithm else ""
        if mode == "adversarial":
            runs += [replace(base, depth=d, order=o) for d in depths for o in orders]
        elif name == "A_STAR":
            runs += [replace(base, heuristic=h) for h in heuristics]
        elif name == "BEAM":
            runs += [replace(base, heuristic=h, k=k) for h in heuristics for k in ks]
        else:
            runs.append(base)
    return runs


def run_sweep(scenario: Scenario, sweep: Sweep) -> list[dict[str, Any]]:
    return [run(scenario, options) for options in expand(scenario, sweep)]


def flatten(report: dict[str, Any]) -> dict[str, Any]:
    """One CSV row: the path becomes `r,c;r,c` and the checks collapse to a single flag."""
    row: dict[str, Any] = {}
    for key, value in report.items():
        if key == "camino":
            row[key] = ";".join(f"{r},{c}" for r, c in value)
        elif key == "verificacion":
            row["verificacion_ok"] = all(check["ok"] for check in value)
        elif key in ("valores_raiz", "unidades", "bases", "mapa"):
            continue  # structured data lives in the JSON export
        else:
            row[key] = value
    return row


def write_csv(path: str | Path, reports: Sequence[dict[str, Any]]) -> None:
    rows = [flatten(report) for report in reports]
    columns: list[str] = []
    for row in rows:
        columns += [key for key in row if key not in columns]
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, restval="", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: str | Path, reports: Sequence[dict[str, Any]]) -> None:
    Path(path).write_text(
        json.dumps(list(reports), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
