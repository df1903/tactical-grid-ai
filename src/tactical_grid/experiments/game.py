"""Mode `partida`: play a full game from the loaded scenario, AI vs AI or a human vs the AI.

Both sides play under the same rules and the same algorithm, depth and weights: MAX and MIN are
only the roles inside each decision's tree. The human picks a legal action by its number.
"""

from collections.abc import Callable
from typing import Any

from tactical_grid.algorithms.adversarial import ActionOrder, alpha_beta, minimax
from tactical_grid.algorithms.adversarial_dynamic import alpha_beta_dynamic, minimax_dynamic
from tactical_grid.algorithms.utility import UtilityWeights, make_utility
from tactical_grid.algorithms.utility_dynamic import make_dynamic_utility
from tactical_grid.domain import dynamic
from tactical_grid.domain.model import Action, GameState, Move, Position, Side
from tactical_grid.domain.rules import apply, is_terminal, legal_actions, skip_turn, winner
from tactical_grid.scenario.loader import Scenario

Reader = Callable[[str], str]
Writer = Callable[[str], None]


# Se lanza cuando la persona abandona la partida (escribe q o se cierra la entrada)
class GameAbandoned(Exception):
    """The human quit the game."""


# Estado de una partida en curso; con la variante dinámica lleva además los contadores
class _Session:
    def __init__(self, scenario: Scenario, dynamic_variant: bool) -> None:
        self.scenario = scenario
        self.board = scenario.board
        self.state = scenario.initial_state
        self.dyn = dynamic.initial_dynamic_state(self.state) if dynamic_variant else None

    # La partida terminó: hay ganador o se agotaron los turnos
    def over(self) -> bool:
        return is_terminal(self.board, self.state)

    # Acciones legales del bando con el turno según la variante
    def legal(self) -> list[Action]:
        if self.dyn is not None:
            return dynamic.legal_actions(self.board, self.dyn)
        return legal_actions(self.board, self.state)

    # Aplica una acción legal según la variante
    def play(self, action: Action) -> None:
        if self.dyn is not None:
            self.dyn = dynamic.apply(self.board, self.dyn, action, self.scenario.dynamic_rules)
            self.state = self.dyn.base
        else:
            self.state, _ = apply(self.board, self.state, action)

    # Pasa el turno del bando que no tiene acciones legales
    def skip(self) -> None:
        if self.dyn is not None:
            self.dyn = dynamic.pass_turn(self.board, self.dyn)
            self.state = self.dyn.base
        else:
            self.state = skip_turn(self.state)

    # Decisión del algoritmo para el bando con el turno: MAX es quien mueve ahora
    def decide(self, name: str, depth: int, order: ActionOrder) -> tuple[Action | None, float, int]:
        weights = UtilityWeights.from_mapping(self.scenario.utility_weights)
        if self.dyn is not None:
            dyn_utility = make_dynamic_utility(self.board, self.state.turn, weights)
            dyn_algorithm = minimax_dynamic if name == "MINIMAX" else alpha_beta_dynamic
            dyn_result = dyn_algorithm(
                self.board, self.dyn, depth, dyn_utility, self.scenario.dynamic_rules, order
            )
            return dyn_result.action, dyn_result.value, dyn_result.generated
        utility = make_utility(self.board, self.state.turn, weights)
        algorithm = minimax if name == "MINIMAX" else alpha_beta
        result = algorithm(self.board, self.state, depth, utility, order)
        return result.action, result.value, result.generated


# Texto corto de una acción: "A1 -> (2, 3)" para un movimiento, "A1 placa a B1" para un placaje
def describe_action(action: Action) -> str:
    if isinstance(action, Move):
        return f"{action.unit_id} -> ({action.dest.row}, {action.dest.col})"
    return f"{action.unit_id} placa a {action.target}"


# Acción como diccionario para el reporte JSON
def _action_report(action: Action) -> dict[str, Any]:
    if isinstance(action, Move):
        return {"unidad": action.unit_id, "destino": [action.dest.row, action.dest.col]}
    return {"unidad": action.unit_id, "placa": action.target}


# Dibuja el mapa en texto: terreno (inicial del nombre), unidades, bases y recurso
def render(session: _Session) -> str:
    board, state = session.board, session.state
    width = max(4, max(len(uid) for uid in board.unit_sides) + 2)
    letters: dict[str, str] = {}
    for name, terrain in board.terrains.items():
        letters[name] = name[0].lower() if terrain.passable else "#"
    units = {pos: uid for uid, pos in state.positions}
    lines = ["    " + "".join(str(col % 100).ljust(width) for col in range(board.cols))]
    for row in range(board.rows):
        cells: list[str] = []
        for col in range(board.cols):
            there = Position(row, col)
            if there in units:
                uid = units[there]
                text = uid + ("*" if uid == state.carrier else "")
            elif state.resource == there:
                text = "$"
            elif board.bases[Side.A] == there:
                text = "<A>"
            elif board.bases[Side.B] == there:
                text = "<B>"
            else:
                text = letters[board.grid[row][col]]
            cells.append(text.ljust(width))
        lines.append(f"{row:>3} " + "".join(cells))
    legend = ", ".join(
        f"{letters[name]}={name} ({terrain.cost:g})" if terrain.passable else f"#={name}"
        for name, terrain in board.terrains.items()
    )
    lines.append(f"Leyenda: {legend}; $=recurso, *=portador, <A>/<B>=bases")
    if session.dyn is not None:
        stuck = [f"{uid}({turns})" for uid, turns in session.dyn.recovery if turns > 0]
        if stuck:
            lines.append("Inmovilizadas (turnos propios): " + ", ".join(stuck))
        if session.dyn.immunity > 0:
            lines.append(f"Portador inmune {session.dyn.immunity} turno(s) del rival")
    return "\n".join(lines)


# Pide a la persona una de las acciones legales por su número
def _ask(actions: list[Action], read: Reader, write: Writer) -> Action:
    for number, action in enumerate(actions, start=1):
        write(f"  {number:>2}) {describe_action(action)}")
    while True:
        try:
            text = read("Tu jugada (número, q para abandonar): ").strip().lower()
        except EOFError:
            raise GameAbandoned from None
        if text in ("q", "salir"):
            raise GameAbandoned
        if text.isdigit() and 1 <= int(text) <= len(actions):
            return actions[int(text) - 1]
        write(f"Opción no válida: escribe un número entre 1 y {len(actions)}.")


# Juega la partida completa y devuelve el reporte
def play_game(
    scenario: Scenario,
    algorithm: str,
    depth: int,
    order: ActionOrder,
    dynamic_variant: bool,
    human: Side | None = None,
    read: Reader = input,
    write: Writer = print,
) -> dict[str, Any]:
    """Play the loaded game to the end: AI for every side except `human` (None = AI vs AI).

    Purpose: let the team run a whole game from the terminal, with a person on one side if wanted.
    Preconditions: `algorithm` is MINIMAX or ALPHA_BETA and `depth` >= 1 (the runner checks them).
    Postconditions: the loop ends at a delivery, at the turn limit or when the human quits; a
        side with no legal action passes. Both sides use the same rules, algorithm, depth and
        weights. `ganador` is the winning side, or None for a draw or an abandoned game.
    Complexity: one decision per turn, at most `juego.limite_turnos` turns.
    AI usage: Yes. Claude Code (Sonnet 5.5) drafted the module on 2026-10-19.
    AI intervention: none after the draft.
    Student validation: tests/test_game.py checks AI vs AI reaches a terminal state with legal
        moves only, the human can play, pick by number, retry an invalid option and quit.
    """
    session = _Session(scenario, dynamic_variant)
    moves: list[dict[str, Any]] = []
    abandoned = False
    while not session.over():
        state = session.state
        side, number = state.turn, state.turn_number + 1
        is_human = side is human
        who = "persona" if is_human else "IA"
        entry: dict[str, Any] = {"turno": number, "bando": side.value, "jugador": who}
        if is_human:
            write("\n" + render(session))
            write(f"\nTurno {number}/{session.board.turn_limit}: juegas tú ({side.value})")
        actions = session.legal()
        if not actions:
            entry["accion"] = None
            session.skip()
            if is_human:
                write("No tienes jugadas legales: pasas el turno.")
        elif is_human:
            try:
                action = _ask(actions, read, write)
            except GameAbandoned:
                abandoned = True
                break
            entry["accion"] = _action_report(action)
            session.play(action)
        else:
            action_ai, value, generated = session.decide(algorithm, depth, order)
            assert action_ai is not None  # there are legal actions, so the search picks one
            entry.update(accion=_action_report(action_ai), valor=value, nodos_generados=generated)
            session.play(action_ai)
            if human is not None:
                write(f"\nTurno {number}: la IA ({side.value}) juega {describe_action(action_ai)}")
        moves.append(entry)
    won = winner(session.board, session.state)
    if human is not None:
        write("\n" + render(session))
        if abandoned:
            write("\nPartida abandonada.")
        elif won is None:
            write("\nEmpate: se agotaron los turnos.")
        else:
            write("\n" + ("¡Ganaste!" if won is human else f"Ganó la IA ({won.value})."))
    return {
        "modo": "partida",
        "variante": "dinamica" if dynamic_variant else "base",
        "algoritmo": algorithm,
        "profundidad": depth,
        "orden": order,
        "jugadores": {
            side.value: "persona" if side is human else "IA" for side in (Side.A, Side.B)
        },
        "terminada": session.over(),
        "abandonada": abandoned,
        "ganador": won.value if won else None,
        "turnos_jugados": session.state.turn_number,
        "jugadas": moves,
        "estado_final": _final_state(session.state),
    }


# Estado final resumido para el reporte
def _final_state(state: GameState) -> dict[str, Any]:
    return {
        "turno": state.turn.value,
        "portador": state.carrier,
        "recurso": [state.resource.row, state.resource.col] if state.resource else None,
        "unidades": {uid: [pos.row, pos.col] for uid, pos in state.positions},
    }
