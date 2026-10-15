from helpers import APENDICE_A, ascii_problem
from tactical_grid.algorithms.common import make_problem
from tactical_grid.algorithms.uninformed import bfs
from tactical_grid.domain.model import Position
from tactical_grid.scenario.loader import load_scenario


def test_bfs_finds_fewest_moves_on_open_grid() -> None:
    problem = ascii_problem(
        [
            "S..",
            "...",
            "..G",
            "X..",
        ]
    )
    result = bfs(problem)
    assert result.success
    assert result.algorithm == "BFS"
    assert result.length == 4
    assert result.path[0] == Position(0, 0)
    assert result.path[-1] == Position(2, 2)
    assert result.cost == 4.0


def test_bfs_path_is_contiguous_and_cost_matches_terrain() -> None:
    problem = ascii_problem(
        [
            "Sp.",
            "#p.",
            "..G",
            "X..",
        ]
    )
    result = bfs(problem)
    assert result.success
    for a, b in zip(result.path, result.path[1:], strict=False):
        assert a.is_adjacent(b)
    expected = sum(problem.board.cost_at(cell) for cell in result.path[1:])
    assert result.cost == expected


def test_bfs_counts_on_corridor() -> None:
    # S . . G in a single row: 4 states, goal tested on expansion.
    problem = ascii_problem(["S..G", "####", "X###"])
    result = bfs(problem)
    assert result.success
    assert result.length == 3
    assert (result.generated, result.expanded, result.max_frontier) == (4, 3, 1)


def test_bfs_unreachable_goal() -> None:
    problem = ascii_problem(
        [
            "S#G",
            "##.",
            "X..",
        ]
    )
    result = bfs(problem)
    assert not result.success
    assert result.path == ()
    assert result.length == 0
    assert result.expanded == 1
    assert result.generated == 1


def test_bfs_goal_is_start() -> None:
    problem = ascii_problem(["SG", "X."])
    from dataclasses import replace

    result = bfs(replace(problem, goal=Position(0, 0)))
    assert result.success
    assert result.path == (Position(0, 0),)
    assert result.cost == 0.0
    assert (result.generated, result.expanded) == (1, 0)


def test_bfs_on_appendix_a() -> None:
    scenario = load_scenario(APENDICE_A)
    config = scenario.test_config
    assert config.start_unit is not None and config.goal is not None
    problem = make_problem(scenario.board, scenario.initial_state, config.start_unit, config.goal)
    result = bfs(problem)
    assert result.success
    assert result.length == 4
    assert result.path[0] == Position(0, 1)
    assert result.path[-1] == Position(3, 2)
