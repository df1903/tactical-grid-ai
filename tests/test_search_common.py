from dataclasses import replace

from helpers import APENDICE_A, ascii_problem
from tactical_grid.algorithms.common import make_problem
from tactical_grid.domain.model import Position, Side
from tactical_grid.scenario.loader import load_scenario


def test_problem_uses_scenario_test_config() -> None:
    scenario = load_scenario(APENDICE_A)
    config = scenario.test_config
    assert config.start_unit is not None and config.goal is not None
    problem = make_problem(scenario.board, scenario.initial_state, config.start_unit, config.goal)
    assert problem.unit_id == "A1"
    assert problem.goal == Position(3, 2)
    assert problem.initial.turn is Side.A
    assert problem.initial.turn_number == 0


def test_expand_moves_only_the_start_unit_in_domain_order() -> None:
    problem = ascii_problem(
        [
            ".....",
            ".....",
            "..S..",
            ".....",
            "...XG",
        ]
    )
    cells = [state.position_of("A1") for state, _ in problem.expand(problem.initial)]
    assert cells == [Position(1, 2), Position(3, 2), Position(2, 1), Position(2, 3)]
    for state, _ in problem.expand(problem.initial):
        assert state.position_of("B1") == Position(4, 3)
        assert state.turn is problem.initial.turn
        assert state.turn_number == 0


def test_expand_ignores_resource_pickup() -> None:
    problem = ascii_problem(
        [
            "SG.",
            "..X",
        ]
    )
    (state, _), *_ = [
        (s, c) for s, c in problem.expand(problem.initial) if s.position_of("A1") == Position(0, 1)
    ]
    assert state.carrier is None
    assert state.resource is None


def test_expand_respects_walls_and_rival_base() -> None:
    problem = ascii_problem(
        [
            "S#G",
            ".X.",
        ]
    )
    cells = {state.position_of("A1") for state, _ in problem.expand(problem.initial)}
    assert cells == {Position(1, 0)}


def test_is_goal() -> None:
    problem = ascii_problem(["SG", "X."])
    assert not problem.is_goal(problem.initial)
    nxt = next(s for s, _ in problem.expand(problem.initial) if s.position_of("A1") == problem.goal)
    assert problem.is_goal(nxt)
    assert replace(problem, goal=Position(0, 0)).is_goal(problem.initial)
