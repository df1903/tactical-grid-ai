from dataclasses import replace

from helpers import APENDICE_A, ascii_problem
from tactical_grid.algorithms.common import make_problem
from tactical_grid.algorithms.uninformed import bfs, ucs
from tactical_grid.domain.model import Position
from tactical_grid.scenario.loader import load_scenario


def test_ucs_prefers_cheaper_longer_route_over_short_expensive_one() -> None:
    # Direct route crosses bosque (4); the detour along the bottom is all camino (1).
    problem = ascii_problem(
        [
            "SfG",
            "...",
            "X..",
        ]
    )
    cheap = ucs(problem)
    short = bfs(problem)
    assert cheap.success and short.success
    assert short.length == 2
    assert short.cost == 5.0
    assert cheap.cost == 4.0
    assert cheap.length == 4
    assert cheap.path != short.path


def test_ucs_cost_matches_terrain_and_is_not_worse_than_bfs() -> None:
    problem = ascii_problem(
        [
            "Spp.",
            ".f#.",
            "..p.",
            "X..G",
        ]
    )
    cheap = ucs(problem)
    short = bfs(problem)
    assert cheap.cost == sum(problem.board.cost_at(c) for c in cheap.path[1:])
    assert cheap.cost <= short.cost


def test_ucs_tie_break_is_first_in_first_out() -> None:
    # Two routes of equal cost reach G: via (1,0) and via (0,1). Domain order puts "down"
    # before "right", so (1,0) enters the frontier first, is expanded first and parents G.
    problem = ascii_problem(
        [
            "S..",
            ".G.",
            "..X",
        ]
    )
    result = ucs(problem)
    assert result.cost == 2.0
    assert result.path == (Position(0, 0), Position(1, 0), Position(1, 1))


def test_ucs_unreachable_goal() -> None:
    problem = ascii_problem(
        [
            "S#G",
            "##.",
            "X..",
        ]
    )
    result = ucs(problem)
    assert not result.success
    assert result.path == ()
    assert (result.generated, result.expanded) == (1, 1)


def test_ucs_goal_is_start() -> None:
    problem = replace(ascii_problem(["SG", "X."]), goal=Position(0, 0))
    result = ucs(problem)
    assert result.success
    assert result.cost == 0.0
    assert (result.generated, result.expanded, result.max_frontier) == (1, 0, 1)


def test_ucs_on_appendix_a_finds_cheapest_path() -> None:
    scenario = load_scenario(APENDICE_A)
    config = scenario.test_config
    assert config.start_unit is not None and config.goal is not None
    problem = make_problem(scenario.board, scenario.initial_state, config.start_unit, config.goal)
    result = ucs(problem)
    assert result.success
    # (0,1) -> (3,2): through the bosque/pantano column costs 2+4+7+1; going around is cheaper.
    assert result.cost <= bfs(problem).cost
