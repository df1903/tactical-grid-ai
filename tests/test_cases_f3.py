"""Minimum demonstration cases 3, 4 and 5 (enunciado section 13): expected vs. obtained.

Expected values were derived by hand from each map before running the algorithms; the
metrics are the deterministic ones (everything except time).
"""

from helpers import SCENARIOS, problem_from_file
from tactical_grid.algorithms.heuristics import manhattan, obstacle_aware
from tactical_grid.algorithms.informed import a_star, beam_search
from tactical_grid.algorithms.uninformed import ucs
from tactical_grid.domain.model import Position
from tactical_grid.experiments.verifier import verify_search


def test_case_3_barrier_makes_manhattan_expand_more_than_obstacle_aware() -> None:
    # 20x20 camino with a wall on col 8, rows 0-15. A1 (5,5) -> (5,12): the goal is 7 cells
    # away but the only way is around the wall's bottom end (row 16): 11 down + 7 right +
    # 11 up = 29 moves, cost 29. Both heuristics stay optimal; h1 is fooled by the wall.
    problem = problem_from_file(SCENARIOS / "caso_03_obstaculo_heuristica.json")
    uniform = ucs(problem)
    h1 = a_star(problem, manhattan(problem), "A_STAR_H1")
    h2 = a_star(problem, obstacle_aware(problem), "A_STAR_H2")

    for result in (uniform, h1, h2):
        assert result.success
        assert (result.length, result.cost) == (29, 29.0)
        assert verify_search(problem, result).ok
    assert all(cell.col != 8 or cell.row >= 16 for cell in h2.path)
    assert (h1.generated, h1.expanded, h1.max_frontier) == (194, 166, 28)
    assert (h2.generated, h2.expanded, h2.max_frontier) == (122, 84, 38)
    assert h2.expanded < h1.expanded < uniform.expanded
    assert Position(16, 8) in h2.path


def test_case_4_same_scenario_two_heuristics_same_cost_different_effort() -> None:
    # Wall on col 9, rows 3-16; the top gap (rows 0-2) is swamp (cost 3), the bottom gap is
    # open ground. A1 (9,5) -> (9,13). Expected: optimal cost 24 over 22 moves for UCS and
    # for A* with either heuristic; h2 expands fewer states because it sees the wall, but it
    # cannot see the swamp, so it still explores more than a perfect heuristic would.
    problem = problem_from_file(SCENARIOS / "caso_04_comparacion_heuristicas.json")
    uniform = ucs(problem)
    h1 = a_star(problem, manhattan(problem), "A_STAR_H1")
    h2 = a_star(problem, obstacle_aware(problem), "A_STAR_H2")

    for result in (uniform, h1, h2):
        assert result.success
        assert (result.length, result.cost) == (22, 24.0)
        assert verify_search(problem, result).ok
    assert (h1.generated, h1.expanded, h1.max_frontier) == (230, 186, 44)
    assert (h2.generated, h2.expanded, h2.max_frontier) == (164, 115, 49)
    assert h2.expanded < h1.expanded < uniform.expanded


def test_case_5_beam_width_changes_exploration_and_solution() -> None:
    # 7x9 map with pasto (2) and bosque (4); A1 (0,0) -> (6,8). Optimal cost is 28 over 14
    # moves. Expected: k=1 prunes the only promising branch and fails; k=2 survives but keeps
    # a worse route (cost 30, 16 moves, so pruning discarded a better path); k=4 and k=8
    # recover the optimum.
    problem = problem_from_file(SCENARIOS / "caso_05_beam_k.json")
    h = manhattan(problem)
    optimum = ucs(problem)
    runs = {k: beam_search(problem, h, k) for k in (1, 2, 4, 8)}

    assert (optimum.length, optimum.cost) == (14, 28.0)
    assert not runs[1].success and runs[1].path == ()
    assert (runs[2].success, runs[2].length, runs[2].cost) == (True, 16, 30.0)
    for k in (4, 8):
        assert (runs[k].success, runs[k].length, runs[k].cost) == (True, 14, 28.0)
    assert [(r.generated, r.expanded, r.max_frontier) for r in runs.values()] == [
        (9, 5, 3),
        (43, 29, 6),
        (50, 41, 6),
        (46, 44, 6),
    ]
    assert runs[2].cost > optimum.cost
    for k in (2, 4, 8):
        assert verify_search(problem, runs[k]).ok
