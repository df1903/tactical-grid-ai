"""Admissible heuristics for the single-unit searches (RF-21, RF-22).

Both are scaled by the cheapest passable terrain cost read from the loaded scenario, so they
stay admissible when an external JSON brings costs below 1 (enunciado 18.4).
"""

import math
from collections import deque
from collections.abc import Callable

from tactical_grid.algorithms.common import PathProblem
from tactical_grid.domain.model import Board, GameState, Position

Heuristic = Callable[[GameState], float]


def min_step_cost(board: Board) -> float:
    """Lowest cost of entering a passable cell, read from the scenario's terrain catalog."""
    costs = [t.cost for t in board.terrains.values() if t.passable and t.cost is not None]
    return min(costs)


def manhattan(problem: PathProblem) -> Heuristic:
    """h1: Manhattan distance to the goal times the cheapest step cost.

    Purpose: estimate the remaining cost as if the map had no walls and every step cost the
        minimum; it ignores obstacles, so it loses discrimination behind barriers (case 3).
    Preconditions: the board has at least one passable terrain with a cost.
    Postconditions: admissible and consistent with 4-direction moves: each move changes the
        distance by at most 1 and costs at least `min_step_cost`. h(goal) = 0.
    Complexity: O(1) per evaluation.
    AI usage: Claude Code (Sonnet 5.5) drafted the function.
    AI intervention: none after the draft; scaling by the minimum cost follows enunciado 18.4.
    Student validation: pending cross-review by the other team member.
    """
    scale = min_step_cost(problem.board)
    goal = problem.goal

    def h(state: GameState) -> float:
        pos = state.position_of(problem.unit_id)
        return (abs(pos.row - goal.row) + abs(pos.col - goal.col)) * scale

    return h


def obstacle_aware(problem: PathProblem) -> Heuristic:
    """h2: fewest moves to the goal around walls and the rival base, times the cheapest step.

    Purpose: estimate the remaining cost using the real map layout (walls and the rival base
        cannot be crossed) but not terrain costs or other units; it dominates `manhattan`.
    Preconditions: the board has at least one passable terrain with a cost.
    Postconditions: one backward BFS from the goal at construction; cells that cannot reach
        the goal get `inf`, which is admissible because no path exists. Admissible and
        consistent: it is the exact move count of a relaxed problem times a lower bound on
        the step cost. h(goal) = 0 and h >= manhattan everywhere.
    Complexity: O(R*C) once to build, O(1) per evaluation.
    AI usage: Claude Code (Sonnet 5.5) drafted the function; the idea is the team's second
        heuristic (RF-21).
    AI intervention: none after the draft.
    Student validation: pending cross-review by the other team member.
    """
    board = problem.board
    scale = min_step_cost(board)
    rival_base = board.bases[board.unit_sides[problem.unit_id].opponent]
    moves: dict[Position, int] = {problem.goal: 0}
    queue: deque[Position] = deque([problem.goal])
    while queue:
        cell = queue.popleft()
        for nxt in cell.neighbors():
            if nxt in moves or nxt == rival_base or not board.is_passable(nxt):
                continue
            moves[nxt] = moves[cell] + 1
            queue.append(nxt)

    def h(state: GameState) -> float:
        steps = moves.get(state.position_of(problem.unit_id))
        return math.inf if steps is None else steps * scale

    return h
