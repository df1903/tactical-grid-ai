import pytest

from helpers import ascii_problem
from tactical_grid.algorithms.heuristics import manhattan
from tactical_grid.algorithms.informed import beam_search
from tactical_grid.algorithms.uninformed import bfs
from tactical_grid.experiments.verifier import verify_search


def test_beam_rejects_a_width_below_one() -> None:
    problem = ascii_problem(["SG", ".X"])
    with pytest.raises(ValueError, match="at least 1"):
        beam_search(problem, manhattan(problem), 0)


def test_beam_with_unbounded_width_finds_the_fewest_moves() -> None:
    problem = ascii_problem(["S.#.G", "..#..", "..#..", ".....", "X...."])
    wide = beam_search(problem, manhattan(problem), 10_000)
    assert wide.success
    assert wide.length == bfs(problem).length
    assert verify_search(problem, wide).ok


def test_beam_keeps_at_most_k_states_per_level() -> None:
    problem = ascii_problem(["S.....", "......", "......", "......", ".....G", "X....."])
    for k in (1, 2, 4):
        result = beam_search(problem, manhattan(problem), k)
        assert result.success
        # candidates before pruning are at most k parents times 4 children
        assert result.max_frontier <= 4 * k


def test_beam_fails_when_the_goal_is_unreachable() -> None:
    problem = ascii_problem(["S#G", "###", "..X"])
    result = beam_search(problem, manhattan(problem), 4)
    assert not result.success and result.path == () and result.cost == 0.0


def test_beam_is_deterministic() -> None:
    problem = ascii_problem(["S.p.G", ".p.p.", "....X"])
    first = beam_search(problem, manhattan(problem), 2)
    second = beam_search(problem, manhattan(problem), 2)
    assert (first.path, first.cost, first.generated, first.expanded) == (
        second.path,
        second.cost,
        second.generated,
        second.expanded,
    )


def test_beam_start_equals_goal_is_found_immediately() -> None:
    problem = ascii_problem(["SG", ".X"])
    at_goal = type(problem)(
        problem.board, problem.initial, problem.unit_id, problem.initial.position_of("A1")
    )
    result = beam_search(at_goal, manhattan(at_goal), 1)
    assert result.success and result.cost == 0.0
    assert (result.generated, result.expanded) == (1, 0)
