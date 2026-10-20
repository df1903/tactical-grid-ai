"""Solution verifier (RF-42): checks 1 to 5 for single-unit searches, check 6 for Minimax."""

import math
from dataclasses import dataclass

from tactical_grid.algorithms.adversarial import AdversarialResult
from tactical_grid.algorithms.adversarial_dynamic import DynamicAdversarialResult
from tactical_grid.algorithms.common import PathProblem, SearchResult
from tactical_grid.domain import dynamic
from tactical_grid.domain.model import Board, GameState, Position
from tactical_grid.domain.rules import legal_actions


# Resultado de un chequeo individual: nombre, si pasó y un detalle
@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


# Conjunto de chequeos hechos al resultado de un algoritmo
@dataclass(frozen=True)
class VerificationReport:
    algorithm: str
    checks: tuple[Check, ...]

    # El reporte está bien solo si todos los chequeos pasaron
    @property
    def ok(self) -> bool:
        return all(check.passed for check in self.checks)


# Verifica un resultado de búsqueda repitiendo su camino con las reglas del dominio (chequeos 1 a 5)
def verify_search(problem: PathProblem, result: SearchResult) -> VerificationReport:
    """Replay the reported path on the domain rules and run RF-42 checks 1 to 5.

    Purpose: independent check that a search result is a legal, consistent solution.
    Preconditions: `problem` is the one the algorithm solved.
    Postconditions: never raises on a malformed path; each check reports why it failed.
        A result without solution has no path to verify and yields an empty report.
    Complexity: O(L * U) for a path of L cells and U units.
    AI usage: Yes. Claude Code (Sonnet 5.5) drafted the function from RF-42.
    AI intervention: none after the draft.
    Student validation: tests/test_verifier.py checks that every algorithm's result passes and
        that a teleport, a path through a wall, a wrong cost and a path not ending at the goal are
        rejected.
    """
    # sin solución no hay camino que verificar
    if not result.success:
        return VerificationReport(result.algorithm, ())

    board = problem.board
    start = problem.initial.position_of(problem.unit_id)
    path = result.path

    # estados y costo que salen de repetir el camino paso a paso
    states: list[GameState] = [problem.initial]
    replay_cost = 0.0
    bad_move: str | None = None
    if not path or path[0] != start:
        bad_move = f"path does not start at the unit's cell {start}"
    else:
        for step, cell in enumerate(path[1:], start=1):
            # se busca entre los sucesores uno que lleve a la siguiente celda del camino
            match = [
                (nxt, cost)
                for nxt, cost in problem.expand(states[-1])
                if nxt.position_of(problem.unit_id) == cell
            ]
            # si no hay, el movimiento es ilegal y se corta la repetición
            if not match:
                bad_move = f"step {step}: {states[-1].position_of(problem.unit_id)} -> {cell}"
                break
            states.append(match[0][0])
            replay_cost += match[0][1]

    # celdas del camino que no son transitables
    walls = [cell for cell in path if not board.is_passable(cell)]
    # pasos cuyo estado es inválido (unidades superpuestas o sobre obstáculos)
    invalid = [i for i, state in enumerate(states) if not _valid_state(problem, state)]
    reported = result.cost
    final = path[-1] if path else None

    # los 5 chequeos: movimientos, obstáculos, costo, meta y estados válidos
    checks = (
        Check(
            "valid moves",
            bad_move is None,
            "every step is a legal action" if bad_move is None else f"illegal move at {bad_move}",
        ),
        Check(
            "no obstacles",
            not walls,
            "no cell is blocked" if not walls else f"blocked cells in path: {walls}",
        ),
        Check(
            "cost matches",
            bad_move is None and math.isclose(replay_cost, reported),
            f"reported {reported}, replayed {replay_cost}",
        ),
        Check(
            "goal reached",
            final == problem.goal,
            f"final cell {final}, goal {problem.goal}",
        ),
        Check(
            "no invalid states",
            not invalid,
            "all replayed states are valid"
            if not invalid
            else f"invalid states at steps {invalid}",
        ),
    )
    return VerificationReport(result.algorithm, checks)


# Un estado es válido si no hay dos unidades en la misma celda y todas están en celdas transitables
def _valid_state(problem: PathProblem, state: GameState) -> bool:
    cells: list[Position] = [pos for _, pos in state.positions]
    # celdas repetidas significan unidades superpuestas
    if len(set(cells)) != len(cells):
        return False
    return all(problem.board.is_passable(cell) for cell in cells)


# Verifica que toda acción que consideró Minimax sea legal (chequeo 6)
def verify_adversarial(
    board: Board, state: GameState, result: AdversarialResult
) -> VerificationReport:
    """RF-42 check 6: every action Minimax considered is legal under the game rules.

    Purpose: independent check that the adversarial search only expands legal actions.
    Preconditions: `result` was produced from `state` with `record=True`, so that
        `result.considered` lists every (state, action) pair the search tried.
    Postconditions: never raises; also checks that the selected action was among the legal
        root actions. A result without recorded actions fails the first check.
    Complexity: O(N * U^2) for N recorded actions and U units.
    AI usage: Yes. Claude Code (Sonnet 5.5) drafted the function from RF-42.
    AI intervention: none after the draft.
    Student validation: tests/test_adversarial.py checks that it rejects an illegal action and
        requires recorded actions.
    """
    # posiciones de las acciones consideradas que no eran legales en su estado
    illegal = [
        index
        for index, (node, action) in enumerate(result.considered)
        if action not in legal_actions(board, node)
    ]
    # si no se registró nada (y había acción) no se puede comprobar
    recorded = bool(result.considered) or result.action is None
    # la acción elegida debe estar entre las legales de la raíz
    root_legal = result.action is None or result.action in legal_actions(board, state)
    checks = (
        Check(
            "legal actions",
            recorded and not illegal,
            "every considered action is legal"
            if recorded and not illegal
            else (
                f"illegal actions at positions {illegal[:5]}"
                if illegal
                else "no considered actions were recorded (run with record=True)"
            ),
        ),
        Check(
            "selected action legal",
            root_legal,
            f"selected {result.action}",
        ),
    )
    return VerificationReport(result.algorithm, checks)


# Verifica que toda acción que consideró la búsqueda dinámica sea legal con sus reglas (chequeo 6)
def verify_adversarial_dynamic(
    board: Board, state: dynamic.DynamicState, result: DynamicAdversarialResult
) -> VerificationReport:
    """RF-42 check 6 for the dynamic variant: every considered action is legal.

    Purpose: independent check that the search never moves a unit in recovery or steals from an
        immune carrier.
    Preconditions: `result` was produced from `state` with `record=True`.
    Postconditions: never raises; also checks that the selected action was legal at the root.
    Complexity: O(N * U^2) for N recorded actions and U units.
    AI usage: Yes. Claude Code (Sonnet 5.5) drafted the function from the approved plan.
    AI intervention: none after the draft.
    Student validation: tests/test_adversarial_dynamic.py checks that it accepts the search and
        rejects a move of a unit in recovery.
    """
    illegal = [
        index
        for index, (node, action) in enumerate(result.considered)
        if action not in dynamic.legal_actions(board, node)
    ]
    recorded = bool(result.considered) or result.action is None
    root_legal = result.action is None or result.action in dynamic.legal_actions(board, state)
    checks = (
        Check(
            "legal actions",
            recorded and not illegal,
            "every considered action is legal"
            if recorded and not illegal
            else (
                f"illegal actions at positions {illegal[:5]}"
                if illegal
                else "no considered actions were recorded (run with record=True)"
            ),
        ),
        Check("selected action legal", root_legal, f"selected {result.action}"),
    )
    return VerificationReport(result.algorithm, checks)
