from dataclasses import replace

from helpers import ascii_problem
from tactical_grid.algorithms.uninformed import bfs, dfs, ucs
from tactical_grid.domain.model import Position
from tactical_grid.experiments.verifier import verify_search

MAP = [
    "S.p.",
    ".#f.",
    "...G",
    "X...",
]


def test_every_algorithm_result_passes_verification() -> None:
    problem = ascii_problem(MAP)
    for algorithm in (bfs, dfs, ucs):
        report = verify_search(problem, algorithm(problem))
        assert report.ok, report
        assert len(report.checks) == 5


def test_failed_search_has_nothing_to_verify() -> None:
    problem = ascii_problem(["S#G", "##.", "X.."])
    report = verify_search(problem, bfs(problem))
    assert report.checks == ()
    assert report.ok


def _failed_names(problem_map: list[str], tamper: dict[str, object]) -> set[str]:
    problem = ascii_problem(problem_map)
    result = replace(bfs(problem), **tamper)  # type: ignore[arg-type]
    report = verify_search(problem, result)
    return {check.name for check in report.checks if not check.passed}


def test_teleport_is_an_invalid_move() -> None:
    path = (Position(0, 0), Position(2, 0), Position(2, 3))
    assert "valid moves" in _failed_names(MAP, {"path": path})


def test_path_through_wall_is_rejected() -> None:
    path = (Position(0, 0), Position(0, 1), Position(1, 1), Position(2, 1))
    failed = _failed_names(MAP, {"path": path})
    assert "no obstacles" in failed
    assert "valid moves" in failed


def test_wrong_cost_is_rejected() -> None:
    problem = ascii_problem(MAP)
    honest = bfs(problem)
    assert "cost matches" in _failed_names(MAP, {"cost": honest.cost + 1})


def test_path_not_ending_at_goal_is_rejected() -> None:
    problem = ascii_problem(MAP)
    short = bfs(problem).path[:-1]
    failed = _failed_names(MAP, {"path": short})
    assert "goal reached" in failed
