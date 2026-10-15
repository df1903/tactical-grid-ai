"""Game rules: legal actions, transitions, costs and terminal conditions."""

from dataclasses import replace

from tactical_grid.domain.model import Action, Board, GameState, Move, Position, Side, Wait


def winner(board: Board, state: GameState) -> Side | None:
    """Side that delivered the resource to its own base, or None."""
    if state.carrier is None:
        return None
    side = board.unit_sides[state.carrier]
    if state.position_of(state.carrier) == board.bases[side]:
        return side
    return None


def is_draw(board: Board, state: GameState) -> bool:
    return winner(board, state) is None and state.turn_number >= board.turn_limit


def is_terminal(board: Board, state: GameState) -> bool:
    return winner(board, state) is not None or state.turn_number >= board.turn_limit


def legal_actions(board: Board, state: GameState) -> list[Action]:
    """List the actions available to the side whose turn it is.

    Purpose: enumerate deterministic legal moves (4 directions) and waits per unit.
    Preconditions: `state` belongs to `board` (same units and bounds).
    Postconditions: empty if the game is over; otherwise, per active unit (sorted by
        id), moves to free passable in-map cells that are not the rival base, then Wait.
    Complexity: O(U * 4 * U) with U units (occupancy lookup is linear in U).
    AI usage: Claude Code (Sonnet 5.5) drafted the function from `rules.md`.
    AI intervention: none after the draft; rules were decided by the team on 2026-10-14.
    Student validation: pending cross-review by the other team member.
    """
    if is_terminal(board, state):
        return []
    rival_base = board.bases[state.turn.opponent]
    actions: list[Action] = []
    for uid, pos in state.positions:
        if board.unit_sides[uid] is not state.turn:
            continue
        for dest in pos.neighbors():
            if board.is_passable(dest) and dest != rival_base and state.unit_at(dest) is None:
                actions.append(Move(uid, dest))
        actions.append(Wait(uid))
    return actions


def apply(board: Board, state: GameState, action: Action) -> tuple[GameState, float]:
    """Apply a legal action and return the successor state and the step cost.

    Purpose: deterministic transition, including pickup, delivery and interception.
    Preconditions: `action` is in `legal_actions(board, state)`.
    Postconditions: turn passes to the opponent and `turn_number` grows by one. Move
        costs the destination terrain cost (paid on entering); Wait costs 0. Order:
        (1) pickup on arrival at the resource cell, (2) delivery at own base wins and
        skips interception, (3) any rival adjacent to the carrier drops the resource
        on the carrier's cell (no transfer). Wait never picks up.
    Complexity: O(U).
    AI usage: Claude Code (Sonnet 5.5) drafted the function from `rules.md`.
    AI intervention: none after the draft; Wait cost 0 is an assumption in decisions.md.
    Student validation: pending cross-review by the other team member.
    """
    next_turn = state.turn.opponent
    if isinstance(action, Wait):
        return replace(state, turn=next_turn, turn_number=state.turn_number + 1), 0.0

    positions = tuple(
        (uid, action.dest if uid == action.unit_id else pos) for uid, pos in state.positions
    )
    carrier, resource = state.carrier, state.resource
    if carrier is None and resource == action.dest:
        carrier, resource = action.unit_id, None
    if carrier is not None:
        carrier_pos = dict(positions)[carrier]
        carrier_side = board.unit_sides[carrier]
        delivered = carrier_pos == board.bases[carrier_side]
        if not delivered and _rival_adjacent(board, positions, carrier_side, carrier_pos):
            carrier, resource = None, carrier_pos
    successor = GameState(
        positions=positions,
        carrier=carrier,
        resource=resource,
        turn=next_turn,
        turn_number=state.turn_number + 1,
    )
    return successor, board.cost_at(action.dest)


def _rival_adjacent(
    board: Board,
    positions: tuple[tuple[str, Position], ...],
    side: Side,
    pos: Position,
) -> bool:
    return any(
        board.unit_sides[uid] is not side and upos.is_adjacent(pos) for uid, upos in positions
    )


def successors(board: Board, state: GameState) -> list[tuple[Action, GameState, float]]:
    """Expand a state into (action, successor, cost) triples in `legal_actions` order.

    Purpose: single entry point used by every search algorithm.
    Preconditions: `state` belongs to `board`.
    Postconditions: order is deterministic; empty for terminal states.
    Complexity: O(U * 4 * U).
    AI usage: Claude Code (Sonnet 5.5) drafted the function.
    AI intervention: none after the draft.
    Student validation: pending cross-review by the other team member.
    """
    result: list[tuple[Action, GameState, float]] = []
    for action in legal_actions(board, state):
        nxt, cost = apply(board, state, action)
        result.append((action, nxt, cost))
    return result
