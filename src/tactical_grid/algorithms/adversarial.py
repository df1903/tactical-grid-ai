"""Adversarial decision: depth-limited Minimax and alpha-beta pruning (RF-25 to RF-32).

MAX is the side to move at the root; one unit of depth is one action of one side (G11), so
MAX and MIN alternate by ply. Both algorithms share one recursion; alpha-beta only adds the
cutoff. Legality and transitions come from `domain.rules`.
"""

import math
import time
from dataclasses import dataclass
from typing import Literal

from tactical_grid.algorithms.utility import Utility
from tactical_grid.domain.model import Action, Board, GameState
from tactical_grid.domain.rules import apply, is_terminal, legal_actions

ActionOrder = Literal["default", "reversed"]


@dataclass(frozen=True)
class AdversarialResult:
    """Outcome of one decision; fields mirror the RF-30 metrics."""

    algorithm: str
    action: Action | None  # None when the root is terminal
    value: float  # Minimax value of the root state
    generated: int
    evaluated: int
    pruned: int
    depth_reached: int
    time_seconds: float
    root_values: tuple[tuple[Action, float], ...]  # value found for each root action
    considered: tuple[tuple[GameState, Action], ...] = ()  # filled only with `record=True`


def minimax(
    board: Board,
    state: GameState,
    depth: int,
    utility: Utility,
    order: ActionOrder = "default",
    record: bool = False,
) -> AdversarialResult:
    """Plain depth-limited Minimax.

    Purpose: pick the root action with the best worst-case utility for the side to move.
    Preconditions: `depth` >= 1; `utility` is measured from the side to move at `state`.
    Postconditions: the chosen action is the first one (in `order`) with the highest value;
        nothing is pruned. Leaves are terminal states or nodes at the depth limit.
    Complexity: O(b^d) time with branching b and depth d; O(d) space.
    AI usage: Claude Code (Sonnet 5.5) drafted the function.
    AI intervention: none after the draft.
    Student validation: pending cross-review by the other team member.
    """
    return _decide("MINIMAX", board, state, depth, utility, order, record, prune=False)


def alpha_beta(
    board: Board,
    state: GameState,
    depth: int,
    utility: Utility,
    order: ActionOrder = "default",
    record: bool = False,
) -> AdversarialResult:
    """Minimax with alpha-beta pruning.

    Purpose: same decision as `minimax` while skipping branches that cannot change it.
    Preconditions: as `minimax`.
    Postconditions: same action and value as `minimax` for equal depth, utility and order
        (RF-31). A node is cut when alpha >= beta; `pruned` counts the child actions skipped.
        At the root only a strictly better value replaces the choice, so ties keep the first
        action exactly like `minimax`; root values of later actions may be bounds.
    Complexity: O(b^(d/2)) time at best with good ordering, O(b^d) at worst; O(d) space.
    AI usage: Claude Code (Sonnet 5.5) drafted the function.
    AI intervention: none after the draft.
    Student validation: pending cross-review by the other team member.
    """
    return _decide("ALPHA_BETA", board, state, depth, utility, order, record, prune=True)


def _decide(
    name: str,
    board: Board,
    state: GameState,
    depth: int,
    utility: Utility,
    order: ActionOrder,
    record: bool,
    prune: bool,
) -> AdversarialResult:
    if depth < 1:
        raise ValueError(f"depth must be >= 1, got {depth}")
    started = time.perf_counter()
    max_side = state.turn
    counters = {"generated": 0, "evaluated": 0, "pruned": 0, "reached": 0}
    considered: list[tuple[GameState, Action]] = []

    def ordered(node: GameState) -> list[Action]:
        actions = legal_actions(board, node)
        return actions[::-1] if order == "reversed" else actions

    def value_of(node: GameState, level: int, alpha: float, beta: float) -> float:
        counters["reached"] = max(counters["reached"], level)
        if level == depth or is_terminal(board, node):
            counters["evaluated"] += 1
            return utility(node)
        actions = ordered(node)
        if not actions:  # side to move is blocked: its turn is skipped, evaluate as a leaf
            counters["evaluated"] += 1
            return utility(node)
        maximizing = node.turn is max_side
        best = -math.inf if maximizing else math.inf
        for index, action in enumerate(actions):
            if record:
                considered.append((node, action))
            child, _ = apply(board, node, action)
            counters["generated"] += 1
            score = value_of(child, level + 1, alpha, beta)
            if maximizing:
                best = max(best, score)
                alpha = max(alpha, best)
            else:
                best = min(best, score)
                beta = min(beta, best)
            if prune and alpha >= beta:
                counters["pruned"] += len(actions) - index - 1
                break
        return best

    root_values: list[tuple[Action, float]] = []
    chosen: Action | None = None
    best_value = -math.inf
    alpha = -math.inf
    if is_terminal(board, state):
        counters["evaluated"] += 1
        best_value = utility(state)
    else:
        for action in ordered(state):
            if record:
                considered.append((state, action))
            child, _ = apply(board, state, action)
            counters["generated"] += 1
            score = value_of(child, 1, alpha, math.inf)
            root_values.append((action, score))
            if score > best_value:
                best_value, chosen = score, action
            alpha = max(alpha, best_value) if prune else alpha
    return AdversarialResult(
        algorithm=name,
        action=chosen,
        value=best_value,
        generated=counters["generated"],
        evaluated=counters["evaluated"],
        pruned=counters["pruned"],
        depth_reached=counters["reached"],
        time_seconds=time.perf_counter() - started,
        root_values=tuple(root_values),
        considered=tuple(considered),
    )
