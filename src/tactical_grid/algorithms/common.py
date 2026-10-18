"""Shared pieces of the single-unit pathfinding searches (RF-14).

The adversary is ignored: rival units are removed from the state, only the start unit
moves (its teammates stay put as obstacles), the turn does not alternate and the resource
is ignored. The rival base is still not enterable (domain rule). Legality and cost come from
`domain.rules`; this module only restricts and normalizes what the domain produces.
"""

import time
from dataclasses import dataclass, replace

from tactical_grid.domain.model import Board, GameState, Move, Position
from tactical_grid.domain.rules import successors


# Resultado de una búsqueda de camino para una unidad en un escenario
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

    # Cantidad de movimientos del camino (celdas menos la de inicio)
    @property
    def length(self) -> int:
        """Number of moves of the path (0 when there is no solution)."""
        return max(len(self.path) - 1, 0)


# Representa un problema de búsqueda de camino para una unidad en un escenario
@dataclass(frozen=True)
class PathProblem:
    """A single-unit pathfinding problem over a scenario."""

    board: Board
    initial: GameState
    unit_id: str
    goal: Position

    # Prueba de meta: la unidad está en la celda objetivo
    def is_goal(self, state: GameState) -> bool:
        return state.position_of(self.unit_id) == self.goal

    # Sucesores del estado: solo los movimientos de la unidad que se busca mover
    def expand(self, state: GameState) -> list[tuple[GameState, float]]:
        """Successors of `state` by moving `unit_id`, in domain order (up, down, left, right)."""
        return [
            (_normalize(nxt, self.initial), cost)
            for action, nxt, cost in successors(self.board, state)
            if isinstance(action, Move) and action.unit_id == self.unit_id
        ]


# Construye el problema de búsqueda de camino para una unidad en un escenario
def make_problem(board: Board, initial: GameState, unit_id: str, goal: Position) -> PathProblem:
    """Build the problem: rivals removed, turn fixed to the unit's side, resource dropped."""
    side = board.unit_sides[unit_id]
    # estado inicial: solo quedan las unidades del propio bando, sin turnos ni recurso
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


# Normaliza un estado de juego para ignorar efectos irrelevantes para la búsqueda de camino
def _normalize(state: GameState, reference: GameState) -> GameState:
    """Undo the side effects of `apply` that are irrelevant to pathfinding."""
    return replace(
        state,
        turn=reference.turn,
        turn_number=reference.turn_number,
        carrier=None,
        resource=None,
    )


# Reconstruye el camino desde el estado objetivo hasta el estado inicial usando los padres
def reconstruct(
    parents: dict[GameState, GameState | None], goal: GameState, unit_id: str
) -> tuple[Position, ...]:
    """Walk parent links from `goal` back to the start and return the cells in order."""
    cells: list[Position] = []
    node: GameState | None = goal
    # se sube por los padres hasta llegar al inicio (que no tiene padre)
    while node is not None:
        cells.append(node.position_of(unit_id))
        node = parents[node]
    # el camino quedó de meta a inicio, se voltea
    cells.reverse()
    return tuple(cells)


# Función para crear un resultado de búsqueda exitoso
def found(
    name: str,
    problem: PathProblem,
    parents: dict[GameState, GameState | None],
    g: dict[GameState, float],
    goal: GameState,
    generated: int,
    expanded: int,
    max_frontier: int,
    started: float,
) -> SearchResult:
    return SearchResult(
        algorithm=name,
        success=True,
        path=reconstruct(parents, goal, problem.unit_id),
        cost=g[goal],
        generated=generated,
        expanded=expanded,
        max_frontier=max_frontier,
        time_seconds=time.perf_counter() - started,
    )


# Función para crear un resultado de búsqueda fallida
def failed(
    name: str, generated: int, expanded: int, max_frontier: int, started: float
) -> SearchResult:
    return SearchResult(
        algorithm=name,
        success=False,
        path=(),
        cost=0.0,
        generated=generated,
        expanded=expanded,
        max_frontier=max_frontier,
        time_seconds=time.perf_counter() - started,
    )
