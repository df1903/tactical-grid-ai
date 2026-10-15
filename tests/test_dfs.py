from dataclasses import replace

from helpers import APENDICE_A, ascii_problem
from tactical_grid.algorithms.common import make_problem
from tactical_grid.algorithms.uninformed import bfs, dfs
from tactical_grid.domain.model import Position
from tactical_grid.scenario.loader import load_scenario


def test_dfs_finds_a_valid_path() -> None:
    problem = ascii_problem(
        [
            "S..",
            "...",
            "..G",
            "X..",
        ]
    )
    result = dfs(problem)
    assert result.success
    assert result.algorithm == "DFS"
    assert result.path[0] == Position(0, 0)
    assert result.path[-1] == Position(2, 2)
    for a, b in zip(result.path, result.path[1:], strict=False):
        assert a.is_adjacent(b)
    assert result.cost == sum(problem.board.cost_at(c) for c in result.path[1:])


def test_dfs_goes_deep_first_and_differs_from_bfs() -> None:
    # Order is up, down, left, right: DFS leaves S going down and reaches G by a detour.
    problem = ascii_problem(
        [
            "S.G",
            "...",
            "...",
            "X..",
        ]
    )
    deep = dfs(problem)
    shallow = bfs(problem)
    assert shallow.length == 2
    assert deep.length > shallow.length
    assert deep.path[1] == Position(1, 0)


def test_dfs_unreachable_goal() -> None:
    problem = ascii_problem(
        [
            "S#G",
            "##.",
            "X..",
        ]
    )
    result = dfs(problem)
    assert not result.success
    assert result.path == ()
    assert (result.generated, result.expanded) == (1, 1)


def test_dfs_goal_is_start() -> None:
    problem = replace(ascii_problem(["SG", "X."]), goal=Position(0, 0))
    result = dfs(problem)
    assert result.success
    assert result.path == (Position(0, 0),)
    assert (result.generated, result.expanded, result.max_frontier) == (1, 0, 1)


def test_dfs_on_appendix_a() -> None:
    scenario = load_scenario(APENDICE_A)
    config = scenario.test_config
    assert config.start_unit is not None and config.goal is not None
    problem = make_problem(scenario.board, scenario.initial_state, config.start_unit, config.goal)
    result = dfs(problem)
    assert result.success
    assert result.path[0] == Position(0, 1)
    assert result.path[-1] == Position(3, 2)
