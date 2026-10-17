"""Scenario JSON loading with atomic validation (RF-34, RF-35).

JSON keys are Spanish and are read only here; the domain uses English names.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeGuard

from tactical_grid.domain.model import Board, GameState, Position, Side, Terrain

DEFAULT_TURN_LIMIT = 100

# Optional extra section `utilidad` (RNF-02). Values below apply only when the JSON omits a key.
UTILITY_KEYS = {
    "entrega": "delivery",
    "recurso_cargado": "carry",
    "distancia_objetivo": "goal_distance",
    "distancia_rival": "rival_distance",
}
DEFAULT_UTILITY_WEIGHTS: Mapping[str, float] = {
    "delivery": 10.0,
    "carry": 3.0,
    "goal_distance": 1.0,
    "rival_distance": 0.5,
}


class ScenarioError(Exception):
    """Raised when a scenario is invalid; carries every detected error."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


@dataclass(frozen=True)
class TestConfig:
    __test__ = False  # not a pytest class

    mode: str | None
    start_unit: str | None
    goal: Position | None
    minimax_depth: int | None
    # Optional extra `prueba` fields (RNF-02, G10): all default to None when absent.
    algorithm: str | None = None
    heuristic: str | None = None
    beam_width: int | None = None
    action_order: str | None = None


@dataclass(frozen=True)
class Scenario:
    board: Board
    initial_state: GameState
    test_config: TestConfig
    utility_weights: Mapping[str, float] = field(default_factory=lambda: DEFAULT_UTILITY_WEIGHTS)


def load_scenario(path: str | Path) -> Scenario:
    """Load and validate a scenario file; all-or-nothing.

    Purpose: build domain objects from JSON only if all RF-35 validations pass.
    Preconditions: `path` points to a UTF-8 JSON file.
    Postconditions: returns a Scenario, or raises ScenarioError listing every error;
        nothing is built or modified when any error exists.
    Complexity: O(R * C + U).
    AI usage: Claude Code (Sonnet 5.5) drafted the loader from RF-34/RF-35.
    AI intervention: added a check that two units cannot share a cell.
    Student validation: pending cross-review by the other team member.
    """
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScenarioError([f"cannot read scenario {path}: {exc}"]) from exc
    if not isinstance(raw, dict):
        raise ScenarioError(["the scenario root must be a JSON object"])
    return build_scenario(raw)


def build_scenario(raw: dict[str, Any]) -> Scenario:
    errors: list[str] = []

    rows, cols = _read_dimensions(raw, errors)
    terrains = _read_terrains(raw, errors)
    grid = _read_grid(raw, rows, cols, terrains, errors)
    bases = _read_bases(raw, rows, cols, errors)
    resource = _read_position(raw.get("recurso"), "recurso", rows, cols, errors)
    units = _read_units(raw, rows, cols, terrains, grid, errors)
    turn = _read_side(raw.get("turno"), "turno", errors)
    carrier = _read_carrier(raw, units, errors)
    turn_limit = _read_turn_limit(raw, errors)
    weights = _read_utility_weights(raw, errors)

    if errors or rows is None or cols is None or grid is None or turn is None:
        raise ScenarioError(errors or ["incomplete scenario"])

    assert terrains is not None and bases is not None
    positions = tuple(sorted((uid, pos) for uid, (_, pos) in units.items()))
    board = Board(
        rows=rows,
        cols=cols,
        grid=grid,
        terrains=terrains,
        bases=bases,
        unit_sides={uid: side for uid, (side, _) in units.items()},
        turn_limit=turn_limit,
    )
    state = GameState(
        positions=positions,
        carrier=carrier,
        resource=None if carrier is not None else resource,
        turn=turn,
    )
    return Scenario(
        board=board,
        initial_state=state,
        test_config=_read_test_config(raw),
        utility_weights=weights,
    )


def _is_int(value: object) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: object) -> TypeGuard[float]:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _read_dimensions(raw: dict[str, Any], errors: list[str]) -> tuple[int | None, int | None]:
    mapa = raw.get("mapa")
    if not isinstance(mapa, dict):
        errors.append("validation 1: 'mapa' with 'filas' and 'columnas' is required")
        return None, None
    rows, cols = mapa.get("filas"), mapa.get("columnas")
    ok = True
    for name, value in (("filas", rows), ("columnas", cols)):
        if not _is_int(value) or value <= 0:
            errors.append(f"validation 1: mapa.{name} must be a positive integer, got {value!r}")
            ok = False
    return (rows, cols) if ok else (None, None)


def _read_terrains(raw: dict[str, Any], errors: list[str]) -> dict[str, Terrain] | None:
    catalog = raw.get("tipos_terreno")
    if not isinstance(catalog, dict) or not catalog:
        errors.append("validation 2: 'tipos_terreno' must be a non-empty object")
        return None
    terrains: dict[str, Terrain] = {}
    for name, spec in catalog.items():
        if not isinstance(spec, dict) or not isinstance(spec.get("transitable"), bool):
            errors.append(f"terrain '{name}': 'transitable' must be true or false")
            continue
        passable = spec["transitable"]
        cost = spec.get("costo")
        if passable:
            if not _is_number(cost) or cost <= 0:
                errors.append(
                    f"validation 3: passable terrain '{name}' needs a positive 'costo', "
                    f"got {cost!r}"
                )
                continue
            terrains[name] = Terrain(cost=float(cost), passable=True)
        else:
            terrains[name] = Terrain(cost=None, passable=False)
    return terrains


def _read_grid(
    raw: dict[str, Any],
    rows: int | None,
    cols: int | None,
    terrains: dict[str, Terrain] | None,
    errors: list[str],
) -> tuple[tuple[str, ...], ...] | None:
    matrix = raw.get("terreno")
    if not isinstance(matrix, list):
        errors.append("validation 1: 'terreno' must be a matrix")
        return None
    if rows is not None and len(matrix) != rows:
        errors.append(f"validation 1: 'terreno' has {len(matrix)} rows, mapa.filas is {rows}")
        return None
    grid: list[tuple[str, ...]] = []
    ok = True
    for r, line in enumerate(matrix):
        if not isinstance(line, list) or (cols is not None and len(line) != cols):
            size = len(line) if isinstance(line, list) else line
            errors.append(f"validation 1: row {r} of 'terreno' has {size}, mapa.columnas is {cols}")
            ok = False
            continue
        for c, name in enumerate(line):
            if not isinstance(name, str) or (terrains is not None and name not in terrains):
                errors.append(f"validation 2: cell ({r},{c}) uses unknown terrain {name!r}")
                ok = False
        grid.append(tuple(str(name) for name in line))
    return tuple(grid) if ok else None


def _read_side(value: object, label: str, errors: list[str]) -> Side | None:
    if isinstance(value, str) and value.upper() in ("A", "B"):
        return Side(value.upper())
    code = 8 if label == "turno" else 7
    errors.append(f"validation {code}: {label} must be 'a' or 'b', got {value!r}")
    return None


def _read_position(
    value: object, label: str, rows: int | None, cols: int | None, errors: list[str]
) -> Position | None:
    if (
        not isinstance(value, dict)
        or not _is_int(value.get("fila"))
        or not _is_int(value.get("columna"))
    ):
        errors.append(f"validation 4: {label} needs integer 'fila' and 'columna'")
        return None
    pos = Position(value["fila"], value["columna"])
    if rows is not None and cols is not None and not (0 <= pos.row < rows and 0 <= pos.col < cols):
        errors.append(f"validation 4: {label} {pos.row},{pos.col} is outside the {rows}x{cols} map")
        return None
    return pos


def _read_bases(
    raw: dict[str, Any], rows: int | None, cols: int | None, errors: list[str]
) -> dict[Side, Position] | None:
    bases = raw.get("bases")
    if not isinstance(bases, dict):
        errors.append("validation 4: 'bases' must define bases 'A' and 'B'")
        return None
    result: dict[Side, Position] = {}
    for key, value in bases.items():
        if not isinstance(key, str) or key.upper() not in ("A", "B"):
            errors.append(f"validation 7: base key {key!r} must be 'a' or 'b'")
            continue
        pos = _read_position(value, f"base {key}", rows, cols, errors)
        if pos is not None:
            result[Side(key.upper())] = pos
    if len(result) != 2 and not errors:
        errors.append("validation 4: both bases 'A' and 'B' are required")
    return result if len(result) == 2 else None


def _read_units(
    raw: dict[str, Any],
    rows: int | None,
    cols: int | None,
    terrains: dict[str, Terrain] | None,
    grid: tuple[tuple[str, ...], ...] | None,
    errors: list[str],
) -> dict[str, tuple[Side, Position]]:
    raw_units = raw.get("unidades")
    units: dict[str, tuple[Side, Position]] = {}
    if not isinstance(raw_units, list):
        errors.append("'unidades' must be a list")
        return units
    cells: dict[Position, str] = {}
    for index, item in enumerate(raw_units):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            errors.append(f"unit #{index}: 'id' must be a string")
            continue
        uid = item["id"]
        label = f"unit {uid}"
        if uid in units:
            errors.append(f"validation 6: unit id '{uid}' is repeated")
            continue
        side = _read_side(item.get("bando"), f"{label} bando", errors)
        pos = _read_position(item, label, rows, cols, errors)
        if side is None or pos is None:
            continue
        if terrains is not None and grid is not None:
            terrain = terrains.get(grid[pos.row][pos.col])
            if terrain is not None and not terrain.passable:
                errors.append(
                    f"validation 5: {label} is on a non-passable cell {pos.row},{pos.col}"
                )
                continue
        if pos in cells:
            errors.append(f"{label} shares cell {pos.row},{pos.col} with unit {cells[pos]}")
            continue
        cells[pos] = uid
        units[uid] = (side, pos)
    return units


def _read_carrier(
    raw: dict[str, Any], units: dict[str, tuple[Side, Position]], errors: list[str]
) -> str | None:
    juego = raw.get("juego", {})
    if not isinstance(juego, dict):
        errors.append("'juego' must be an object")
        return None
    carrier = juego.get("portador_recurso")
    if carrier is None:
        return None
    if not isinstance(carrier, str) or carrier not in units:
        errors.append(f"validation 9: portador_recurso {carrier!r} is not an existing unit")
        return None
    return carrier


def _read_turn_limit(raw: dict[str, Any], errors: list[str]) -> int:
    juego = raw.get("juego", {})
    limit = juego.get("limite_turnos") if isinstance(juego, dict) else None
    if limit is None:
        return DEFAULT_TURN_LIMIT
    if not _is_int(limit) or limit <= 0:
        errors.append(f"juego.limite_turnos must be a positive integer, got {limit!r}")
        return DEFAULT_TURN_LIMIT
    return int(limit)


def _read_utility_weights(raw: dict[str, Any], errors: list[str]) -> dict[str, float]:
    weights = dict(DEFAULT_UTILITY_WEIGHTS)
    section = raw.get("utilidad")
    if section is None:
        return weights
    if not isinstance(section, dict):
        errors.append("'utilidad' must be an object")
        return weights
    for key, value in section.items():
        if key not in UTILITY_KEYS:
            errors.append(f"utilidad.{key} is unknown; expected one of {sorted(UTILITY_KEYS)}")
        elif not _is_number(value) or value < 0:
            errors.append(f"utilidad.{key} must be a non-negative number, got {value!r}")
        else:
            weights[UTILITY_KEYS[key]] = float(value)
    return weights


def _read_test_config(raw: dict[str, Any]) -> TestConfig:
    prueba = raw.get("prueba")
    prueba = prueba if isinstance(prueba, dict) else {}
    juego = raw.get("juego")
    juego = juego if isinstance(juego, dict) else {}
    goal = prueba.get("objetivo")
    depth = juego.get("profundidad_maxima_minimax")
    return TestConfig(
        mode=prueba.get("modo") if isinstance(prueba.get("modo"), str) else None,
        start_unit=prueba.get("unidad_inicio")
        if isinstance(prueba.get("unidad_inicio"), str)
        else None,
        goal=Position(goal["fila"], goal["columna"])
        if isinstance(goal, dict) and _is_int(goal.get("fila")) and _is_int(goal.get("columna"))
        else None,
        minimax_depth=depth if _is_int(depth) else None,
        algorithm=_text(prueba.get("algoritmo")),
        heuristic=_text(prueba.get("heuristica")),
        beam_width=prueba["k"] if _is_int(prueba.get("k")) else None,
        action_order=_text(prueba.get("orden_acciones")),
    )


def _text(value: object) -> str | None:
    return value if isinstance(value, str) else None
