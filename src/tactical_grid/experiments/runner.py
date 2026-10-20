"""Run one test of a scenario (modes `busqueda`, `adversarial`, `partida`) and report it.

Results use keys equivalent to Appendix B of the assignment so they are easy to compare and
reproduce (RF-38, RF-39). The command line in `__main__` is a thin wrapper over this module.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from tactical_grid.algorithms.adversarial import (
    ActionOrder,
    AdversarialResult,
    alpha_beta,
    minimax,
)
from tactical_grid.algorithms.adversarial_dynamic import (
    DynamicAdversarialResult,
    alpha_beta_dynamic,
    minimax_dynamic,
)
from tactical_grid.algorithms.common import PathProblem, SearchResult, make_problem
from tactical_grid.algorithms.heuristics import Heuristic, manhattan, obstacle_aware
from tactical_grid.algorithms.informed import a_star, beam_search
from tactical_grid.algorithms.uninformed import bfs, dfs, ucs
from tactical_grid.algorithms.utility import UtilityWeights, make_utility
from tactical_grid.algorithms.utility_dynamic import make_dynamic_utility
from tactical_grid.domain.dynamic import initial_dynamic_state
from tactical_grid.domain.model import Position, Side
from tactical_grid.experiments.game import play_game
from tactical_grid.experiments.verifier import (
    VerificationReport,
    verify_adversarial,
    verify_adversarial_dynamic,
    verify_search,
)
from tactical_grid.scenario.loader import Scenario

# modos de prueba permitidos
MODES = ("busqueda", "adversarial", "partida")
# nombres alternativos de algoritmos que se convierten al nombre oficial
_ALIASES = {"A*": "A_STAR", "A_ESTRELLA": "A_STAR", "ASTAR": "A_STAR", "BEAM_SEARCH": "BEAM"}
# algoritmos de búsqueda de camino y algoritmos adversariales disponibles
SEARCH_ALGORITHMS = ("BFS", "DFS", "UCS", "A_STAR", "BEAM")
ADVERSARIAL_ALGORITHMS = ("MINIMAX", "ALPHA_BETA")
# variantes de reglas del juego adversarial
VARIANTS = ("base", "dinamica")
# formas de jugar el modo partida: IA contra IA o una persona contra la IA
PLAYS = ("auto", "humano")
# heurísticas disponibles por nombre (H1 = Manhattan, H2 = con obstáculos)
_HEURISTICS: dict[str, Callable[[PathProblem], Heuristic]] = {
    "H1": manhattan,
    "MANHATTAN": manhattan,
    "H2": obstacle_aware,
    "OBSTACLE_AWARE": obstacle_aware,
}
# algoritmos sin heurística, buscados por nombre
_UNINFORMED = {"BFS": bfs, "DFS": dfs, "UCS": ucs}


# Excepción para cuando la prueba no se puede ejecutar (opción faltante o desconocida)
class RunError(Exception):
    """The requested test cannot run (missing or unknown option)."""


# Opciones de la ejecución; lo que quede en None se toma de la sección `prueba` del escenario
@dataclass(frozen=True)
class RunOptions:
    """Overrides; any field left as None falls back to the scenario's `prueba` section."""

    mode: str | None = None
    algorithm: str | None = None
    heuristic: str | None = None
    k: int | None = None
    depth: int | None = None
    order: str | None = None
    unit: str | None = None
    goal: Position | None = None
    verify: bool = False
    variant: str | None = None  # base o dinamica; si falta se usa `juego.variante` del escenario
    play: str | None = None  # partida: auto (IA contra IA) o humano; si falta solo se describe
    side: str | None = None  # partida con humano: bando de la persona (A por defecto)


# Pasa un nombre a su forma oficial: mayúsculas, guiones bajos y sin alias
def canonical(name: str) -> str:
    key = name.strip().upper().replace("-", "_").replace(" ", "_")
    return _ALIASES.get(key, key)


# Ejecuta la prueba configurada y devuelve el reporte
def run(scenario: Scenario, options: RunOptions) -> dict[str, Any]:
    """Execute the configured test and return a JSON-serializable report.

    Purpose: single entry point that picks the mode, resolves options against the scenario's
        `prueba` section (the explicit options win) and runs the algorithm.
    Preconditions: `scenario` was loaded and validated.
    Postconditions: raises RunError, never a bare KeyError, for missing or unknown options.
        With `options.verify` the report carries the RF-42 checks that apply to the mode.
    Complexity: that of the chosen algorithm.
    AI usage: Yes. Claude Code (Sonnet 5.5) drafted the module.
    AI intervention: none after the draft; option names are the team's G10 proposal.
    Student validation: tests/test_runner.py checks that the JSON prueba section drives the
        search, the CLI overrides, invalid options, scenario errors and the 15x15 and 20x20
        scenarios.
    """
    config = scenario.test_config
    # la opción explícita gana; si falta se usa la del escenario
    mode = (options.mode or config.mode or "").lower()
    if mode not in MODES:
        raise RunError(f"mode must be one of {MODES}, got {mode!r}")
    if options.play and mode != "partida":
        raise RunError("--play only applies to mode partida")
    # en modo partida se describe el juego cargado, o se juega completo si se pidió `play`
    if mode == "partida":
        return _run_game(scenario, options) if options.play else describe(scenario)
    name = canonical(options.algorithm or config.algorithm or "")
    if mode == "busqueda":
        return _run_search(scenario, options, name)
    return _run_adversarial(scenario, options, name)


# Resumen del juego cargado (modo partida)
def describe(scenario: Scenario) -> dict[str, Any]:
    """Mode `partida`: summary of the loaded game (the GUI continues it turn by turn)."""
    board, state = scenario.board, scenario.initial_state
    return {
        "modo": "partida",
        "mapa": [board.rows, board.cols],
        "turno": state.turn.value,
        "portador": state.carrier,
        "recurso": _cell(state.resource) if state.resource else None,
        "unidades": {
            uid: {"bando": board.unit_sides[uid].value, "celda": _cell(pos)}
            for uid, pos in state.positions
        },
        "bases": {side.value: _cell(pos) for side, pos in board.bases.items()},
        "limite_turnos": board.turn_limit,
    }


# Ejecuta una búsqueda de camino (BFS, DFS, UCS, A* o Beam) y arma su reporte
def _run_search(scenario: Scenario, options: RunOptions, name: str) -> dict[str, Any]:
    config = scenario.test_config
    if name not in SEARCH_ALGORITHMS:
        raise RunError(f"search algorithm must be one of {SEARCH_ALGORITHMS}, got {name!r}")
    # unidad y meta: la opción explícita gana sobre la del escenario
    unit = options.unit or config.start_unit
    goal = options.goal or config.goal
    if unit is None or goal is None:
        raise RunError("a search needs a start unit and a goal (prueba.unidad_inicio/objetivo)")
    if unit not in scenario.board.unit_sides:
        raise RunError(f"unknown unit {unit!r}")
    if not scenario.board.is_passable(goal):
        raise RunError(f"goal {_cell(goal)} is outside the map or not passable")
    problem = make_problem(scenario.board, scenario.initial_state, unit, goal)

    # los algoritmos sin heurística se ejecutan directo
    if name in _UNINFORMED:
        result = _UNINFORMED[name](problem)
    else:
        # A* y Beam necesitan una heurística (por defecto H1)
        heuristic_name = canonical(options.heuristic or config.heuristic or "H1")
        factory = _HEURISTICS.get(heuristic_name)
        if factory is None:
            raise RunError(
                f"heuristic must be one of {sorted(_HEURISTICS)}, got {heuristic_name!r}"
            )
        heuristic = factory(problem)
        if name == "A_STAR":
            result = a_star(problem, heuristic, f"A_STAR_{heuristic_name}")
        else:
            # Beam además necesita el ancho k del haz
            k = options.k if options.k is not None else config.beam_width
            if k is None:
                raise RunError("BEAM needs a width k (prueba.k or --k)")
            if k < 1:
                raise RunError(f"beam width k must be at least 1, got {k}")
            result = beam_search(problem, heuristic, k, f"BEAM_K{k}")
    report = _search_report(result)
    # si se pidió verificar, se agregan los chequeos al reporte
    if options.verify:
        report["verificacion"] = _checks(verify_search(problem, result))
    return report


# Valida y resuelve algoritmo, profundidad, orden y variante (la opción explícita gana)
def _adversarial_settings(
    scenario: Scenario, options: RunOptions, name: str
) -> tuple[int, str, str]:
    config = scenario.test_config
    if name not in ADVERSARIAL_ALGORITHMS:
        raise RunError(
            f"adversarial algorithm must be one of {ADVERSARIAL_ALGORITHMS}, got {name!r}"
        )
    depth = options.depth if options.depth is not None else config.minimax_depth
    if depth is None:
        raise RunError("Minimax needs a depth (juego.profundidad_maxima_minimax or --depth)")
    if depth < 1:
        raise RunError(f"depth must be at least 1, got {depth}")
    order = (options.order or config.action_order or "default").lower()
    if order not in ("default", "reversed"):
        raise RunError(f"action order must be default or reversed, got {order!r}")
    variant = (options.variant or scenario.variant).lower()
    if variant not in VARIANTS:
        raise RunError(f"variant must be one of {VARIANTS}, got {variant!r}")
    return depth, order, variant


# Juega la partida completa (modo partida con --play): IA contra IA o persona contra la IA
def _run_game(scenario: Scenario, options: RunOptions) -> dict[str, Any]:
    play = (options.play or "").lower()
    if play not in PLAYS:
        raise RunError(f"play must be one of {PLAYS}, got {play!r}")
    # la IA usa el algoritmo pedido, el del escenario si es adversarial, o alfa-beta
    name = canonical(options.algorithm or "")
    if not name:
        configured = canonical(scenario.test_config.algorithm or "")
        name = configured if configured in ADVERSARIAL_ALGORITHMS else "ALPHA_BETA"
    depth, order, variant = _adversarial_settings(scenario, options, name)
    action_order: ActionOrder = "reversed" if order == "reversed" else "default"
    human: Side | None = None
    if play == "humano":
        side = (options.side or "A").upper()
        if side not in ("A", "B"):
            raise RunError(f"side must be A or B, got {side!r}")
        human = Side(side)
    elif options.side:
        raise RunError("--side only applies with --play humano")
    return play_game(
        scenario,
        name,
        depth,
        action_order,
        variant == "dinamica",
        human,
        write=print if human else (lambda _text: None),
    )


# Ejecuta Minimax o alfa-beta sobre el estado inicial y arma su reporte
def _run_adversarial(scenario: Scenario, options: RunOptions, name: str) -> dict[str, Any]:
    depth, order, variant = _adversarial_settings(scenario, options, name)
    board, state = scenario.board, scenario.initial_state
    # la utilidad se mide desde el lado que tiene el turno, con los pesos del escenario
    weights = UtilityWeights.from_mapping(scenario.utility_weights)
    utility = make_utility(board, state.turn, weights)
    action_order: ActionOrder = "reversed" if order == "reversed" else "default"
    if variant == "dinamica":
        dynamic_state = initial_dynamic_state(state)
        dynamic_algorithm = minimax_dynamic if name == "MINIMAX" else alpha_beta_dynamic
        rules = scenario.dynamic_rules
        dynamic_utility = make_dynamic_utility(board, state.turn, weights)
        dynamic_result = dynamic_algorithm(
            board, dynamic_state, depth, dynamic_utility, rules, action_order, record=options.verify
        )
        report = _adversarial_report(dynamic_result, depth, order)
        report["variante"] = "dinamica"
        if options.verify:
            report["verificacion"] = _checks(
                verify_adversarial_dynamic(board, dynamic_state, dynamic_result)
            )
        return report
    algorithm = minimax if name == "MINIMAX" else alpha_beta
    # con verify se registran las acciones consideradas para poder revisarlas después
    result = algorithm(board, state, depth, utility, action_order, record=options.verify)
    report = _adversarial_report(result, depth, order)
    if options.verify:
        report["verificacion"] = _checks(verify_adversarial(board, state, result))
    return report


# Posición como lista [fila, columna] para el reporte
def _cell(pos: Position) -> list[int]:
    return [pos.row, pos.col]


# Reporte (con claves en español) del resultado de una búsqueda de camino
def _search_report(result: SearchResult) -> dict[str, Any]:
    return {
        "algoritmo": result.algorithm,
        "exito": result.success,
        "camino": [_cell(cell) for cell in result.path],
        "costo": result.cost,
        "longitud": result.length,
        "estados_generados": result.generated,
        "estados_expandidos": result.expanded,
        "maximo_frontera": result.max_frontier,
        "tiempo_segundos": result.time_seconds,
    }


# Reporte (con claves en español) del resultado de una decisión adversarial
def _adversarial_report(
    result: AdversarialResult | DynamicAdversarialResult, depth: int, order: str
) -> dict[str, Any]:
    return {
        "algoritmo": result.algorithm,
        "profundidad": depth,
        "orden_acciones": order,
        "accion": None if result.action is None else repr(result.action),
        "valor": result.value,
        "nodos_generados": result.generated,
        "nodos_evaluados": result.evaluated,
        "nodos_podados": result.pruned,
        "profundidad_alcanzada": result.depth_reached,
        "valores_raiz": [
            {"accion": repr(action), "valor": value} for action, value in result.root_values
        ],
        "tiempo_segundos": result.time_seconds,
    }


# Convierte los chequeos del verificador a una lista de diccionarios para el reporte
def _checks(report: VerificationReport) -> list[dict[str, Any]]:
    return [
        {"chequeo": check.name, "ok": check.passed, "detalle": check.detail}
        for check in report.checks
    ]
