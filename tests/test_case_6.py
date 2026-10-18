"""Minimum demonstration case 6 (enunciado section 13): composite state.

The same physical situation (unit A1 on the same cell) is a different state when the
additional game information differs, and the difference changes what the rules produce.
"""

from dataclasses import replace

from helpers import mini_race
from tactical_grid.domain.model import Move, Position, Side
from tactical_grid.domain.rules import apply, legal_actions, winner


def test_case_6_same_cell_different_states_different_consequences() -> None:
    # A1 stands at (1,0), next to its base (0,0). Initial state: nobody carries the resource.
    scenario = mini_race()
    board, free = scenario.board, scenario.initial_state
    carrying = replace(free, carrier="A1", resource=None)
    rival_turn = replace(free, turn=Side.B)
    enter_base = Move("A1", Position(0, 0))

    # Same unit on the same cell in every variant, yet they are four different states.
    states = [free, carrying, rival_turn]
    assert {state.position_of("A1") for state in states} == {Position(1, 0)}
    assert len(set(states)) == 3
    assert free.positions == carrying.positions == rival_turn.positions

    # Same action, different outcome: only the carrier delivers (and wins) by entering the base.
    after_free, _ = apply(board, free, enter_base)
    after_carrying, _ = apply(board, carrying, enter_base)
    assert winner(board, after_free) is None
    assert winner(board, after_carrying) is Side.A
    assert after_carrying.carrier == "A1" and after_free.carrier is None

    # The turn also matters: A1 has no legal action when it is B's turn.
    assert enter_base in legal_actions(board, free)
    assert all(
        not isinstance(action, Move) or action.unit_id != "A1"
        for action in legal_actions(board, rival_turn)
    )

    # A search keyed by state keeps them apart; keyed by position alone it would merge them.
    visited = {free: "free", carrying: "carrying", rival_turn: "rival turn"}
    assert len(visited) == 3 and len({s.position_of("A1") for s in visited}) == 1
