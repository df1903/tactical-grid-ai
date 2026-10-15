from dataclasses import FrozenInstanceError, replace

import pytest

from helpers import APENDICE_A
from tactical_grid.domain.model import GameState, Position, Side
from tactical_grid.scenario.loader import load_scenario


def test_case_6_same_position_different_states() -> None:
    """RF-11: a unit on the same cell is a different state if it carries the resource."""
    state = load_scenario(APENDICE_A).initial_state
    cell = state.position_of("A1")
    without = replace(state, carrier=None, resource=Position(2, 2))
    carrying = replace(state, carrier="A1", resource=None)
    assert without.position_of("A1") == carrying.position_of("A1") == cell
    assert without != carrying
    assert hash(without) != hash(carrying)


def test_turn_distinguishes_states() -> None:
    state = load_scenario(APENDICE_A).initial_state
    assert state != replace(state, turn=Side.B)


def test_state_is_immutable() -> None:
    state = load_scenario(APENDICE_A).initial_state
    with pytest.raises(FrozenInstanceError):
        state.turn = Side.B  # type: ignore[misc]


def test_equal_states_hash_equal() -> None:
    a = load_scenario(APENDICE_A).initial_state
    b = load_scenario(APENDICE_A).initial_state
    assert a == b and hash(a) == hash(b)
    assert isinstance(a, GameState)
