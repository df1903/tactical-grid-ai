"""Shared pieces of the single-unit pathfinding searches (RF-14).

The adversary is ignored: rival units are removed from the state, only the start unit
moves (its teammates stay put as obstacles), the turn does not alternate and the resource
is ignored. The rival base is still not enterable (domain rule). Legality and cost come from
`domain.rules`; this module only restricts and normalizes what the domain produces.
"""

from dataclasses import dataclass, replace

from tactical_grid.domain.model import Board, GameState, Move, Position
from tactical_grid.domain.rules import successors


@dataclass(frozen=True)
class SearchResult:
    """Outcome of one search run; fields mirror Appendix B plus time and path length."""

    algorithm: str
    success: bool
    path: tuple[Position, ...]  # cells from start to goal, start included; empty on failure
    cost: float
    generated: int
    expanded: int
    max_frontier: int
    time_seconds: float

    @property
    def length(self) -> int:
        """Number of moves of the path (0 when there is no solution)."""
        return max(len(self.path) - 1, 0)


@dataclass(frozen=True)
class PathProblem:
    """A single-unit pathfinding problem over a scenario."""

    board: Board
    initial: GameState
    unit_id: str
    goal: Position

    def is_goal(self, state: GameState) -> bool:
        return state.position_of(self.unit_id) == self.goal

    def expand(self, state: GameState) -> list[tuple[GameState, float]]:
        """Successors of `state` by moving `unit_id`, in domain order (up, down, left, right)."""
        return [
            (_normalize(nxt, self.initial), cost)
            for action, nxt, cost in successors(self.board, state)
            if isinstance(action, Move) and action.unit_id == self.unit_id
        ]


def make_problem(board: Board, initial: GameState, unit_id: str, goal: Position) -> PathProblem:
    """Build the problem: rivals removed, turn fixed to the unit's side, resource dropped."""
    side = board.unit_sides[unit_id]
    start = replace(
        initial,
        positions=tuple(
            (uid, pos) for uid, pos in initial.positions if board.unit_sides[uid] is side
        ),
        turn=side,
        turn_number=0,
        carrier=None,
        resource=None,
    )
    return PathProblem(board, start, unit_id, goal)


def _normalize(state: GameState, reference: GameState) -> GameState:
    """Undo the side effects of `apply` that are irrelevant to pathfinding."""
    return replace(
        state,
        turn=reference.turn,
        turn_number=reference.turn_number,
        carrier=None,
        resource=None,
    )


def reconstruct(
    parents: dict[GameState, GameState | None], goal: GameState, unit_id: str
) -> tuple[Position, ...]:
    """Walk parent links from `goal` back to the start and return the cells in order."""
    cells: list[Position] = []
    node: GameState | None = goal
    while node is not None:
        cells.append(node.position_of(unit_id))
        node = parents[node]
    cells.reverse()
    return tuple(cells)
