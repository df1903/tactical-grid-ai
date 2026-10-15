"""Solution verifier for single-unit searches (RF-42, checks 1 to 5).

Check 6 (Minimax only considers legal actions) belongs to the adversarial phase.
"""

import math
from dataclasses import dataclass

from tactical_grid.algorithms.common import PathProblem, SearchResult
from tactical_grid.domain.model import GameState, Position


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class VerificationReport:
    algorithm: str
    checks: tuple[Check, ...]

    @property
    def ok(self) -> bool:
        return all(check.passed for check in self.checks)


def verify_search(problem: PathProblem, result: SearchResult) -> VerificationReport:
    """Replay the reported path on the domain rules and run RF-42 checks 1 to 5.

    Purpose: independent check that a search result is a legal, consistent solution.
    Preconditions: `problem` is the one the algorithm solved.
    Postconditions: never raises on a malformed path; each check reports why it failed.
        A result without solution has no path to verify and yields an empty report.
    Complexity: O(L * U) for a path of L cells and U units.
    AI usage: Claude Code (Sonnet 5.5) drafted the function from RF-42.
    AI intervention: none after the draft.
    Student validation: pending cross-review by the other team member.
    """
    if not result.success:
        return VerificationReport(result.algorithm, ())

    board = problem.board
    start = problem.initial.position_of(problem.unit_id)
    path = result.path

    states: list[GameState] = [problem.initial]
    replay_cost = 0.0
    bad_move: str | None = None
    if not path or path[0] != start:
        bad_move = f"path does not start at the unit's cell {start}"
    else:
        for step, cell in enumerate(path[1:], start=1):
            match = [
                (nxt, cost)
                for nxt, cost in problem.expand(states[-1])
                if nxt.position_of(problem.unit_id) == cell
            ]
            if not match:
                bad_move = f"step {step}: {states[-1].position_of(problem.unit_id)} -> {cell}"
                break
            states.append(match[0][0])
            replay_cost += match[0][1]

    walls = [cell for cell in path if not board.is_passable(cell)]
    invalid = [i for i, state in enumerate(states) if not _valid_state(problem, state)]
    reported = result.cost
    final = path[-1] if path else None

    checks = (
        Check(
            "valid moves",
            bad_move is None,
            "every step is a legal action" if bad_move is None else f"illegal move at {bad_move}",
        ),
        Check(
            "no obstacles",
            not walls,
            "no cell is blocked" if not walls else f"blocked cells in path: {walls}",
        ),
        Check(
            "cost matches",
            bad_move is None and math.isclose(replay_cost, reported),
            f"reported {reported}, replayed {replay_cost}",
        ),
        Check(
            "goal reached",
            final == problem.goal,
            f"final cell {final}, goal {problem.goal}",
        ),
        Check(
            "no invalid states",
            not invalid,
            "all replayed states are valid"
            if not invalid
            else f"invalid states at steps {invalid}",
        ),
    )
    return VerificationReport(result.algorithm, checks)


def _valid_state(problem: PathProblem, state: GameState) -> bool:
    cells: list[Position] = [pos for _, pos in state.positions]
    if len(set(cells)) != len(cells):
        return False
    return all(problem.board.is_passable(cell) for cell in cells)
