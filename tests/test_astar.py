from helpers import APENDICE_A, SCENARIOS, ascii_problem, problem_from_file
from tactical_grid.algorithms.common import PathProblem
from tactical_grid.algorithms.heuristics import manhattan, obstacle_aware
from tactical_grid.algorithms.informed import a_star
from tactical_grid.algorithms.uninformed import ucs
from tactical_grid.domain.model import GameState
from tactical_grid.experiments.verifier import verify_search

MAPS = [
    ["S...G", "....X"],
    ["S.p.G", ".p.p.", "....X"],
    ["S.f..", "ff.f.", "p.p.G", "...fX"],
    ["S.#.G", "..#..", "..#..", ".....", "X...."],
    ["S#G", "###", "..X"],
]


def zero(_: GameState) -> float:
    return 0.0


def test_a_star_with_zero_heuristic_behaves_like_ucs() -> None:
    for rows in MAPS:
        problem = ascii_problem(rows)
        blind, uniform = a_star(problem, zero), ucs(problem)
        assert blind.success == uniform.success
        assert blind.cost == uniform.cost
        assert blind.path == uniform.path
        assert (blind.generated, blind.expanded) == (uniform.generated, uniform.expanded)


def test_a_star_is_optimal_with_both_heuristics() -> None:
    for rows in MAPS:
        problem = ascii_problem(rows)
        reference = ucs(problem)
        for build in (manhattan, obstacle_aware):
            result = a_star(problem, build(problem))
            assert result.success == reference.success
            assert result.cost == reference.cost
            if result.success:
                assert verify_search(problem, result).ok


def test_better_heuristic_never_expands_more() -> None:
    for rows in MAPS:
        problem = ascii_problem(rows)
        h1 = a_star(problem, manhattan(problem)).expanded
        h2 = a_star(problem, obstacle_aware(problem)).expanded
        assert h2 <= h1 <= ucs(problem).expanded


def test_a_star_reports_no_solution_when_goal_is_walled_off() -> None:
    problem = ascii_problem(["S#G", "###", "..X"])
    result = a_star(problem, manhattan(problem))
    assert not result.success
    assert result.path == ()
    assert result.length == 0


def test_a_star_start_equals_goal_has_zero_cost() -> None:
    problem = ascii_problem(["SG", ".X"])
    at_goal = PathProblem(
        problem.board, problem.initial, problem.unit_id, problem.initial.position_of("A1")
    )
    result = a_star(at_goal, manhattan(at_goal))
    assert result.success and result.cost == 0.0 and result.path == (at_goal.goal,)
    assert (result.generated, result.expanded) == (1, 0)


def test_a_star_reopens_when_heuristic_is_admissible_but_inconsistent() -> None:
    # Row of cost-1 cells with a costly shortcut: an inconsistent h must still yield the optimum.
    problem = ascii_problem(["S.fG", "....", "X..."])
    exact = ucs(problem).cost

    def lopsided(state: GameState) -> float:
        pos = state.position_of(problem.unit_id)
        return 0.0 if (pos.row + pos.col) % 2 else min(exact, 3.0)

    assert a_star(problem, lopsided).cost == exact


def test_a_star_runs_on_the_official_example_and_cases() -> None:
    for path in (
        APENDICE_A,
        SCENARIOS / "caso_01_bfs_vs_dfs.json",
        SCENARIOS / "caso_02_bfs_vs_ucs.json",
    ):
        problem = problem_from_file(path)
        reference = ucs(problem)
        result = a_star(problem, obstacle_aware(problem))
        assert result.success == reference.success
        assert result.cost == reference.cost
        assert result.expanded <= reference.expanded
