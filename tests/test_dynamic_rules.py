from dataclasses import replace
from typing import Any

import pytest

from tactical_grid.domain.dynamic import (
    DynamicRules,
    DynamicState,
    apply,
    initial_dynamic_state,
    is_terminal,
    legal_actions,
    pass_turn,
    recovery_turns,
)
from tactical_grid.domain.model import Board, Move, Position, Side, Tackle
from tactical_grid.domain.rules import winner
from tactical_grid.scenario.loader import DEFAULT_DYNAMIC_RULES, build_scenario

Unit = tuple[str, str, int, int]
RULES = DynamicRules(tackle_penalty=2, steal_immunity=1)
# nombres de terreno de prueba -> costo; los costos 3 y 7 son los de los escenarios del proyecto
TERRAINS = {"camino": 1, "pasto": 2, "pantano": 3, "bosque": 4, "cienaga": 7, "pradera": 1.5}


def make(
    units: list[Unit],
    resource: tuple[int, int] = (2, 2),
    carrier: str | None = None,
    turn: str = "A",
    special: dict[tuple[int, int], str] | None = None,
    turn_limit: int = 100,
) -> tuple[Board, DynamicState]:
    grid = [["camino"] * 5 for _ in range(5)]
    for (r, c), name in (special or {}).items():
        grid[r][c] = name
    raw: dict[str, Any] = {
        "mapa": {"filas": 5, "columnas": 5},
        "tipos_terreno": {
            name: {"costo": cost, "transitable": True} for name, cost in TERRAINS.items()
        },
        "terreno": grid,
        "bases": {"A": {"fila": 0, "columna": 0}, "B": {"fila": 4, "columna": 4}},
        "recurso": {"fila": resource[0], "columna": resource[1]},
        "unidades": [
            {"id": uid, "bando": side, "tipo": "estandar", "fila": r, "columna": c}
            for uid, side, r, c in units
        ],
        "turno": turn,
        "juego": {"portador_recurso": carrier, "limite_turnos": turn_limit},
    }
    scenario = build_scenario(raw)
    return scenario.board, initial_dynamic_state(scenario.initial_state)


def with_recovery(state: DynamicState, **turns: int) -> DynamicState:
    return replace(state, recovery=tuple((uid, turns.get(uid, t)) for uid, t in state.recovery))


def movers(board: Board, state: DynamicState) -> set[str]:
    return {a.unit_id for a in legal_actions(board, state) if isinstance(a, Move)}


@pytest.mark.parametrize(
    ("terrain", "expected"),
    [("camino", 0), ("pasto", 1), ("pantano", 2), ("bosque", 3), ("cienaga", 6), ("pradera", 1)],
)
def test_recovery_turns_come_from_the_terrain_cost(terrain: str, expected: int) -> None:
    board, _ = make([("A1", "A", 2, 2), ("B1", "B", 4, 0)], special={(1, 2): terrain})
    assert recovery_turns(board, Position(1, 2)) == expected


def test_default_parameters_are_read_by_the_loader() -> None:
    assert DEFAULT_DYNAMIC_RULES == DynamicRules(tackle_penalty=2, steal_immunity=1)


def first_move(board: Board, state: DynamicState, unit_id: str) -> Move:
    return next(
        a for a in legal_actions(board, state) if isinstance(a, Move) and a.unit_id == unit_id
    )


def test_a_unit_in_a_swamp_waits_two_own_turns_and_moves_on_the_third() -> None:
    units: list[Unit] = [("A1", "A", 2, 2), ("A2", "A", 3, 0), ("B1", "B", 4, 3), ("B2", "B", 0, 4)]
    board, state = make(units, resource=(0, 3), special={(1, 2): "pantano"})
    state = apply(board, state, Move("A1", Position(1, 2)), RULES)
    assert state.recovery_of("A1") == 2
    for expected in (1, 0):
        state = apply(board, state, first_move(board, state, "B2"), RULES)
        assert "A1" not in movers(board, state)
        state = apply(board, state, first_move(board, state, "A2"), RULES)
        assert state.recovery_of("A1") == expected
    state = apply(board, state, first_move(board, state, "B2"), RULES)
    assert "A1" in movers(board, state)


def test_cost_seven_example_waits_six_own_turns() -> None:
    units: list[Unit] = [("A1", "A", 2, 2), ("A2", "A", 3, 0), ("B1", "B", 4, 3), ("B2", "B", 0, 4)]
    board, state = make(units, resource=(0, 3), special={(1, 2): "cienaga"})
    state = apply(board, state, Move("A1", Position(1, 2)), RULES)
    assert state.recovery_of("A1") == 6
    state = pass_turn(board, state)  # B pasa: no toca los contadores de A
    assert state.recovery_of("A1") == 6


def test_rival_counters_do_not_drop_on_my_turn() -> None:
    board, state = make(
        [("A1", "A", 2, 2), ("A2", "A", 3, 0), ("B1", "B", 4, 3), ("B2", "B", 0, 4)]
    )
    state = with_recovery(state, B1=3)
    state = apply(board, state, Move("A1", Position(2, 1)), RULES)
    assert state.recovery_of("B1") == 3


def test_a_blocked_side_passes_and_its_counters_drop() -> None:
    board, state = make(
        [("A1", "A", 2, 2), ("A2", "A", 3, 0), ("B1", "B", 4, 3), ("B2", "B", 0, 4)]
    )
    state = with_recovery(state, A1=2, A2=1)
    assert legal_actions(board, state) == []
    assert not is_terminal(board, state)
    passed = pass_turn(board, state)
    assert passed.turn is Side.B
    assert passed.base.turn_number == state.base.turn_number + 1
    assert (passed.recovery_of("A1"), passed.recovery_of("A2")) == (1, 0)


def test_equal_positions_with_different_counters_are_different_states() -> None:
    _, state = make([("A1", "A", 2, 2), ("B1", "B", 4, 3)])
    other = with_recovery(state, A1=1)
    assert state != other
    assert len({state, other}) == 2


STEAL: list[Unit] = [
    ("A1", "A", 2, 2),
    ("A2", "A", 1, 3),
    ("A3", "A", 0, 1),
    ("B1", "B", 2, 3),
    ("B2", "B", 4, 0),
]


def test_an_adjacent_free_unit_steals_the_resource_and_the_victim_is_penalized() -> None:
    board, state = make(STEAL, carrier="A1", turn="B")
    tackle = Tackle("B1", "A1")
    assert tackle in legal_actions(board, state)
    after = apply(board, state, tackle, RULES)
    assert after.base.carrier == "B1" and after.base.resource is None
    assert after.base.positions == state.base.positions
    assert after.recovery_of("A1") == 2
    assert after.recovery_of("B1") == 0
    assert after.immunity == 1
    assert after.turn is Side.A


def test_a_unit_in_recovery_cannot_tackle_but_a_carrier_in_recovery_can_be_tackled() -> None:
    board, state = make(STEAL, carrier="A1", turn="B")
    assert Tackle("B1", "A1") not in legal_actions(board, with_recovery(state, B1=1))
    assert Tackle("B1", "A1") in legal_actions(board, with_recovery(state, A1=5))


@pytest.mark.parametrize(("current", "expected"), [(0, 2), (1, 2), (2, 2), (5, 5)])
def test_the_penalty_is_the_maximum_not_the_sum(current: int, expected: int) -> None:
    board, state = make(STEAL, carrier="A1", turn="B")
    after = apply(board, with_recovery(state, A1=current), Tackle("B1", "A1"), RULES)
    assert after.recovery_of("A1") == expected


def test_the_new_carrier_is_immune_for_one_rival_turn() -> None:
    board, state = make(STEAL, carrier="A1", turn="B")
    state = apply(board, state, Tackle("B1", "A1"), RULES)
    # A2 está pegado a B1 pero no puede robar en el primer turno de A
    assert Position(1, 3).is_adjacent(state.base.position_of("B1"))
    assert not any(isinstance(a, Tackle) for a in legal_actions(board, state))
    state = apply(board, state, Move("A3", Position(0, 2)), RULES)
    state = apply(board, state, Move("B2", Position(3, 0)), RULES)
    assert state.immunity == 0
    assert Tackle("A2", "B1") in legal_actions(board, state)


def test_without_immunity_the_steal_back_is_immediate() -> None:
    board, state = make(STEAL, carrier="A1", turn="B")
    state = apply(board, state, Tackle("B1", "A1"), DynamicRules(2, 0))
    assert Tackle("A2", "B1") in legal_actions(board, state)


def test_the_stolen_resource_is_not_left_on_the_floor() -> None:
    board, state = make(STEAL, carrier="A1", turn="B")
    after = apply(board, state, Tackle("B1", "A1"), RULES)
    assert after.base.resource is None
    assert after.base.carrier is not None


def test_stealing_on_the_own_base_wins_at_once() -> None:
    board, state = make(
        [("A1", "A", 4, 3), ("B1", "B", 4, 4), ("A2", "A", 0, 1)], carrier="A1", turn="B"
    )
    after = apply(board, state, Tackle("B1", "A1"), RULES)
    assert winner(board, after.base) is Side.B
    assert is_terminal(board, after)
    assert legal_actions(board, after) == []


def test_stealing_on_the_own_base_wins_for_a_too() -> None:
    board, state = make(
        [("B1", "B", 0, 1), ("A1", "A", 0, 0), ("B2", "B", 4, 3)], carrier="B1", turn="A"
    )
    after = apply(board, state, Tackle("A1", "B1"), RULES)
    assert winner(board, after.base) is Side.A


def test_moving_the_carrier_into_swamp_leaves_it_exposed() -> None:
    units: list[Unit] = [("A1", "A", 2, 2), ("A2", "A", 0, 1), ("B1", "B", 2, 4), ("B2", "B", 4, 0)]
    board, state = make(units, carrier="A1", special={(2, 3): "pantano"})
    state = apply(board, state, Move("A1", Position(2, 3)), RULES)
    assert state.recovery_of("A1") == 2
    assert Tackle("B1", "A1") in legal_actions(board, state)
