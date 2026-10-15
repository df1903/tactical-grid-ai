"""Uninformed and cost-based single-unit searches: BFS, DFS and UCS (RF-15, RF-17)."""

import time
from collections import deque

from tactical_grid.algorithms.common import PathProblem, SearchResult, reconstruct
from tactical_grid.domain.model import GameState


def bfs(problem: PathProblem) -> SearchResult:
    """Breadth-first graph search with a FIFO frontier.

    Purpose: find the path with the fewest moves; costs are only accumulated and reported.
    Preconditions: `problem.initial` belongs to `problem.board`; the goal is a board cell.
    Postconditions: goal test is applied when a node is expanded (not when generated).
        A state is generated at most once: it is skipped if already in the frontier or
        expanded. The initial state counts as generated. Successor order is the domain
        order (up, down, left, right). `max_frontier` is the peak frontier size.
    Complexity: O(S) time and space over S reachable states (position-only state space).
    AI usage: Claude Code (Sonnet 5.5) drafted the function.
    AI intervention: none after the draft; goal-at-expansion is a team convention.
    Student validation: pending cross-review by the other team member.
    """
    started = time.perf_counter()
    start = problem.initial
    parents: dict[GameState, GameState | None] = {start: None}
    g: dict[GameState, float] = {start: 0.0}
    frontier: deque[GameState] = deque([start])
    explored: set[GameState] = set()
    generated, expanded, max_frontier = 1, 0, 1

    while frontier:
        node = frontier.popleft()
        if problem.is_goal(node):
            return _found(
                "BFS", problem, parents, g, node, generated, expanded, max_frontier, started
            )
        expanded += 1
        explored.add(node)
        for child, cost in problem.expand(node):
            if child in explored or child in parents:
                continue
            parents[child] = node
            g[child] = g[node] + cost
            frontier.append(child)
            generated += 1
        max_frontier = max(max_frontier, len(frontier))
    return _failed("BFS", generated, expanded, max_frontier, started)


def dfs(problem: PathProblem) -> SearchResult:
    """Depth-first graph search with a LIFO frontier.

    Purpose: find some path by always going deepest first; it is neither shortest nor
        cheapest. Reported cost is the accumulated cost of the path found.
    Preconditions: `problem.initial` belongs to `problem.board`; the goal is a board cell.
    Postconditions: same bookkeeping as `bfs` (goal tested on expansion, no state generated
        twice, initial state counts as generated). Children are pushed in reverse domain
        order so the first one in domain order (up, down, left, right) is expanded first.
    Complexity: O(S) time and space over S reachable states.
    AI usage: Claude Code (Sonnet 5.5) drafted the function.
    AI intervention: none after the draft; successor order is a team convention.
    Student validation: pending cross-review by the other team member.
    """
    started = time.perf_counter()
    start = problem.initial
    parents: dict[GameState, GameState | None] = {start: None}
    g: dict[GameState, float] = {start: 0.0}
    frontier: list[GameState] = [start]
    explored: set[GameState] = set()
    generated, expanded, max_frontier = 1, 0, 1

    while frontier:
        node = frontier.pop()
        if problem.is_goal(node):
            return _found(
                "DFS", problem, parents, g, node, generated, expanded, max_frontier, started
            )
        expanded += 1
        explored.add(node)
        fresh: list[GameState] = []
        for child, cost in problem.expand(node):
            if child in explored or child in parents:
                continue
            parents[child] = node
            g[child] = g[node] + cost
            fresh.append(child)
            generated += 1
        frontier.extend(reversed(fresh))
        max_frontier = max(max_frontier, len(frontier))
    return _failed("DFS", generated, expanded, max_frontier, started)


def _found(
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


def _failed(
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
