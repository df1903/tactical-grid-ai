"""Command line: load a scenario JSON, run its test (or an override) and print the report."""

import argparse
import json
import sys
from collections.abc import Sequence

from tactical_grid.domain.model import Position
from tactical_grid.experiments.runner import MODES, RunError, RunOptions, run
from tactical_grid.scenario.loader import ScenarioError, load_scenario


def _goal(text: str) -> Position:
    try:
        row, col = (int(part) for part in text.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("goal must be row,col (for example 3,2)") from exc
    return Position(row, col)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tactical_grid",
        description="Run a TacticalGrid test; options override the scenario's `prueba` section.",
    )
    parser.add_argument("scenario", nargs="?", help="path to the scenario JSON")
    parser.add_argument("--mode", choices=MODES)
    parser.add_argument(
        "--algorithm",
        help="BFS, DFS, UCS, A_STAR (A*, A_ESTRELLA), BEAM, MINIMAX or ALPHA_BETA",
    )
    parser.add_argument("--heuristic", help="H1 (Manhattan) or H2 (obstacle aware); A* and Beam")
    parser.add_argument("--k", type=int, help="beam width")
    parser.add_argument("--depth", type=int, help="Minimax depth (default: from the JSON)")
    parser.add_argument("--order", choices=("default", "reversed"), help="action order")
    parser.add_argument("--unit", help="start unit of a search")
    parser.add_argument("--goal", type=_goal, help="goal cell of a search, as row,col")
    parser.add_argument("--verify", action="store_true", help="run the RF-42 checks")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.scenario is None:
        print("TacticalGrid")
        parser.print_usage()
        return 0
    try:
        scenario = load_scenario(args.scenario)
        options = RunOptions(
            mode=args.mode,
            algorithm=args.algorithm,
            heuristic=args.heuristic,
            k=args.k,
            depth=args.depth,
            order=args.order,
            unit=args.unit,
            goal=args.goal,
            verify=args.verify,
        )
        report = run(scenario, options)
    except ScenarioError as exc:
        print("invalid scenario:", file=sys.stderr)
        for error in exc.errors:
            print(f"  - {error}", file=sys.stderr)
        return 2
    except RunError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
