"""Game rules: legal actions, transitions, costs and terminal conditions."""

from dataclasses import replace

from tactical_grid.domain.model import Action, Board, GameState, Move, Side, Tackle


# funcion para determinar si hay un ganador, es decir, si un lado entrego el recurso a su base
def winner(board: Board, state: GameState) -> Side | None:
    """Side that delivered the resource to its own base, or None."""
    if state.carrier is None:
        return None
    side = board.unit_sides[state.carrier]
    if state.position_of(state.carrier) == board.bases[side]:
        return side
    return None


# funcion para determinar si hay un empate: no hay ganador y se llego al limite de turnos
def is_draw(board: Board, state: GameState) -> bool:
    # empate: nadie ganó y ya no quedan turnos
    return winner(board, state) is None and state.turn_number >= board.turn_limit


# funcion para determinar si el juego ha terminado: hay un ganador o se llego al limite de turnos
def is_terminal(board: Board, state: GameState) -> bool:
    return winner(board, state) is not None or state.turn_number >= board.turn_limit


# funcion para determinar las acciones legales: movimientos y placajes del lado con el turno
def legal_actions(board: Board, state: GameState) -> list[Action]:
    """List the actions available to the side whose turn it is.

    Purpose: enumerate deterministic legal actions: moves (4 directions) per unit, plus a
        tackle for each own unit adjacent to the rival carrier.
    Preconditions: `state` belongs to `board` (same units and bounds).
    Postconditions: empty if the game is over or the side has no unit that can move;
        otherwise, per active unit (sorted by id), moves to free passable in-map cells
        that are not the rival base, followed by `Tackle(unit, carrier)` for each own unit
        adjacent to the carrier when the carrier belongs to the rival.
    Complexity: O(U * 4 * U) with U units (occupancy lookup is linear in U).
    AI usage: Yes. Claude Code (Sonnet 5.5) drafted the function from `rules.md`.
    AI intervention: none after the draft; rules were decided by the team on 2026-10-14.
    Student validation: tests/test_domain_rules.py checks four directions, map edges, one unit per
        cell, rival base blocked, pick-up on arrival, delivery wins and the tackle rules; expected
        outcomes come from rules.md, not from the code.
    """
    # si el juego terminó no hay acciones
    if is_terminal(board, state):
        return []
    # la base rival está prohibida como destino
    rival_base = board.bases[state.turn.opponent]
    actions: list[Action] = []
    for uid, pos in state.positions:
        # solo se mueven las unidades del lado que tiene el turno
        if board.unit_sides[uid] is not state.turn:
            continue
        # el destino debe ser transitable, no ser la base rival y estar libre
        for dest in pos.neighbors():
            if board.is_passable(dest) and dest != rival_base and state.unit_at(dest) is None:
                actions.append(Move(uid, dest))
    # placaje: solo si el portador es rival y la unidad está pegada a él al empezar el turno
    if state.carrier is not None and board.unit_sides[state.carrier] is not state.turn:
        carrier_pos = state.position_of(state.carrier)
        for uid, pos in state.positions:
            if board.unit_sides[uid] is state.turn and pos.is_adjacent(carrier_pos):
                actions.append(Tackle(uid, state.carrier))
    return actions


# funcion para pasar el turno cuando el lado que tiene el turno no tiene acciones legales
def skip_turn(state: GameState) -> GameState:
    """Pass the turn when the side to move has no legal action (not an action itself)."""
    return replace(state, turn=state.turn.opponent, turn_number=state.turn_number + 1)


# funcion para aplicar una accion legal y devolver el estado sucesor y el costo del paso
def apply(board: Board, state: GameState, action: Action) -> tuple[GameState, float]:
    """Apply a legal action and return the successor state and the step cost.

    Purpose: deterministic transition, including pickup, delivery and tackle.
    Preconditions: `action` is in `legal_actions(board, state)`.
    Postconditions: turn passes to the opponent and `turn_number` grows by one.
        Move costs the destination terrain cost (paid on entering). Order inside a move:
        (1) pickup on arrival at the resource cell, (2) delivery at own base (wins).
        A move never makes the carrier lose the resource by itself.
        Tackle costs 0, moves nobody and makes the rival carrier drop the resource on its
        own cell (no transfer); the carrier can answer on its next turn before it is tackled
        again, and only a unit that arrives at that cell picks the resource up.
    Complexity: O(U).
    AI usage: Yes. Claude Code (Sonnet 5.5) drafted the function from `rules.md`.
    AI intervention: none after the draft.
    Student validation: tests/test_domain_rules.py checks the blocked-side pass, skip_turn and the
        turn-limit draw.
    """
    next_turn = state.turn.opponent
    # placaje: el portador suelta el recurso en su celda; nadie se mueve y no cuesta nada
    if isinstance(action, Tackle):
        dropped = state.position_of(action.target)
        return (
            GameState(
                positions=state.positions,
                carrier=None,
                resource=dropped,
                turn=next_turn,
                turn_number=state.turn_number + 1,
            ),
            0.0,
        )
    # se crean las nuevas posiciones de todas las unidades
    positions = tuple(
        (uid, action.dest if uid == action.unit_id else pos) for uid, pos in state.positions
    )
    # se copia el estado del recurso quien lo lleva  y donde esta
    carrier, resource = state.carrier, state.resource
    # (1) Recoger el recurso al llegar a su celda
    if carrier is None and resource == action.dest:
        carrier, resource = action.unit_id, None
    # (2) la entrega (llegar a la propia base con el recurso) la detecta `winner`
    successor = GameState(
        positions=positions,
        carrier=carrier,
        resource=resource,
        turn=next_turn,
        turn_number=state.turn_number + 1,
    )
    return successor, board.cost_at(action.dest)


# funcion para expandir un estado en triples (accion, sucesor, costo) en orden de `legal_actions`
def successors(board: Board, state: GameState) -> list[tuple[Action, GameState, float]]:
    """Expand a state into (action, successor, cost) triples in `legal_actions` order.

    Purpose: single entry point used by every search algorithm.
    Preconditions: `state` belongs to `board`.
    Postconditions: order is deterministic; empty for terminal states.
    Complexity: O(U * 4 * U).
    AI usage: Yes. Claude Code (Sonnet 5.5) drafted the function.
    AI intervention: none after the draft.
    Student validation: tests/test_domain_rules.py (cost paid on entering the destination,
        deterministic and consistent successors) and tests/test_domain_state.py (case 6: same
        position, different state; immutability; equal states hash equal).
    """
    result: list[tuple[Action, GameState, float]] = []
    # por cada acción legal se calcula su sucesor y su costo
    for action in legal_actions(board, state):
        nxt, cost = apply(board, state, action)
        result.append((action, nxt, cost))
    return result
