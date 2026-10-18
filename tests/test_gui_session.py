import pytest

from helpers import APENDICE_A, SCENARIOS
from tactical_grid.domain.model import Move, Position
from tactical_grid.experiments.runner import RunError, RunOptions
from tactical_grid.gui.session import Session
from tactical_grid.scenario.loader import Scenario, TestConfig, load_scenario
from test_domain_rules import make


def _session(path=APENDICE_A) -> Session:
    return Session.start(load_scenario(path))


def test_play_undo_and_reset_follow_the_rules() -> None:
    session = _session(SCENARIOS / "caso_07_decision_adversarial.json")
    first = session.state
    action = session.move_for_click("A1", Position(2, 0))
    assert isinstance(action, Move)
    session.play(action)
    assert session.state.turn_number == 1 and session.state.turn.value == "B"
    assert session.log == ["1. Bando A: A1 -> (2,0) (costo 1)"]
    assert session.undo() and session.state == first and not session.undo()
    session.play(action)
    session.reset()
    assert session.state == first and session.log == [] and session.history == []


def test_illegal_clicks_and_actions_are_rejected() -> None:
    session = _session(SCENARIOS / "caso_07_decision_adversarial.json")
    assert session.move_for_click("B1", Position(1, 3)) is None  # not B's turn
    assert session.move_for_click("A1", Position(3, 0)) is None  # two cells away
    with pytest.raises(ValueError):
        session.play(Move("A1", Position(4, 4)))


def test_search_starts_from_the_current_state() -> None:
    session = _session()
    report = session.search(RunOptions(algorithm="A_STAR", heuristic="H1"))
    assert report["exito"] is True and report["camino"][-1] == [3, 2]


def test_decide_and_play_until_the_game_ends() -> None:
    session = _session(SCENARIOS / "caso_07_decision_adversarial.json")
    for _ in range(60):
        if session.outcome():
            break
        result = session.decide("ALPHA_BETA", 2, "default")
        assert result.action is not None
        session.play(result.action)
    assert session.outcome() is not None


def test_decide_rejects_bad_options() -> None:
    session = _session()
    with pytest.raises(RunError):
        session.decide("BFS", 2, "default")
    with pytest.raises(RunError):
        session.decide("MINIMAX", 0, "default")
    with pytest.raises(RunError):
        session.decide("MINIMAX", 2, "sideways")


def test_destinations_match_legal_moves() -> None:
    session = _session(SCENARIOS / "caso_07_decision_adversarial.json")
    assert set(session.destinations("A1")) == {Position(0, 0), Position(2, 0), Position(1, 1)}
    assert session.destinations("B1") == []  # not B's turn


def test_blocked_side_passes_its_turn_automatically() -> None:
    board, state = make(
        [("A1", "A", 2, 2), ("A2", "A", 0, 1), ("A3", "A", 1, 0), ("B1", "B", 0, 0)],
        resource=(3, 3),
    )
    session = Session.start(Scenario(board, state, TestConfig(None, None, None, None)))
    action = session.move_for_click("A1", Position(2, 3))
    assert isinstance(action, Move)
    session.play(action)
    assert session.state.turn.value == "A" and session.state.turn_number == 2
    assert "sin movimientos: pasa" in session.log[-1]
    assert session.undo() and session.state == state
