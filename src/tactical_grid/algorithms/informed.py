"""Informed searches: A* and Beam Search (RF-20, RF-23)."""

import heapq
import time

from tactical_grid.algorithms.common import PathProblem, SearchResult, failed, found
from tactical_grid.algorithms.heuristics import Heuristic
from tactical_grid.domain.model import GameState


# Búsqueda A*: expande siempre el nodo con menor f(n) = g(n) + h(n)
def a_star(problem: PathProblem, heuristic: Heuristic, name: str = "A_STAR") -> SearchResult:
    """A* graph search: always expand the frontier node with the lowest f(n) = g(n) + h(n).

    Purpose: find the minimum-cost path using `heuristic` to steer the search (RF-20).
    Preconditions: terrain costs are positive; `heuristic` is admissible (and, to avoid
        re-expansions, consistent); the unit's start cell belongs to the board.
    Postconditions: ties on f are broken by first entry to the frontier (same convention as
        UCS); a cheaper path to a known state updates its g and parent and, if the state was
        already expanded, reopens it. Goal tested on expansion, so with an admissible
        heuristic the returned cost is optimal. Updates and reopenings are not counted as
        generated. `max_frontier` counts distinct states waiting to be expanded. `name`
        labels the result (e.g. which heuristic was used).
    Complexity: O(S log S) time and O(S) space over S reachable states in the worst case; a
        better heuristic expands fewer states.
    AI usage: Yes. Claude Code (Sonnet 5.5) drafted the function.
    AI intervention: none after the draft; reopening was added to stay correct if a custom
        heuristic is admissible but not consistent.
    Student validation: reviewed in meeting.
    """
    # se guarda la hora de inicio para medir el tiempo de la búsqueda
    started = time.perf_counter()
    start = problem.initial
    # padre de cada estado, para reconstruir el camino al final
    parents: dict[GameState, GameState | None] = {start: None}
    # mejor costo acumulado g conocido para cada estado
    g: dict[GameState, float] = {start: 0.0}
    # orden de llegada a la frontera, se usa para desempatar
    order: dict[GameState, int] = {start: 0}
    by_order: list[GameState] = [start]
    # frontera como cola de prioridad
    heap: list[tuple[float, int, float]] = [(heuristic(start), 0, 0.0)]  # (f, order, g)
    # estados que siguen esperando ser expandidos
    waiting: set[GameState] = {start}
    explored: set[GameState] = set()
    # contadores para las métricas
    generated, expanded, max_frontier = 1, 0, 1

    while heap:
        _, rank, cost_so_far = heapq.heappop(heap)
        node = by_order[rank]
        if node in explored or cost_so_far > g[node]:
            continue  # stale entry left behind by a cost update
        waiting.discard(node)
        # la meta se prueba al expandir, no al generar
        if problem.is_goal(node):
            return found(
                name, problem, parents, g, node, generated, expanded, max_frontier, started
            )
        expanded += 1
        explored.add(node)
        for child, cost in problem.expand(node):
            new_cost = g[node] + cost
            # estado nuevo: se registra y cuenta como generado
            if child not in g:
                parents[child] = node
                g[child] = new_cost
                order[child] = len(by_order)
                by_order.append(child)
                waiting.add(child)
                generated += 1
            # estado conocido con camino más barato: se actualiza y se reabre si ya se expandió
            elif new_cost < g[child]:
                parents[child] = node
                g[child] = new_cost
                explored.discard(child)  # reopen: a cheaper route was found
                waiting.add(child)
            # camino igual o peor: no se hace nada
            else:
                continue
            heapq.heappush(heap, (new_cost + heuristic(child), order[child], new_cost))
        max_frontier = max(max_frontier, len(waiting))
    # la frontera se vació sin llegar a la meta
    return failed(name, generated, expanded, max_frontier, started)


# Beam Search: por niveles, solo se conservan los k candidatos más prometedores de cada nivel
def beam_search(
    problem: PathProblem, heuristic: Heuristic, k: int, name: str = "BEAM"
) -> SearchResult:
    """Beam Search by levels: keep only the k most promising candidates of each level.

    Purpose: bounded-memory informed search (RF-23); trades completeness and optimality for
        a frontier that never holds more than k states between levels.
    Preconditions: `k >= 1`; `heuristic` need not be admissible, but a poor one prunes badly.
    Postconditions: level by level, every state in the beam is expanded in rank order (goal
        tested on expansion) and its children form the next candidates; the k candidates with
        the lowest f = g + h survive, ties broken by generation order. A state kept in some
        beam is never generated again; a pruned one may be, through another route. A cheaper
        route to a candidate of the same level updates it without counting as generated.
        `max_frontier` is the largest candidate set before pruning. The result can be
        suboptimal or fail although a solution exists, because pruned states are lost.
    Complexity: O(L * k * b * log(k * b)) time for L levels and branching factor b (at most
        4 here); O(S) space for the kept-state bookkeeping, O(k * b) for the live candidates.
    AI usage: Yes. Claude Code (Sonnet 5.5) drafted the function.
    AI intervention: none after the draft; ranking by f and by-level pruning are team
        decisions (G9, 2026-10-16).
    Student validation: reviewed in meeting.
    """
    if k < 1:
        raise ValueError(f"beam width k must be at least 1, got {k}")
    started = time.perf_counter()
    start = problem.initial
    parents: dict[GameState, GameState | None] = {start: None}
    g: dict[GameState, float] = {start: 0.0}
    # estados que ya entraron a algún haz (no se vuelven a generar)
    kept: set[GameState] = {start}
    # haz actual: los estados del nivel que se va a expandir
    beam: list[GameState] = [start]
    generated, expanded, max_frontier = 1, 0, 1

    while beam:
        # candidatos del siguiente nivel, aún sin podar
        pending: dict[GameState, tuple[float, GameState]] = {}  # child -> (g, parent)
        for node in beam:
            if problem.is_goal(node):
                return found(
                    name, problem, parents, g, node, generated, expanded, max_frontier, started
                )
            expanded += 1
            for child, cost in problem.expand(node):
                if child in kept:
                    continue
                new_cost = g[node] + cost
                # candidato nuevo: cuenta como generado
                if child not in pending:
                    generated += 1
                    pending[child] = (new_cost, node)
                # candidato repetido en este nivel: se queda con la ruta más barata
                elif new_cost < pending[child][0]:
                    pending[child] = (new_cost, node)
        max_frontier = max(max_frontier, len(pending))
        # se ordenan por f = g + h y, si empatan, por orden de generación
        ranked = sorted(
            enumerate(pending.items()),
            key=lambda item: (item[1][1][0] + heuristic(item[1][0]), item[0]),
        )
        # poda: solo los k mejores pasan al siguiente nivel
        beam = []
        for _, (child, (cost, parent)) in ranked[:k]:
            parents[child] = parent
            g[child] = cost
            kept.add(child)
            beam.append(child)
    return failed(name, generated, expanded, max_frontier, started)
