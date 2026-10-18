from dataclasses import replace
from typing import Any

from tactical_grid.domain.model import Board, GameState, Move, Position, Side, Tackle
from tactical_grid.domain.rules import (
    apply,
    is_draw,
    is_terminal,
    legal_actions,
    skip_turn,
    successors,
    winner,
)
from tactical_grid.scenario.loader import build_scenario

Unit = tuple[str, str, int, int]


def make(
    units: list[Unit],
    resource: tuple[int, int] = (2, 2),
    carrier: str | None = None,
    turn: str = "A",
    pasto_at: tuple[int, int] | None = None,
    turn_limit: int = 100,
) -> tuple[Board, GameState]:
    grid = [["camino"] * 5 for _ in range(5)]
    if pasto_at is not None:
        grid[pasto_at[0]][pasto_at[1]] = "pasto"
    raw: dict[str, Any] = {
        "mapa": {"filas": 5, "columnas": 5},
        "tipos_terreno": {
            "camino": {"costo": 1, "transitable": True},
            "pasto": {"costo": 2, "transitable": True},
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
    return scenario.board, scenario.initial_state


def moves_of(board: Board, state: GameState, unit_id: str) -> set[Position]:
    return {
        a.dest for a in legal_actions(board, state) if isinstance(a, Move) and a.unit_id == unit_id
    }


def test_four_directions_only() -> None:
    board, state = make([("A1", "A", 2, 2), ("B1", "B", 4, 0)], resource=(0, 4))
    actions = legal_actions(board, state)
    assert moves_of(board, state, "A1") == {
        Position(1, 2),
        Position(3, 2),
        Position(2, 1),
        Position(2, 3),
    }
    assert len(actions) == 4  # only the active side acts


def test_cost_is_paid_on_entering_destination() -> None:
    board, state = make([("A1", "A", 2, 2), ("B1", "B", 4, 0)], resource=(0, 4), pasto_at=(2, 3))
    _, to_pasto = apply(board, state, Move("A1", Position(2, 3)))
    _, to_camino = apply(board, state, Move("A1", Position(2, 1)))
    assert (to_pasto, to_camino) == (2.0, 1.0)


def test_one_unit_per_cell() -> None:
    board, state = make([("A1", "A", 2, 2), ("A2", "A", 2, 3), ("B1", "B", 4, 0)], resource=(0, 4))
    assert Position(2, 3) not in moves_of(board, state, "A1")


def test_map_edges_are_respected() -> None:
    board, state = make([("A1", "A", 0, 2), ("B1", "B", 4, 0)], resource=(3, 3))
    assert Position(-1, 2) not in moves_of(board, state, "A1")


def test_rival_base_blocked_own_base_allowed() -> None:
    board, state = make([("A1", "A", 4, 3), ("A2", "A", 0, 1), ("B1", "B", 2, 0)], resource=(2, 4))
    assert Position(4, 4) not in moves_of(board, state, "A1")
    assert Position(0, 0) in moves_of(board, state, "A2")


def test_pickup_on_arrival_at_resource_cell() -> None:
    board, state = make([("A1", "A", 2, 1), ("B1", "B", 4, 0)])
    nxt, _ = apply(board, state, Move("A1", Position(2, 2)))
    assert nxt.carrier == "A1"
    assert nxt.resource is None
    assert nxt.turn is Side.B
    assert nxt.turn_number == 1


def test_delivery_wins_even_with_rival_adjacent() -> None:
    board, state = make([("A1", "A", 0, 1), ("B1", "B", 1, 0)], resource=(0, 1), carrier="A1")
    nxt, _ = apply(board, state, Move("A1", Position(0, 0)))
    assert winner(board, nxt) is Side.A
    assert nxt.carrier == "A1"
    assert legal_actions(board, nxt) == []


def test_rival_moving_next_to_carrier_does_not_drop_resource() -> None:
    board, state = make(
        [("A1", "A", 2, 2), ("B1", "B", 2, 4)], resource=(2, 2), carrier="A1", turn="B"
    )
    nxt, _ = apply(board, state, Move("B1", Position(2, 3)))
    assert nxt.carrier == "A1"
    assert nxt.resource is None


def test_carrier_walking_next_to_a_rival_keeps_the_resource() -> None:
    board, state = make(
        [("A1", "A", 2, 2), ("B1", "B", 2, 4)], resource=(2, 2), carrier="A1", turn="A"
    )
    nxt, _ = apply(board, state, Move("A1", Position(2, 3)))
    assert nxt.carrier == "A1"


def test_tackle_is_legal_only_for_own_units_adjacent_to_the_rival_carrier() -> None:
    board, state = make(
        [("A1", "A", 2, 2), ("B1", "B", 2, 3), ("B2", "B", 4, 0)],
        resource=(2, 2),
        carrier="A1",
        turn="B",
    )
    tackles = [a for a in legal_actions(board, state) if isinstance(a, Tackle)]
    assert tackles == [Tackle("B1", "A1")]


def test_no_tackle_when_nobody_is_adjacent_or_the_carrier_is_own_side() -> None:
    far, far_state = make(
        [("A1", "A", 2, 2), ("B1", "B", 2, 4)], resource=(2, 2), carrier="A1", turn="B"
    )
    assert not any(isinstance(a, Tackle) for a in legal_actions(far, far_state))
    own, own_state = make(
        [("A1", "A", 2, 2), ("A2", "A", 2, 3), ("B1", "B", 4, 0)],
        resource=(2, 2),
        carrier="A1",
        turn="A",
    )
    assert not any(isinstance(a, Tackle) for a in legal_actions(own, own_state))
    no_carrier, free_state = make([("A1", "A", 2, 2), ("B1", "B", 2, 3)], turn="B")
    assert not any(isinstance(a, Tackle) for a in legal_actions(no_carrier, free_state))


def test_tackle_drops_the_resource_on_the_carrier_cell_without_moving_anyone() -> None:
    board, state = make(
        [("A1", "A", 2, 2), ("B1", "B", 2, 3)], resource=(2, 2), carrier="A1", turn="B"
    )
    nxt, cost = apply(board, state, Tackle("B1", "A1"))
    assert nxt.carrier is None
    assert nxt.resource == Position(2, 2)
    assert nxt.positions == state.positions
    assert nxt.turn is Side.A
    assert nxt.turn_number == state.turn_number + 1
    assert cost == 0.0


def test_no_transfer_to_the_tackler() -> None:
    board, state = make(
        [("A1", "A", 2, 2), ("B1", "B", 2, 3)], resource=(2, 2), carrier="A1", turn="B"
    )
    nxt, _ = apply(board, state, Tackle("B1", "A1"))
    assert nxt.carrier != "B1"


def test_carrier_can_run_away_before_it_is_tackled() -> None:
    board, state = make(
        [("A1", "A", 2, 2), ("B1", "B", 2, 4)], resource=(2, 2), carrier="A1", turn="B"
    )
    threatened, _ = apply(board, state, Move("B1", Position(2, 3)))
    fled, _ = apply(board, threatened, Move("A1", Position(1, 2)))
    assert fled.carrier == "A1"
    assert not any(isinstance(a, Tackle) for a in legal_actions(board, fled))


def test_other_unit_moving_does_not_repick_resource_under_the_dropper() -> None:
    board, state = make(
        [("A1", "A", 2, 2), ("A2", "A", 0, 3), ("B1", "B", 2, 3)],
        resource=(2, 2),
        carrier="A1",
        turn="B",
    )
    dropped, _ = apply(board, state, Tackle("B1", "A1"))
    after_other, _ = apply(board, dropped, Move("A2", Position(0, 2)))
    assert after_other.carrier is None
    assert after_other.resource == Position(2, 2)


def test_blocked_side_has_no_actions_and_skip_turn_passes() -> None:
    board, state = make([("A1", "A", 0, 0), ("B1", "B", 0, 1), ("B2", "B", 1, 0)], resource=(3, 3))
    assert not is_terminal(board, state)
    assert legal_actions(board, state) == []
    after = skip_turn(state)
    assert after.turn is Side.B
    assert after.turn_number == state.turn_number + 1
    assert after.positions == state.positions


def test_leaving_and_returning_picks_up_again() -> None:
    board, state = make(
        [("A1", "A", 2, 2), ("B1", "B", 2, 3)], resource=(2, 2), carrier="A1", turn="B"
    )
    dropped, _ = apply(board, state, Tackle("B1", "A1"))
    away, _ = apply(board, dropped, Move("A1", Position(2, 1)))
    assert away.carrier is None
    # the tackler stays next to the cell, but nothing is automatic: the return picks up
    b_waits, _ = apply(board, away, Move("B1", Position(1, 3)))
    back, _ = apply(board, b_waits, Move("A1", Position(2, 2)))
    assert back.carrier == "A1"
    assert back.resource is None


def test_turn_limit_is_a_draw() -> None:
    board, state = make([("A1", "A", 2, 1), ("B1", "B", 4, 0)], turn_limit=3)
    late = replace(state, turn_number=3)
    assert is_terminal(board, late)
    assert is_draw(board, late)
    assert winner(board, late) is None
    assert legal_actions(board, late) == []


def test_successors_are_deterministic_and_consistent() -> None:
    board, state = make([("A1", "A", 2, 1), ("B1", "B", 4, 0)])
    first = successors(board, state)
    second = successors(board, state)
    assert first == second
    assert [a for a, _, _ in first] == legal_actions(board, state)
    assert all(s.turn is Side.B for _, s, _ in first)
