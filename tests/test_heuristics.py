import math

from helpers import ascii_problem
from tactical_grid.algorithms.heuristics import manhattan, min_step_cost, obstacle_aware


def test_min_step_cost_reads_cheapest_passable_terrain() -> None:
    problem = ascii_problem(["S.pG", "...X"])
    assert min_step_cost(problem.board) == 1.0


def test_manhattan_is_distance_times_min_cost() -> None:
    problem = ascii_problem(["S...G", "....X"])
    h = manhattan(problem)
    assert h(problem.initial) == 4.0


def test_both_heuristics_are_zero_at_the_goal() -> None:
    problem = ascii_problem(["SG", ".X"])
    state = next(s for s, _ in problem.expand(problem.initial) if problem.is_goal(s))
    assert manhattan(problem)(state) == 0.0
    assert obstacle_aware(problem)(state) == 0.0


def test_obstacle_aware_sees_the_wall_that_manhattan_ignores() -> None:
    # S at (0,0), G at (0,4); wall column at col 2 except row 3 -> detour of 3 down + 3 up.
    problem = ascii_problem(
        [
            "S.#.G",
            "..#..",
            "..#..",
            ".....",
            "X....",
        ]
    )
    assert manhattan(problem)(problem.initial) == 4.0
    assert obstacle_aware(problem)(problem.initial) == 10.0


def test_obstacle_aware_dominates_manhattan_on_every_reachable_cell() -> None:
    problem = ascii_problem(
        [
            "S.#.G",
            "..#..",
            "..#..",
            ".....",
            "X....",
        ]
    )
    h1, h2 = manhattan(problem), obstacle_aware(problem)
    seen = {problem.initial}
    queue = [problem.initial]
    while queue:
        state = queue.pop()
        assert h2(state) >= h1(state)
        for child, _ in problem.expand(state):
            if child not in seen:
                seen.add(child)
                queue.append(child)


def test_cells_walled_off_from_the_goal_have_infinite_estimate() -> None:
    problem = ascii_problem(["S#G", "###", "..X"])
    assert obstacle_aware(problem)(problem.initial) == math.inf
