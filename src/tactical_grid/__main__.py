"""Command line: load a scenario JSON, run its test (or a sweep) and print the report."""

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from typing import Any

from tactical_grid.domain.model import Position
from tactical_grid.experiments.runner import MODES, PLAYS, VARIANTS, RunError, RunOptions
from tactical_grid.experiments.sweep import Sweep, run_sweep, write_csv, write_json
from tactical_grid.scenario.loader import ScenarioError, load_scenario


# Convierte un texto "fila,col" en una posición (para el argumento --goal)
def _goal(text: str) -> Position:
    try:
        row, col = (int(part) for part in text.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("goal must be row,col (for example 3,2)") from exc
    return Position(row, col)


# Crea un lector de listas separadas por comas, aplicando `convert` a cada elemento
def _list_of[T](convert: Callable[[str], T]) -> Callable[[str], tuple[T, ...]]:
    def parse(text: str) -> tuple[T, ...]:
        try:
            return tuple(convert(part.strip()) for part in text.split(",") if part.strip())
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"invalid list {text!r}: {exc}") from exc

    return parse


# Define los argumentos de la línea de comandos
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tactical_grid",
        description="Run a TacticalGrid test; options override the scenario's `prueba` section. "
        "Options marked (list) accept comma-separated values and run every combination.",
    )
    parser.add_argument("scenario", nargs="?", help="path to the scenario JSON")
    parser.add_argument("--mode", choices=MODES)
    parser.add_argument(
        "--algorithm",
        type=_list_of(str),
        help="(list) BFS, DFS, UCS, A_STAR (A*, A_ESTRELLA), BEAM, MINIMAX or ALPHA_BETA",
    )
    parser.add_argument(
        "--heuristic", type=_list_of(str), help="(list) H1 (Manhattan) or H2 (obstacle aware)"
    )
    parser.add_argument("--k", type=_list_of(int), help="(list) beam width")
    parser.add_argument("--depth", type=_list_of(int), help="(list) Minimax depth")
    parser.add_argument(
        "--order", type=_list_of(str), help="(list) action order: default or reversed"
    )
    parser.add_argument(
        "--variant",
        choices=VARIANTS,
        help="adversarial rules: base or dinamica (default: scenario)",
    )
    parser.add_argument(
        "--play",
        choices=PLAYS,
        help="mode partida: auto (AI vs AI) or humano (you vs the AI); omit to only describe",
    )
    parser.add_argument("--side", choices=("A", "B"), help="your side with --play humano (A)")
    parser.add_argument("--unit", help="start unit of a search")
    parser.add_argument("--goal", type=_goal, help="goal cell of a search, as row,col")
    parser.add_argument("--verify", action="store_true", help="run the RF-42 checks")
    parser.add_argument("--csv", metavar="PATH", help="write the metrics, one row per run")
    parser.add_argument("--json", metavar="PATH", help="write the full reports as JSON")
    return parser


# Punto de entrada: carga el escenario, ejecuta la prueba o el barrido e imprime el reporte
def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # sin escenario solo se muestra el uso
    if args.scenario is None:
        print("TacticalGrid")
        parser.print_usage()
        return 0
    try:
        scenario = load_scenario(args.scenario)
        # las opciones de la terminal se agrupan en un barrido (una sola corrida si no hay listas)
        sweep = Sweep(
            base=RunOptions(
                mode=args.mode,
                unit=args.unit,
                goal=args.goal,
                verify=args.verify,
                variant=args.variant,
                play=args.play,
                side=args.side,
            ),
            algorithms=args.algorithm or (),
            heuristics=args.heuristic or (),
            ks=args.k or (),
            depths=args.depth or (),
            orders=args.order or (),
        )
        reports = run_sweep(scenario, sweep)
        # exportación opcional a CSV y JSON
        if args.csv:
            write_csv(args.csv, reports)
        if args.json:
            write_json(args.json, reports)
    # errores del escenario o de la ejecución: se muestran y se sale con código 2
    except ScenarioError as exc:
        print("invalid scenario:", file=sys.stderr)
        for error in exc.errors:
            print(f"  - {error}", file=sys.stderr)
        return 2
    except (RunError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    # una sola corrida se imprime como objeto; varias, como lista
    output: Any = reports[0] if len(reports) == 1 else reports
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
