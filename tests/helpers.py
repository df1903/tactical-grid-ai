from pathlib import Path
from typing import Any

from tactical_grid.algorithms.common import PathProblem, make_problem
from tactical_grid.domain.model import Position
from tactical_grid.scenario.loader import Scenario, build_scenario, load_scenario

SCENARIOS = Path(__file__).parent.parent / "scenarios"
APENDICE_A = SCENARIOS / "apendice_a.json"


def problem_from_file(path: Path) -> PathProblem:
    """Load a scenario file and build the path problem from its `prueba` section."""
    scenario = load_scenario(path)
    config = scenario.test_config
    assert config.start_unit is not None and config.goal is not None
    return make_problem(scenario.board, scenario.initial_state, config.start_unit, config.goal)


_TERRAIN_CHARS = {".": "camino", "p": "pasto", "f": "bosque", "#": "muro"}


def ascii_problem(rows: list[str]) -> PathProblem:
    """Build a pathfinding problem from an ASCII map.

    `.` camino (1), `p` pasto (2), `f` bosque (4), `#` muro, `S` start (unit A1 and base A),
    `G` goal, `X` rival unit B1 (also base B). Exactly one `S`, `G` and `X` are required.
    """
    marks: dict[str, tuple[int, int]] = {}
    grid: list[list[str]] = []
    for r, line in enumerate(rows):
        row: list[str] = []
        for c, ch in enumerate(line):
            if ch in "SGX":
                marks[ch] = (r, c)
                row.append("camino")
            else:
                row.append(_TERRAIN_CHARS[ch])
        grid.append(row)
    sr, sc = marks["S"]
    gr, gc = marks["G"]
    xr, xc = marks["X"]
    raw: dict[str, Any] = {
        "mapa": {"filas": len(rows), "columnas": len(rows[0])},
        "tipos_terreno": {
            "camino": {"costo": 1, "transitable": True},
            "pasto": {"costo": 2, "transitable": True},
            "bosque": {"costo": 4, "transitable": True},
            "muro": {"transitable": False},
        },
        "terreno": grid,
        "bases": {"A": {"fila": sr, "columna": sc}, "B": {"fila": xr, "columna": xc}},
        "recurso": {"fila": gr, "columna": gc},
        "unidades": [
            {"id": "A1", "bando": "A", "tipo": "estandar", "fila": sr, "columna": sc},
            {"id": "B1", "bando": "B", "tipo": "estandar", "fila": xr, "columna": xc},
        ],
        "turno": "A",
        "juego": {"portador_recurso": None},
    }
    scenario = build_scenario(raw)
    return make_problem(scenario.board, scenario.initial_state, "A1", Position(gr, gc))


def mini_race() -> Scenario:
    """5x7 open map, two units per side, resource (0,1) next to base A: a race to count by hand."""
    units = [("A1", "A", 1, 0), ("A2", "A", 0, 2), ("B1", "B", 1, 2), ("B2", "B", 2, 4)]
    return build_scenario(
        {
            "version": "1.0",
            "mapa": {"filas": 5, "columnas": 7},
            "tipos_terreno": {"camino": {"costo": 1, "transitable": True}},
            "terreno": [["camino"] * 7 for _ in range(5)],
            "bases": {"A": {"fila": 0, "columna": 0}, "B": {"fila": 4, "columna": 6}},
            "recurso": {"fila": 0, "columna": 1},
            "unidades": [
                {"id": uid, "bando": side, "tipo": "estandar", "fila": r, "columna": c}
                for uid, side, r, c in units
            ],
            "turno": "A",
            "juego": {"portador_recurso": None, "limite_turnos": 50},
        }
    )
