"""Informed searches: A* and Beam Search (RF-20, RF-23)."""

import heapq
import time

from tactical_grid.algorithms.common import PathProblem, SearchResult, failed, found
from tactical_grid.algorithms.heuristics import Heuristic
from tactical_grid.domain.model import GameState


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
    AI usage: Claude Code (Sonnet 5.5) drafted the function.
    AI intervention: none after the draft; reopening was added to stay correct if a custom
        heuristic is admissible but not consistent.
    Student validation: pending cross-review by the other team member.
    """
    started = time.perf_counter()
    start = problem.initial
    parents: dict[GameState, GameState | None] = {start: None}
    g: dict[GameState, float] = {start: 0.0}
    order: dict[GameState, int] = {start: 0}
    by_order: list[GameState] = [start]
    heap: list[tuple[float, int, float]] = [(heuristic(start), 0, 0.0)]  # (f, order, g)
    waiting: set[GameState] = {start}
    explored: set[GameState] = set()
    generated, expanded, max_frontier = 1, 0, 1

    while heap:
        _, rank, cost_so_far = heapq.heappop(heap)
        node = by_order[rank]
        if node in explored or cost_so_far > g[node]:
            continue  # stale entry left behind by a cost update
        waiting.discard(node)
        if problem.is_goal(node):
            return found(
                name, problem, parents, g, node, generated, expanded, max_frontier, started
            )
        expanded += 1
        explored.add(node)
        for child, cost in problem.expand(node):
            new_cost = g[node] + cost
            if child not in g:
                parents[child] = node
                g[child] = new_cost
                order[child] = len(by_order)
                by_order.append(child)
                waiting.add(child)
                generated += 1
            elif new_cost < g[child]:
                parents[child] = node
                g[child] = new_cost
                explored.discard(child)  # reopen: a cheaper route was found
                waiting.add(child)
            else:
                continue
            heapq.heappush(heap, (new_cost + heuristic(child), order[child], new_cost))
        max_frontier = max(max_frontier, len(waiting))
    return failed(name, generated, expanded, max_frontier, started)
