"""Minimum demonstration cases 1 and 2 (enunciado section 13): expected vs. obtained.

Expected values were derived by hand from each map before running the algorithms.
"""

from helpers import SCENARIOS, problem_from_file
from tactical_grid.algorithms.uninformed import bfs, dfs, ucs
from tactical_grid.domain.model import Position
from tactical_grid.experiments.verifier import verify_search


def test_case_1_bfs_vs_dfs_explore_differently() -> None:
    # 20x20 all camino (cost 1), A1 (2,2) -> (2,6). Expected: BFS finds the 4-move straight
    # route; DFS goes "down" first and reaches the goal by a much longer path.
    problem = problem_from_file(SCENARIOS / "caso_01_bfs_vs_dfs.json")
    breadth, depth = bfs(problem), dfs(problem)

    assert breadth.success and depth.success
    assert breadth.length == 4
    assert breadth.cost == 4.0
    assert depth.length > breadth.length
    assert depth.path != breadth.path
    assert depth.expanded != breadth.expanded
    assert (breadth.generated, breadth.expanded, breadth.max_frontier) == (39, 29, 11)
    assert (depth.generated, depth.expanded, depth.max_frontier) == (152, 94, 58)
    assert verify_search(problem, breadth).ok
    assert verify_search(problem, depth).ok


def test_case_2_bfs_vs_ucs_differ_because_of_terrain_cost() -> None:
    # Pantano (7) band on cols 8-10, rows 0-9. A1 (5,5) -> (5,12). Expected: BFS crosses the
    # band: 7 moves, cost 4*1 + 3*7 = 25. UCS goes around it through row 10: 17 moves, cost 17.
    problem = problem_from_file(SCENARIOS / "caso_02_bfs_vs_ucs.json")
    short, cheap = bfs(problem), ucs(problem)

    assert short.success and cheap.success
    assert (short.length, short.cost) == (7, 25.0)
    assert (cheap.length, cheap.cost) == (17, 17.0)
    assert short.path != cheap.path
    assert Position(5, 9) in short.path
    assert all(cell.row >= 10 or cell.col not in (8, 9, 10) for cell in cheap.path)
    assert verify_search(problem, short).ok
    assert verify_search(problem, cheap).ok
