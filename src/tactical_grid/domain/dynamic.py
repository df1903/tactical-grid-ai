"""Dynamic variant of the rules: terrain cost as recovery turns and tackle that steals the resource.

It lives next to `rules.py` and never changes it: `DynamicState` wraps a base `GameState` and adds
the recovery counters and the immunity of the carrier. Movement, pick-up and delivery are delegated
to the base rules; only the recovery and the tackle differ.
"""

import math
from dataclasses import dataclass

from tactical_grid.domain import rules
from tactical_grid.domain.model import Action, Board, GameState, Position, Side, Tackle


# Clase para guardar los parámetros de la variante (salen del JSON, no del código)
@dataclass(frozen=True)
class DynamicRules:
    """Scenario parameters of the variant: turns of penalty and of immunity after a steal."""

    tackle_penalty: int  # turnos propios que queda inmovilizada la víctima de un robo
    steal_immunity: int  # turnos del rival en que el nuevo portador no puede ser robado


# Clase para representar el estado de la variante: estado base + contadores
@dataclass(frozen=True)
class DynamicState:
    """Base state plus own turns each unit still has to wait and the carrier's immunity.

    Two states with the same base but different counters are different states.
    """

    base: GameState
    recovery: tuple[tuple[str, int], ...]  # sorted by unit id; 0 means the unit is free
    immunity: int = 0  # rival turns left in which the carrier cannot be tackled

    # Turnos de recuperación que le quedan a una unidad
    def recovery_of(self, unit_id: str) -> int:
        for uid, turns in self.recovery:
            if uid == unit_id:
                return turns
        raise KeyError(unit_id)

    # Bando que tiene el turno
    @property
    def turn(self) -> Side:
        return self.base.turn


# Estado dinámico inicial: todas las unidades libres y sin inmunidad
def initial_dynamic_state(state: GameState) -> DynamicState:
    return DynamicState(base=state, recovery=tuple((uid, 0) for uid, _ in state.positions))


# Turnos de recuperación al entrar a una celda: el costo del terreno de destino menos 1
def recovery_turns(board: Board, dest: Position) -> int:
    """Own turns a unit waits after entering the cell `dest`: `ceil(cost) - 1`.

    Purpose: turn the terrain cost read from the scenario into waiting turns (cost 1 -> 0).
    Preconditions: the destination is passable (the move is legal).
    Postconditions: never negative; no cost or terrain name is written here.
    Complexity: O(1).
    AI usage: Yes. Claude Code (Sonnet 5.5) drafted the function from the approved plan.
    AI intervention: none after the draft.
    Student validation: tests/test_dynamic_rules.py checks the costs 1, 2, 3, 4, 7 and a decimal.
    """
    return max(math.ceil(board.cost_at(dest)) - 1, 0)


# Fin de partida: el de la base (entrega, o límite de turnos)
def is_terminal(board: Board, state: DynamicState) -> bool:
    return rules.is_terminal(board, state.base)


# Acciones legales de la variante: solo actúan unidades libres; el robo exige no haber inmunidad
def legal_actions(board: Board, state: DynamicState) -> list[Action]:
    """List the actions available to the side to move in the dynamic variant.

    Purpose: base legal actions restricted to free units, plus the steal rule.
    Preconditions: `state.base` belongs to `board`.
    Postconditions: empty if the game is over or no free unit can act (the side passes).
        Otherwise the base order: moves per free unit sorted by id, then `Tackle(unit, carrier)`
        for each free own unit adjacent to the rival carrier, only when the carrier has no
        immunity. A unit in recovery neither moves nor tackles, but it can be tackled.
    Complexity: O(U * 4 * U) with U units.
    AI usage: Yes. Claude Code (Sonnet 5.5) drafted the function from the approved plan.
    AI intervention: none after the draft.
    Student validation: tests/test_dynamic_rules.py checks that units in recovery are excluded,
        the base order, immunity and the tackle conditions.
    """
    base = state.base
    # la base ya devuelve [] en estados terminales
    return [action for action in rules.legal_actions(board, base) if _can_act(board, state, action)]


# Una acción de la base es legal en la variante si la unidad está libre y el robo no está protegido
def _can_act(board: Board, state: DynamicState, action: Action) -> bool:
    if state.recovery_of(action.unit_id) > 0:
        return False
    return not (isinstance(action, Tackle) and state.immunity > 0)


# Contadores al cerrar el turno de `side`: sus unidades bajan 1 y luego se aplican `updates`
def _counters(
    board: Board, state: DynamicState, side: Side, updates: dict[str, int]
) -> tuple[tuple[str, int], ...]:
    result: list[tuple[str, int]] = []
    for uid, turns in state.recovery:
        if board.unit_sides[uid] is side:
            turns = max(turns - 1, 0)
        result.append((uid, updates.get(uid, turns)))
    return tuple(result)


# La inmunidad baja cuando juega el bando que no lleva el recurso
def _immunity_after(board: Board, state: DynamicState, side: Side) -> int:
    carrier = state.base.carrier
    if state.immunity > 0 and carrier is not None and board.unit_sides[carrier] is not side:
        return state.immunity - 1
    return state.immunity


# Aplica una acción legal y devuelve el estado sucesor
def apply(board: Board, state: DynamicState, action: Action, params: DynamicRules) -> DynamicState:
    """Apply a legal dynamic action.

    Purpose: deterministic transition of the variant.
    Preconditions: `action` is in `legal_actions(board, state)`.
    Postconditions: the turn passes and `turn_number` grows by one. At the end of the turn all
        units of the side that played drop one recovery turn; then a moved unit gets
        `recovery_turns` of its destination. A tackle makes the tackler the carrier (nobody
        moves, no cost, no recovery for the tackler), puts the victim at
        `max(current, tackle_penalty)` and gives the new carrier `steal_immunity` rival turns.
        Delivery is detected by `rules.winner` (stealing on the own base wins at once).
    Complexity: O(U).
    AI usage: Yes. Claude Code (Sonnet 5.5) drafted the function from the approved plan.
    AI intervention: none after the draft.
    Student validation: tests/test_dynamic_rules.py checks the example of the cost 7 swamp,
        the penalty as a maximum, the immunity and the steal on the own base.
    """
    side = state.turn
    if isinstance(action, Tackle):
        base = state.base
        next_base = GameState(
            positions=base.positions,
            carrier=action.unit_id,
            resource=None,
            turn=side.opponent,
            turn_number=base.turn_number + 1,
        )
        updates = {action.target: max(state.recovery_of(action.target), params.tackle_penalty)}
        return DynamicState(
            base=next_base,
            recovery=_counters(board, state, side, updates),
            immunity=params.steal_immunity,
        )
    next_base, _ = rules.apply(board, state.base, action)
    return DynamicState(
        base=next_base,
        recovery=_counters(
            board, state, side, {action.unit_id: recovery_turns(board, action.dest)}
        ),
        immunity=_immunity_after(board, state, side),
    )


# Pasa el turno cuando el bando no tiene unidades libres con acciones
def pass_turn(board: Board, state: DynamicState) -> DynamicState:
    """Pass the turn of a blocked side: its units still drop one recovery turn."""
    side = state.turn
    return DynamicState(
        base=rules.skip_turn(state.base),
        recovery=_counters(board, state, side, {}),
        immunity=_immunity_after(board, state, side),
    )


# Expande un estado en pares (acción, sucesor) en el orden de `legal_actions`
def successors(
    board: Board, state: DynamicState, params: DynamicRules
) -> list[tuple[Action, DynamicState]]:
    return [(a, apply(board, state, a, params)) for a in legal_actions(board, state)]
