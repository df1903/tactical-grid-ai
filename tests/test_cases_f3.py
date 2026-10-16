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
