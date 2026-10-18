"""Uninformed and cost-based single-unit searches: BFS, DFS and UCS (RF-15, RF-17)."""

import heapq
import time
from collections import deque

from tactical_grid.algorithms.common import PathProblem, SearchResult, failed, found
from tactical_grid.domain.model import GameState


# Busqueda en anchura (BFS)
def bfs(problem: PathProblem) -> SearchResult:
    """Breadth-first graph search with a FIFO frontier.

    Purpose: find the path with the fewest moves; costs are only accumulated and reported.
    Preconditions: `problem.initial` belongs to `problem.board`; the goal is a board cell.
    Postconditions: goal test is applied when a node is expanded (not when generated).
        A state is generated at most once: it is skipped if already in the frontier or
        expanded. The initial state counts as generated. Successor order is the domain
        order (up, down, left, right). `max_frontier` is the peak frontier size.
    Complexity: O(S) time and space over S reachable states (position-only state space).
    AI usage: Yes. Claude Code (Sonnet 5.5) drafted the function.
    AI intervention: none after the draft; goal-at-expansion is a team convention.
    Student validation: reviewed in meeting.
    """
    # se guarda la hora de inicio para medir el tiempo
    started = time.perf_counter()
    start = problem.initial
    # padre de cada estado, para reconstruir el camino
    parents: dict[GameState, GameState | None] = {start: None}
    # costo acumulado hasta cada estado
    g: dict[GameState, float] = {start: 0.0}
    # frontera FIFO: el primero en entrar es el primero en salir
    frontier: deque[GameState] = deque([start])
    explored: set[GameState] = set()
    # contadores para las métricas
    generated, expanded, max_frontier = 1, 0, 1

    while frontier:
        node = frontier.popleft()
        # la meta se prueba al expandir el nodo
        if problem.is_goal(node):
            return found(
                "BFS", problem, parents, g, node, generated, expanded, max_frontier, started
            )
        expanded += 1
        explored.add(node)
        for child, cost in problem.expand(node):
            # se ignoran estados ya expandidos o ya en la frontera
            if child in explored or child in parents:
                continue
            parents[child] = node
            g[child] = g[node] + cost
            frontier.append(child)
            generated += 1
        max_frontier = max(max_frontier, len(frontier))
    # la frontera se vació sin encontrar la meta
    return failed("BFS", generated, expanded, max_frontier, started)


# Busqueda en profundidad (DFS)
def dfs(problem: PathProblem) -> SearchResult:
    """Depth-first graph search with a LIFO frontier.

    Purpose: find some path by always going deepest first; it is neither shortest nor
        cheapest. Reported cost is the accumulated cost of the path found.
    Preconditions: `problem.initial` belongs to `problem.board`; the goal is a board cell.
    Postconditions: same bookkeeping as `bfs` (goal tested on expansion, no state generated
        twice, initial state counts as generated). Children are pushed in reverse domain
        order so the first one in domain order (up, down, left, right) is expanded first.
    Complexity: O(S) time and space over S reachable states.
    AI usage: Yes. Claude Code (Sonnet 5.5) drafted the function.
    AI intervention: none after the draft; successor order is a team convention.
    Student validation: reviewed in meeting.
    """
    started = time.perf_counter()
    start = problem.initial
    parents: dict[GameState, GameState | None] = {start: None}
    g: dict[GameState, float] = {start: 0.0}
    # frontera LIFO (pila): el último en entrar es el primero en salir
    frontier: list[GameState] = [start]
    explored: set[GameState] = set()
    generated, expanded, max_frontier = 1, 0, 1

    while frontier:
        node = frontier.pop()
        if problem.is_goal(node):
            return found(
                "DFS", problem, parents, g, node, generated, expanded, max_frontier, started
            )
        expanded += 1
        explored.add(node)
        # hijos nuevos de este nodo
        fresh: list[GameState] = []
        for child, cost in problem.expand(node):
            if child in explored or child in parents:
                continue
            parents[child] = node
            g[child] = g[node] + cost
            fresh.append(child)
            generated += 1
        # se apilan al revés para que salga primero el primer hijo del dominio
        frontier.extend(reversed(fresh))
        max_frontier = max(max_frontier, len(frontier))
    return failed("DFS", generated, expanded, max_frontier, started)


# Busqueda de costo uniforme (UCS)
def ucs(problem: PathProblem) -> SearchResult:
    """Uniform-cost search: always expand the frontier node with the lowest g(n).

    Purpose: find the minimum-cost path (not the one with fewest moves), RF-17.
    Preconditions: `problem.initial` belongs to `problem.board`; terrain costs are
        positive (guaranteed by the scenario loader).
    Postconditions: ties on g(n) are broken by first entry to the frontier (RF-19); a
        cheaper path to a state still in the frontier updates its cost and parent but keeps
        its original entry order, and is not counted as a new generated state. Goal tested
        on expansion, so the returned cost is optimal. `max_frontier` counts distinct
        states waiting to be expanded (stale heap entries are not counted).
    Complexity: O(S log S) time and O(S) space over S reachable states.
    AI usage: Yes. Claude Code (Sonnet 5.5) drafted the function.
    AI intervention: none after the draft; tie-break and update rules come from RF-19.
    Student validation: reviewed in meeting.
    """
    started = time.perf_counter()
    start = problem.initial
    parents: dict[GameState, GameState | None] = {start: None}
    g: dict[GameState, float] = {start: 0.0}
    # orden de llegada a la frontera, sirve para desempatar costos iguales
    order: dict[GameState, int] = {start: 0}
    by_order: list[GameState] = [start]
    # frontera como cola de prioridad con (costo, orden de llegada)
    heap: list[tuple[float, int]] = [(0.0, 0)]
    # estados que siguen esperando ser expandidos
    waiting: set[GameState] = {start}
    explored: set[GameState] = set()
    generated, expanded, max_frontier = 1, 0, 1

    while heap:
        cost_so_far, rank = heapq.heappop(heap)
        node = by_order[rank]
        if node in explored or cost_so_far > g[node]:
            continue  # stale entry left behind by a cost update
        waiting.discard(node)
        # la meta se prueba al expandir, por eso el costo devuelto es el óptimo
        if problem.is_goal(node):
            return found(
                "UCS", problem, parents, g, node, generated, expanded, max_frontier, started
            )
        expanded += 1
        explored.add(node)
        for child, cost in problem.expand(node):
            if child in explored:
                continue
            new_cost = g[node] + cost
            # estado nuevo: se registra y cuenta como generado
            if child not in g:
                parents[child] = node
                g[child] = new_cost
                order[child] = len(by_order)
                by_order.append(child)
                waiting.add(child)
                generated += 1
                heapq.heappush(heap, (new_cost, order[child]))
            # estado conocido con un camino más barato: se actualiza costo y padre
            elif new_cost < g[child]:
                parents[child] = node
                g[child] = new_cost
                heapq.heappush(heap, (new_cost, order[child]))
        max_frontier = max(max_frontier, len(waiting))
    return failed("UCS", generated, expanded, max_frontier, started)
