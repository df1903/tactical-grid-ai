import copy
import json
from pathlib import Path
from typing import Any

import pytest

from tactical_grid.domain.model import Position, Side
from tactical_grid.scenario.loader import (
    DEFAULT_TURN_LIMIT,
    ScenarioError,
    build_scenario,
    load_scenario,
)

APENDICE_A = Path(__file__).parent.parent / "scenarios" / "apendice_a.json"


def raw_scenario() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(APENDICE_A.read_text(encoding="utf-8"))
    return copy.deepcopy(data)


def errors_of(raw: dict[str, Any]) -> list[str]:
    with pytest.raises(ScenarioError) as info:
        build_scenario(raw)
    return info.value.errors


def test_loads_official_example() -> None:
    scenario = load_scenario(APENDICE_A)
    assert (scenario.board.rows, scenario.board.cols) == (4, 4)
    assert scenario.board.bases[Side.B] == Position(3, 3)
    assert scenario.board.turn_limit == DEFAULT_TURN_LIMIT
    assert scenario.initial_state.turn is Side.A
    assert scenario.initial_state.resource == Position(2, 2)
    assert scenario.initial_state.carrier is None
    assert scenario.test_config.goal == Position(3, 2)
    assert scenario.test_config.minimax_depth == 4


def test_v1_rows_and_columns_must_match_matrix() -> None:
    raw = raw_scenario()
    raw["mapa"]["filas"] = 5
    assert any("validation 1" in e for e in errors_of(raw))


def test_v1_rows_must_be_positive() -> None:
    raw = raw_scenario()
    raw["mapa"]["columnas"] = 0
    assert any("validation 1" in e for e in errors_of(raw))


def test_v2_unknown_terrain() -> None:
    raw = raw_scenario()
    raw["terreno"][0][0] = "lava"
    assert any("validation 2" in e and "lava" in e for e in errors_of(raw))


def test_v3_passable_terrain_needs_positive_cost() -> None:
    raw = raw_scenario()
    raw["tipos_terreno"]["pasto"]["costo"] = 0
    assert any("validation 3" in e and "pasto" in e for e in errors_of(raw))


def test_v4_unit_outside_map() -> None:
    raw = raw_scenario()
    raw["unidades"][0]["fila"] = 9
    assert any("validation 4" in e for e in errors_of(raw))


def test_v4_resource_outside_map() -> None:
    raw = raw_scenario()
    raw["recurso"] = {"fila": 0, "columna": 7}
    assert any("validation 4" in e and "recurso" in e for e in errors_of(raw))


def test_v4_base_outside_map() -> None:
    raw = raw_scenario()
    raw["bases"]["A"] = {"fila": -1, "columna": 0}
    assert any("validation 4" in e and "base A" in e for e in errors_of(raw))


def test_v5_unit_on_non_passable_cell() -> None:
    raw = raw_scenario()
    raw["unidades"][0].update(fila=1, columna=1)  # muro
    assert any("validation 5" in e for e in errors_of(raw))


def test_v6_unit_ids_unique() -> None:
    raw = raw_scenario()
    raw["unidades"][1]["id"] = "A1"
    assert any("validation 6" in e for e in errors_of(raw))


def test_v7_unit_side_must_be_a_or_b() -> None:
    raw = raw_scenario()
    raw["unidades"][0]["bando"] = "C"
    assert any("validation 7" in e for e in errors_of(raw))


def test_v8_turn_must_be_a_or_b() -> None:
    raw = raw_scenario()
    raw["turno"] = "x"
    assert any("validation 8" in e for e in errors_of(raw))


def test_v9_carrier_must_exist() -> None:
    raw = raw_scenario()
    raw["juego"]["portador_recurso"] = "Z9"
    assert any("validation 9" in e for e in errors_of(raw))


def test_carrier_removes_resource_cell() -> None:
    raw = raw_scenario()
    raw["juego"]["portador_recurso"] = "A1"
    scenario = build_scenario(raw)
    assert scenario.initial_state.carrier == "A1"
    assert scenario.initial_state.resource is None


def test_lowercase_sides_and_decimal_costs_are_normalized() -> None:
    raw = raw_scenario()
    raw["unidades"][0]["bando"] = "a"
    raw["turno"] = "b"
    raw["bases"] = {"a": {"fila": 0, "columna": 0}, "b": {"fila": 3, "columna": 3}}
    raw["tipos_terreno"]["pasto"]["costo"] = 1.5
    scenario = build_scenario(raw)
    assert scenario.board.unit_sides["A1"] is Side.A
    assert scenario.initial_state.turn is Side.B
    assert scenario.board.terrains["pasto"].cost == 1.5


def test_units_cannot_share_a_cell() -> None:
    raw = raw_scenario()
    raw["unidades"][1].update(fila=0, columna=1)
    assert any("shares cell" in e for e in errors_of(raw))


def test_all_errors_are_reported_together() -> None:
    raw = raw_scenario()
    raw["turno"] = "x"
    raw["terreno"][0][0] = "lava"
    raw["juego"]["portador_recurso"] = "Z9"
    assert len(errors_of(raw)) >= 3


def test_invalid_file_is_rejected_atomically(tmp_path: Path) -> None:
    raw = raw_scenario()
    raw["turno"] = "x"
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ScenarioError):
        load_scenario(bad)
    assert load_scenario(APENDICE_A).initial_state.turn is Side.A


def test_missing_file_gives_clear_error(tmp_path: Path) -> None:
    with pytest.raises(ScenarioError, match="cannot read scenario"):
        load_scenario(tmp_path / "nope.json")


def test_utility_weights_default_when_section_is_missing() -> None:
    weights = build_scenario(raw_scenario()).utility_weights
    assert weights == {"delivery": 10.0, "carry": 3.0, "goal_distance": 1.0, "rival_distance": 0.5}


def test_utility_weights_are_read_from_the_json() -> None:
    raw = raw_scenario()
    raw["utilidad"] = {"entrega": 20, "distancia_rival": 0}
    weights = build_scenario(raw).utility_weights
    assert (weights["delivery"], weights["rival_distance"], weights["carry"]) == (20.0, 0.0, 3.0)


@pytest.mark.parametrize("section", [{"entrega": -1}, {"entrega": "x"}, {"otro": 1}, [1]])
def test_invalid_utility_section_is_rejected(section: Any) -> None:
    raw = raw_scenario()
    raw["utilidad"] = section
    assert any("utilidad" in error for error in errors_of(raw))
