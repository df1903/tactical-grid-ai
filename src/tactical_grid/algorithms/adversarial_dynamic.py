"""Adversarial decision for the dynamic variant: depth-limited Minimax and alpha-beta.

Same recursion, tie-break and metrics as `adversarial.py` (which is not modified); the differences
are that states are `DynamicState` and that a blocked side is not a leaf: it passes its turn, which
is a node with a single child that consumes one level of depth.
"""

import math
import time
from dataclasses import dataclass

from tactical_grid.algorithms.adversarial import ActionOrder
from tactical_grid.algorithms.utility_dynamic import DynamicUtility
from tactical_grid.domain.dynamic import (
    DynamicRules,
    DynamicState,
    apply,
    is_terminal,
    legal_actions,
    pass_turn,
)
from tactical_grid.domain.model import Action, Board


# Clase para guardar el resultado de una decisión de la variante (mismos campos que la base)
@dataclass(frozen=True)
class DynamicAdversarialResult:
    """Outcome of one decision; fields mirror `AdversarialResult`."""

    algorithm: str
    action: Action | None  # None when the root is terminal or its side must pass
    value: float
    generated: int
    evaluated: int
    pruned: int
    depth_reached: int
    time_seconds: float
    root_values: tuple[tuple[Action, float], ...]
    considered: tuple[tuple[DynamicState, Action], ...] = ()  # filled only with `record=True`


# Minimax con límite de profundidad (sin poda) para la variante dinámica
def minimax_dynamic(
    board: Board,
    state: DynamicState,
    depth: int,
    utility: DynamicUtility,
    params: DynamicRules,
    order: ActionOrder = "default",
    record: bool = False,
) -> DynamicAdversarialResult:
    """Plain depth-limited Minimax on the dynamic variant.

    Purpose: pick the root action with the best worst-case utility for the side to move.
    Preconditions: `depth` >= 1; `utility` is measured on the dynamic state from the side to move.
    Postconditions: the chosen action is the first one (in `order`) with the highest value;
        nothing is pruned. A blocked side passes (a one-child node) and, at the root, returns
        `action=None` with the value of the pass.
    Complexity: O(b^d) time with branching b and depth d; O(d) space.
    AI usage: Yes. Claude Code (Sonnet 5.5) drafted the function from the approved plan.
    AI intervention: none after the draft.
    Student validation: tests/test_adversarial_dynamic.py checks the equality with alpha-beta,
        the pass nodes and that only legal dynamic actions are considered.
    """
    return _decide("MINIMAX", board, state, depth, utility, params, order, record, prune=False)


# Minimax con poda alfa-beta para la variante dinámica
def alpha_beta_dynamic(
    board: Board,
    state: DynamicState,
    depth: int,
    utility: DynamicUtility,
    params: DynamicRules,
    order: ActionOrder = "default",
    record: bool = False,
) -> DynamicAdversarialResult:
    """Alpha-beta on the dynamic variant.

    Purpose: same decision as `minimax_dynamic` while skipping branches that cannot change it.
    Preconditions: as `minimax_dynamic`.
    Postconditions: same action and value as `minimax_dynamic` for equal depth, utility and order.
        A node is cut when alpha >= beta; pass nodes have one child and are never cut.
    Complexity: O(b^(d/2)) time at best with good ordering, O(b^d) at worst; O(d) space.
    AI usage: Yes. Claude Code (Sonnet 5.5) drafted the function from the approved plan.
    AI intervention: none after the draft.
    Student validation: tests/test_adversarial_dynamic.py checks that it returns the same value and
        action as the dynamic Minimax on small and large maps.
    """
    return _decide("ALPHA_BETA", board, state, depth, utility, params, order, record, prune=True)


# Recursión común a ambos algoritmos; `prune` activa la poda
def _decide(
    name: str,
    board: Board,
    state: DynamicState,
    depth: int,
    utility: DynamicUtility,
    params: DynamicRules,
    order: ActionOrder,
    record: bool,
    prune: bool,
) -> DynamicAdversarialResult:
    if depth < 1:
        raise ValueError(f"depth must be >= 1, got {depth}")
    started = time.perf_counter()
    # MAX es el lado que mueve en la raíz
    max_side = state.turn
    counters = {"generated": 0, "evaluated": 0, "pruned": 0, "reached": 0}
    considered: list[tuple[DynamicState, Action]] = []

    # acciones legales de un nodo, en el orden pedido
    def ordered(node: DynamicState) -> list[Action]:
        actions = legal_actions(board, node)
        return actions[::-1] if order == "reversed" else actions

    # valor minimax de un nodo; alpha y beta son las cotas de la poda
    def value_of(node: DynamicState, level: int, alpha: float, beta: float) -> float:
        counters["reached"] = max(counters["reached"], level)
        # hoja: se llegó al límite de profundidad o el juego terminó
        if level == depth or is_terminal(board, node):
            counters["evaluated"] += 1
            return utility(node)
        actions = ordered(node)
        if not actions:  # el bando no tiene unidades libres: pasa el turno (un solo hijo)
            counters["generated"] += 1
            return value_of(pass_turn(board, node), level + 1, alpha, beta)
        maximizing = node.turn is max_side
        best = -math.inf if maximizing else math.inf
        for index, action in enumerate(actions):
            if record:
                considered.append((node, action))
            child = apply(board, node, action, params)
            counters["generated"] += 1
            score = value_of(child, level + 1, alpha, beta)
            if maximizing:
                best = max(best, score)
                alpha = max(alpha, best)
            else:
                best = min(best, score)
                beta = min(beta, best)
            # poda: si alpha >= beta, las acciones que faltan no pueden cambiar el resultado
            if prune and alpha >= beta:
                counters["pruned"] += len(actions) - index - 1
                break
        return best

    root_values: list[tuple[Action, float]] = []
    chosen: Action | None = None
    best_value = -math.inf
    alpha = -math.inf
    root_actions = [] if is_terminal(board, state) else ordered(state)
    if not root_actions:
        if is_terminal(board, state):
            counters["evaluated"] += 1
            best_value = utility(state)
        else:
            # raíz bloqueada: no hay acción que elegir, el valor es el de pasar el turno
            counters["generated"] += 1
            best_value = value_of(pass_turn(board, state), 1, -math.inf, math.inf)
    else:
        for action in root_actions:
            if record:
                considered.append((state, action))
            child = apply(board, state, action, params)
            counters["generated"] += 1
            score = value_of(child, 1, alpha, math.inf)
            root_values.append((action, score))
            # solo reemplaza si es estrictamente mejor, así los empates conservan la primera
            if score > best_value:
                best_value, chosen = score, action
            alpha = max(alpha, best_value) if prune else alpha
    return DynamicAdversarialResult(
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
