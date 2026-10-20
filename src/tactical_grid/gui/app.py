"""Interfaz gráfica de TacticalGrid (tkinter): búsqueda de camino, decisión adversarial y partida.

`python -m tactical_grid.gui [escenario.json]` abre la ventana. Arriba se elige el escenario JSON
y el algoritmo; al cambiar de algoritmo, el panel «Parámetros» se reconstruye con los controles
propios de ese algoritmo. La unidad y la meta de las búsquedas salen de la sección `prueba`.

- BFS, DFS, UCS, A* y Beam: «Ejecutar» muestra el camino y «Animar» reproduce la expansión.
- Minimax y alfa-beta: «Ejecutar» muestra la mejor jugada del bando con el turno; «Aplicar
  jugada» la juega y deja que el rival responda con el mismo algoritmo. También se puede jugar
  a mano: clic en una unidad del bando con el turno y luego en una celda a la que pueda ir
  (o en el portador rival al que pueda placar); el rival responde solo.
- «Verificar» ejecuta las comprobaciones de RF-42 sobre el resultado.

Para añadir un algoritmo basta registrar un `AlgorithmSpec` en `SPECS`: el layout, los controles,
las métricas y el panel de traza ya están. Los algoritmos se usan tal cual (`algorithms.*`); el
orden de expansión se registra envolviendo el problema, sin tocarlos.
"""

import random
import sys
import tkinter as tk
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from tkinter import filedialog, ttk

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
from tactical_grid.domain import dynamic
from tactical_grid.domain.model import Action, GameState, Move, Position, Side
from tactical_grid.domain.rules import apply, is_terminal, legal_actions, skip_turn, winner
from tactical_grid.experiments.verifier import (
    VerificationReport,
    verify_adversarial,
    verify_adversarial_dynamic,
    verify_search,
)
from tactical_grid.scenario.loader import Scenario, ScenarioError, load_scenario

# Valores elegidos en el panel de parámetros: clave -> texto
Params = Mapping[str, str]


# Un parámetro de un algoritmo: `choice` (lista de (valor, etiqueta)) o `int` (número entero)
@dataclass(frozen=True)
class ParamSpec:
    key: str
    label: str
    kind: str  # "choice" | "int" | "float"
    default: str
    options: tuple[tuple[str, str], ...] = ()  # solo para "choice"
    minimum: float = 1  # solo para "int" y "float"
    maximum: float = 99  # solo para "int" y "float"


# Un algoritmo disponible en el selector, con los parámetros que muestra su panel
@dataclass(frozen=True)
class AlgorithmSpec:
    name: str
    run: Callable[[PathProblem, Params], SearchResult] | None = None  # búsqueda de camino
    params: tuple[ParamSpec, ...] = ()
    description: str = ""
    # decisión adversarial sobre el estado inicial completo (Minimax, alfa-beta)
    decide: Callable[[Scenario, GameState, Params, bool], AdversarialResult] | None = None
    # decisión de la variante dinámica: recibe el estado con los contadores de recuperación
    decide_dynamic: (
        Callable[[Scenario, dynamic.DynamicState, Params, bool], DynamicAdversarialResult] | None
    ) = None

    @property
    def adversarial(self) -> bool:
        return self.decide is not None or self.decide_dynamic is not None


# Heurísticas del selector: valor interno -> (etiqueta, fábrica)
HEURISTICS: dict[str, tuple[str, Callable[[PathProblem], Heuristic]]] = {
    "h1": ("h1 · Manhattan", manhattan),
    "h2": ("h2 · Con obstáculos", obstacle_aware),
}
HEURISTIC_PARAM = ParamSpec(
    "heuristic",
    "Heurística",
    "choice",
    "h1",
    options=tuple((key, label) for key, (label, _) in HEURISTICS.items()),
)


# Heurística elegida en el panel, construida para el problema (h1 si el valor no se conoce)
def _heuristic(problem: PathProblem, params: Params) -> tuple[str, Heuristic]:
    key = params.get("heuristic", "h1")
    _, factory = HEURISTICS.get(key, HEURISTICS["h1"])
    return key.upper(), factory(problem)


# Ancho del haz leído del panel; error legible si no es un entero >= 1
def _beam_width(params: Params) -> int:
    try:
        k = int(params.get("k", ""))
    except ValueError:
        raise ValueError("el ancho k del haz debe ser un entero") from None
    if k < 1:
        raise ValueError("el ancho k del haz debe ser al menos 1")
    return k


def _run_a_star(problem: PathProblem, params: Params) -> SearchResult:
    name, heuristic = _heuristic(problem, params)
    return a_star(problem, heuristic, f"A_STAR_{name}")


def _run_beam(problem: PathProblem, params: Params) -> SearchResult:
    _, heuristic = _heuristic(problem, params)
    k = _beam_width(params)
    return beam_search(problem, heuristic, k, f"BEAM_K{k}")


# Parámetros de Minimax y alfa-beta: profundidad, orden de acciones y pesos de la utilidad
ADVERSARIAL_PARAMS = (
    ParamSpec("depth", "Profundidad", "int", "3", minimum=1, maximum=12),
    ParamSpec(
        "order",
        "Orden de acciones",
        "choice",
        "default",
        options=(("default", "Por defecto"), ("reversed", "Inverso")),
    ),
    ParamSpec("w_delivery", "Peso: entrega", "float", "10.0", minimum=0, maximum=100),
    ParamSpec("w_carry", "Peso: recurso cargado", "float", "3.0", minimum=0, maximum=100),
    ParamSpec(
        "w_goal_distance", "Peso: distancia al objetivo", "float", "1.0", minimum=0, maximum=100
    ),
    ParamSpec(
        "w_rival_distance", "Peso: distancia del rival", "float", "0.5", minimum=0, maximum=100
    ),
    ParamSpec(
        "w_rival_progress", "Peso: progreso del rival", "float", "0.5", minimum=0, maximum=100
    ),
)


# Lee un número del panel; error legible si no se puede convertir
def _number(params: Params, key: str, label: str, cast: Callable[[str], float]) -> float:
    try:
        return cast(params.get(key, ""))
    except ValueError:
        raise ValueError(f"{label} debe ser un número") from None


# Decisión de Minimax o alfa-beta sobre el estado inicial; MAX es el lado que tiene el turno
def _decide(
    algorithm: Callable[..., AdversarialResult],
    scenario: Scenario,
    state: GameState,
    params: Params,
    record: bool,
) -> AdversarialResult:
    depth = int(_number(params, "depth", "la profundidad", int))
    if depth < 1:
        raise ValueError("la profundidad debe ser al menos 1")
    order: ActionOrder = "reversed" if params.get("order") == "reversed" else "default"
    weights = UtilityWeights(
        delivery=_number(params, "w_delivery", "el peso de entrega", float),
        carry=_number(params, "w_carry", "el peso de recurso cargado", float),
        goal_distance=_number(params, "w_goal_distance", "el peso de distancia al objetivo", float),
        rival_distance=_number(params, "w_rival_distance", "el peso de distancia del rival", float),
        rival_progress=_number(params, "w_rival_progress", "el peso de progreso del rival", float),
    )
    utility = make_utility(scenario.board, state.turn, weights)
    return algorithm(scenario.board, state, depth, utility, order, record=record)


# Decisión de la variante dinámica; las reglas (penalización, inmunidad) salen del escenario
def _decide_dynamic(
    algorithm: Callable[..., DynamicAdversarialResult],
    scenario: Scenario,
    state: dynamic.DynamicState,
    params: Params,
    record: bool,
) -> DynamicAdversarialResult:
    depth = int(_number(params, "depth", "la profundidad", int))
    if depth < 1:
        raise ValueError("la profundidad debe ser al menos 1")
    order: ActionOrder = "reversed" if params.get("order") == "reversed" else "default"
    weights = UtilityWeights(
        delivery=_number(params, "w_delivery", "el peso de entrega", float),
        carry=_number(params, "w_carry", "el peso de recurso cargado", float),
        goal_distance=_number(params, "w_goal_distance", "el peso de distancia al objetivo", float),
        rival_distance=_number(params, "w_rival_distance", "el peso de distancia del rival", float),
        rival_progress=_number(params, "w_rival_progress", "el peso de progreso del rival", float),
    )
    utility = make_dynamic_utility(scenario.board, state.turn, weights)
    return algorithm(
        scenario.board, state, depth, utility, scenario.dynamic_rules, order, record=record
    )


def _decide_minimax_dynamic(
    scenario: Scenario, state: dynamic.DynamicState, params: Params, record: bool
) -> DynamicAdversarialResult:
    return _decide_dynamic(minimax_dynamic, scenario, state, params, record)


def _decide_alpha_beta_dynamic(
    scenario: Scenario, state: dynamic.DynamicState, params: Params, record: bool
) -> DynamicAdversarialResult:
    return _decide_dynamic(alpha_beta_dynamic, scenario, state, params, record)


def _decide_minimax(
    scenario: Scenario, state: GameState, params: Params, record: bool
) -> AdversarialResult:
    return _decide(minimax, scenario, state, params, record)


def _decide_alpha_beta(
    scenario: Scenario, state: GameState, params: Params, record: bool
) -> AdversarialResult:
    return _decide(alpha_beta, scenario, state, params, record)


# Algoritmos del selector. Para sumar uno nuevo: añadir su AlgorithmSpec aquí.
SPECS: dict[str, AlgorithmSpec] = {
    "BFS": AlgorithmSpec(
        "BFS", lambda p, _: bfs(p), description="Anchura: óptimo en número de pasos."
    ),
    "DFS": AlgorithmSpec(
        "DFS",
        lambda p, _: dfs(p),
        params=(
            ParamSpec(
                "neighbor_order",
                "Orden de expansión de vecinos",
                "choice",
                "default",
                options=(("default", "Por defecto"), ("reversed", "Inverso")),
            ),
        ),
        description="Profundidad: encuentra un camino, no necesariamente el mejor.",
    ),
    "UCS": AlgorithmSpec(
        "UCS", lambda p, _: ucs(p), description="Costo uniforme: óptimo en costo."
    ),
    "A*": AlgorithmSpec(
        "A*",
        _run_a_star,
        params=(HEURISTIC_PARAM,),
        description="Expande el menor f = g + h; óptimo con heurística admisible.",
    ),
    "Beam": AlgorithmSpec(
        "Beam",
        _run_beam,
        params=(
            HEURISTIC_PARAM,
            ParamSpec("k", "Ancho del haz (k)", "int", "3", minimum=1, maximum=99),
        ),
        description="Por niveles, conserva solo los k mejores; memoria acotada, sin garantías.",
    ),
    "Minimax": AlgorithmSpec(
        "Minimax",
        params=ADVERSARIAL_PARAMS,
        decide=_decide_minimax,
        description="Decide el turno del bando que mueve, asumiendo un rival óptimo.",
    ),
    "Alfa-beta": AlgorithmSpec(
        "Alfa-beta",
        params=ADVERSARIAL_PARAMS,
        decide=_decide_alpha_beta,
        description="Misma decisión que Minimax, podando ramas que no la pueden cambiar.",
    ),
    "Minimax dinámico": AlgorithmSpec(
        "Minimax dinámico",
        params=ADVERSARIAL_PARAMS,
        decide_dynamic=_decide_minimax_dynamic,
        description="Minimax con recuperación por costo de terreno y placaje que roba el recurso.",
    ),
    "Alfa-beta dinámico": AlgorithmSpec(
        "Alfa-beta dinámico",
        params=ADVERSARIAL_PARAMS,
        decide_dynamic=_decide_alpha_beta_dynamic,
        description="Misma decisión que Minimax dinámico, podando ramas que no la pueden cambiar.",
    ),
}

# tamaño máximo del tablero en píxeles, pausa entre pasos y colores
CANVAS_PIXELS = 560
STEP_MILLISECONDS = 120
RESPONSE_MILLISECONDS = 700  # pausa antes de que el rival responda
# bando de la persona contra la IA: el que abre la partida (por defecto) o uno fijo
HUMAN_CHOICES = (("opener", "Bando que abre"), ("A", "Bando A"), ("B", "Bando B"))
SIDE_COLORS = {Side.A: "#1e6fd9", Side.B: "#d9381e"}
IMPASSABLE = "#3a3a3a"
EXPANDED = "#ffd27a"
PATH = "#8000c8"
GOAL = "#00a050"
RESOURCE = "#e0b000"
# colores de terreno de barato a caro; se reparten por el orden de costo de los tipos del escenario
TERRAIN_PALETTE = ("#e6d3a3", "#b5e07a", "#3f9b57", "#7a6aa8", "#b8693d", "#2f7fa8")


# Problema de camino que anota la celda de cada nodo que BFS expande, en orden
@dataclass(frozen=True)
class _RecordingProblem(PathProblem):
    expanded_cells: list[Position] = field(default_factory=list, compare=False)
    reverse_neighbors: bool = False

    # Anota la celda expandida y, si se pide, entrega los vecinos en orden inverso
    def expand(self, state: GameState) -> list[tuple[GameState, float]]:
        self.expanded_cells.append(state.position_of(self.unit_id))
        children = super().expand(state)
        return children[::-1] if self.reverse_neighbors else children


# Resultado de una corrida: unidad, meta, celdas expandidas en orden y resultado de la búsqueda
@dataclass(frozen=True)
class SearchTrace:
    unit: str
    goal: Position
    expanded_cells: tuple[Position, ...]
    result: SearchResult
    problem: PathProblem


# Corre el algoritmo elegido con la unidad y la meta de la sección `prueba` del escenario
def trace_search(scenario: Scenario, algorithm: str, params: Params | None = None) -> SearchTrace:
    config = scenario.test_config
    if config.start_unit is None or config.goal is None:
        raise ValueError("el escenario no define prueba.unidad_inicio / prueba.objetivo")
    if config.start_unit not in scenario.board.unit_sides:
        raise ValueError(f"unidad desconocida: {config.start_unit!r}")
    if not scenario.board.is_passable(config.goal):
        raise ValueError(f"la meta ({config.goal.row}, {config.goal.col}) no es transitable")
    base = make_problem(scenario.board, scenario.initial_state, config.start_unit, config.goal)
    run = SPECS[algorithm].run
    if run is None:
        raise ValueError(f"{algorithm} no es una búsqueda de camino")
    reverse = (params or {}).get("neighbor_order") == "reversed"
    problem = _RecordingProblem(
        base.board, base.initial, base.unit_id, base.goal, reverse_neighbors=reverse
    )
    result = run(problem, params or {})
    return SearchTrace(
        config.start_unit, config.goal, tuple(problem.expanded_cells), result, problem
    )


# Decisión adversarial del bando que mueve en `state` (por defecto, el estado inicial)
def trace_decision(
    scenario: Scenario,
    algorithm: str,
    params: Params | None = None,
    state: GameState | None = None,
    record: bool = False,
    dynamic_state: dynamic.DynamicState | None = None,
) -> AdversarialResult | DynamicAdversarialResult:
    spec = SPECS[algorithm]
    if spec.decide_dynamic is not None:
        start = dynamic_state or dynamic.initial_dynamic_state(state or scenario.initial_state)
        return spec.decide_dynamic(scenario, start, params or {}, record)
    if spec.decide is None:
        raise ValueError(f"{algorithm} no es un algoritmo adversarial")
    return spec.decide(scenario, state or scenario.initial_state, params or {}, record)


# Texto corto de una acción: "A1 -> (2, 3)" para un movimiento, "A1 placa a B1" para un placaje
def describe_action(action: Action) -> str:
    if isinstance(action, Move):
        return f"{action.unit_id} -> ({action.dest.row}, {action.dest.col})"
    return f"{action.unit_id} placa a {action.target}"


# Celdas de origen y destino de la flecha de una acción (en un placaje, de la unidad al portador)
def action_arrow(state: GameState, action: Action) -> tuple[Position, Position]:
    origin = state.position_of(action.unit_id)
    if isinstance(action, Move):
        return origin, action.dest
    return origin, state.position_of(action.target)


# Líneas legibles de un reporte de verificación (RF-42)
def describe_verification(report: VerificationReport) -> str:
    if not report.checks:
        return "Verificación: sin solución que verificar"
    lines = [f"Verificación RF-42: {'todo correcto' if report.ok else 'FALLÓ'}"]
    for check in report.checks:
        mark = "ok" if check.passed else "FALLO"
        lines.append(f"  [{mark}] {check.name}: {check.detail}")
    return "\n".join(lines)


# Aspecto de los terrenos conocidos por su nombre: nombre -> clase de textura. Un tipo con otro
# nombre se dibuja liso con un color de TERRAIN_PALETTE según el orden de su costo.
TERRAIN_KINDS = {
    "camino": "road",
    "pasto": "grass",
    "bosque": "forest",
    "pantano": "swamp",
    "muro": "wall",
}
KIND_COLORS = {
    "road": "#a3a3a3",
    "grass": "#98d86e",
    "forest": "#2e7d3e",
    "swamp": "#7d9b62",
    "wall": "#2a2a2a",
}


# Clase de textura y color de fondo de cada tipo de terreno del escenario (clase None = liso)
def terrain_styles(scenario: Scenario) -> dict[str, tuple[str | None, str]]:
    terrains = scenario.board.terrains
    ranked = sorted({t.cost for t in terrains.values() if t.passable and t.cost is not None})
    last = len(TERRAIN_PALETTE) - 1
    styles: dict[str, tuple[str | None, str]] = {}
    for name, terrain in terrains.items():
        if not terrain.passable or terrain.cost is None:
            styles[name] = ("wall", KIND_COLORS["wall"])
            continue
        plain = unicodedata.normalize("NFD", name.lower()).encode("ascii", "ignore").decode()
        kind = TERRAIN_KINDS.get(plain)
        if kind is not None and kind != "wall":
            styles[name] = (kind, KIND_COLORS[kind])
            continue
        rank = ranked.index(terrain.cost)
        index = rank if len(ranked) > last else round(rank * last / max(len(ranked) - 1, 1))
        styles[name] = (None, TERRAIN_PALETTE[min(index, last)])
    return styles


# Dibuja la textura de una clase de terreno dentro de la celda; la semilla fija repite el dibujo
def _draw_texture(
    canvas: tk.Canvas, kind: str | None, box: tuple[float, float, float, float], seed: int
) -> None:
    x0, y0, x1, y1 = box
    size = x1 - x0
    if kind is None or size < 14:
        return
    rnd = random.Random(seed)

    def point() -> tuple[float, float]:
        return x0 + size * rnd.uniform(0.12, 0.88), y0 + size * rnd.uniform(0.12, 0.88)

    if kind == "road":  # piedritas sobre el empedrado
        for _ in range(7):
            cx, cy = point()
            r = size * rnd.uniform(0.03, 0.06)
            shade = rnd.choice(("#8a8a8a", "#bdbdbd", "#7a7a7a"))
            canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=shade, outline="")
    elif kind == "grass":  # briznas de pasto
        for _ in range(8):
            cx, cy = point()
            h, w = size * 0.13, size * 0.05
            canvas.create_line(cx, cy, cx - w, cy - h, fill="#4f9c32")
            canvas.create_line(cx, cy, cx + w, cy - h, fill="#4f9c32")
    elif kind == "forest":  # dos árboles: tronco y dos capas de copa
        for fx, fy, scale in ((0.32, 0.88, 0.8), (0.68, 0.8, 1.0)):
            cx, base, s = x0 + size * fx, y0 + size * fy, size * 0.42 * scale
            canvas.create_rectangle(
                cx - s * 0.07, base - s * 0.25, cx + s * 0.07, base, fill="#5b3a1e", outline=""
            )
            canvas.create_polygon(
                cx - s * 0.4, base - s * 0.2, cx + s * 0.4, base - s * 0.2, cx, base - s * 0.75,
                fill="#14532d", outline="",
            )  # fmt: skip
            canvas.create_polygon(
                cx - s * 0.32, base - s * 0.5, cx + s * 0.32, base - s * 0.5, cx, base - s * 1.0,
                fill="#1f7a3a", outline="",
            )  # fmt: skip
    elif kind == "swamp":  # charcos de agua, ondas y juncos
        for _ in range(3):
            cx, cy = point()
            rx, ry = size * rnd.uniform(0.12, 0.2), size * rnd.uniform(0.06, 0.1)
            canvas.create_oval(cx - rx, cy - ry, cx + rx, cy + ry, fill="#4f8088", outline="")
            canvas.create_arc(
                cx - rx * 0.6, cy - ry * 0.6, cx + rx * 0.6, cy + ry * 0.6,
                start=20, extent=140, style="arc", outline="#a9d0d3",
            )  # fmt: skip
        for _ in range(3):
            cx, cy = point()
            canvas.create_line(cx, cy, cx, cy - size * 0.2, fill="#44663a", width=2)
            canvas.create_oval(
                cx - 2, cy - size * 0.27, cx + 2, cy - size * 0.17, fill="#6b4423", outline=""
            )
    elif kind == "wall":  # ladrillos: hiladas con las juntas desfasadas
        rows = 4
        h = size / rows
        for i in range(rows):
            y = y0 + i * h
            canvas.create_line(x0, y, x1, y, fill="#5a5a5a")
            offset = (size / 2) if i % 2 else (size / 4)
            for k in range(2):
                x = x0 + offset + k * size / 2
                if x < x1:
                    canvas.create_line(x, y, x, y + h, fill="#5a5a5a")


# Costo para mostrar en la celda: «3» si es entero, «1.5» si no
def _cost_text(cost: float) -> str:
    return f"{cost:g}"


class App:
    # Construye el layout común: barra superior, tablero, paneles a la derecha y controles abajo
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("TacticalGrid")
        self.scenario: Scenario | None = None
        self.trace: SearchTrace | None = None
        self.decision: AdversarialResult | DynamicAdversarialResult | None = None
        # partida en curso (Minimax/alfa-beta): estado actual, historial y última jugada
        self.game_state: GameState | None = None
        # variante dinámica: mismo estado con los contadores; su `base` es `game_state`
        self.dyn_state: dynamic.DynamicState | None = None
        self.history: list[str] = []
        self.arrow: tuple[Position, Position] | None = None
        self.busy = False
        self.auto = False  # partida automática IA contra IA en curso
        self.selected: str | None = None  # unidad elegida con el clic (juego manual)
        self.verification = ""
        self.after_id: str | None = None
        self.param_vars: dict[str, tk.StringVar] = {}

        # Barra superior: escenario y algoritmo
        bar = ttk.Frame(root, padding=6)
        bar.pack(fill="x")
        ttk.Button(bar, text="Seleccionar JSON", command=self.choose_file).pack(side="left")
        self.file_label = ttk.Label(bar, text="(ningún escenario)")
        self.file_label.pack(side="left", padx=8)
        self.algorithm = tk.StringVar(value="BFS")
        algorithm_box = ttk.Combobox(
            bar,
            textvariable=self.algorithm,
            values=list(SPECS),
            state="readonly",
            width=18,
        )
        algorithm_box.pack(side="right")
        ttk.Label(bar, text="Algoritmo:").pack(side="right", padx=(0, 4))
        algorithm_box.bind("<<ComboboxSelected>>", lambda _event: self.on_algorithm_changed())

        # Centro: tablero a la izquierda, paneles a la derecha
        body = ttk.Frame(root, padding=(6, 0))
        body.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(body, width=CANVAS_PIXELS, height=CANVAS_PIXELS, bg="white")
        self.canvas.pack(side="left")
        self.canvas.bind("<Button-1>", self._on_click)
        side = ttk.Frame(body, padding=(8, 0, 0, 0))
        side.pack(side="left", fill="both", expand=True)

        # Estado de la partida: turno, jugada, portador y leyenda de colores
        status_frame = ttk.LabelFrame(side, text="Estado", padding=6)
        status_frame.pack(fill="x", pady=(0, 6))
        self.turn_label = ttk.Label(status_frame, text="", justify="left", width=44)
        self.turn_label.pack(fill="x")
        # terrenos del escenario cargado: cuadro de color, nombre y costo
        self.terrain_legend = ttk.Frame(status_frame)
        self.terrain_legend.pack(fill="x", pady=(4, 0))
        legend = ttk.Frame(status_frame)
        legend.pack(fill="x", pady=(4, 0))
        for text, color in (
            ("● bando A", SIDE_COLORS[Side.A]),
            ("● bando B", SIDE_COLORS[Side.B]),
            ("◆ recurso", RESOURCE),
            ("▭ base", "#555555"),
            ("■ muro", IMPASSABLE),
        ):
            ttk.Label(legend, text=text, foreground=color).pack(side="left", padx=(0, 10))

        # Panel de parámetros: se reconstruye según el algoritmo elegido
        self.params_frame = ttk.LabelFrame(side, text="Parámetros", padding=6)
        self.params_frame.pack(fill="x")
        # Panel de métricas del resultado
        metrics_frame = ttk.LabelFrame(side, text="Métricas", padding=6)
        metrics_frame.pack(fill="x", pady=6)
        self.summary = ttk.Label(metrics_frame, text="", justify="left", width=44)
        self.summary.pack(fill="x")
        # Panel de traza: orden de expansión (aquí irán frontera, g/h/f, árbol...)
        trace_frame = ttk.LabelFrame(side, text="Traza", padding=6)
        trace_frame.pack(fill="both", expand=True)
        self.trace_text = tk.Text(trace_frame, width=44, height=12, state="disabled")
        self.trace_text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(trace_frame, command=self.trace_text.yview)
        scroll.pack(side="right", fill="y")
        self.trace_text.configure(yscrollcommand=scroll.set)

        # Controles de ejecución, comunes a todos los algoritmos
        controls = ttk.Frame(root, padding=6)
        controls.pack(fill="x")
        self.run_button = ttk.Button(controls, text="Ejecutar", command=self.run_all_at_once)
        self.run_button.pack(side="left")
        self.step_button = ttk.Button(controls, text="Animar", command=self.run_step_by_step)
        self.step_button.pack(side="left", padx=6)
        self.apply_button = ttk.Button(controls, text="Aplicar jugada", command=self.apply_move)
        self.apply_button.pack(side="left")
        self.reset_button = ttk.Button(controls, text="Reiniciar", command=self.reset)
        self.reset_button.pack(side="left", padx=6)
        self.verify = tk.BooleanVar(value=False)
        ttk.Checkbutton(controls, text="Verificar (RF-42)", variable=self.verify).pack(
            side="left", padx=6
        )
        # Partida: bando de la persona contra la IA, o la IA contra sí misma
        self.human = tk.StringVar(value=HUMAN_CHOICES[0][0])
        labels = {label: code for code, label in HUMAN_CHOICES}
        shown = tk.StringVar(value=HUMAN_CHOICES[0][1])
        ttk.Label(controls, text="Juegas:").pack(side="left", padx=(6, 4))
        human_box = ttk.Combobox(
            controls, textvariable=shown, values=list(labels), state="readonly", width=14
        )
        human_box.pack(side="left")
        human_box.bind(
            "<<ComboboxSelected>>", lambda _event: self._on_human_changed(labels[shown.get()])
        )
        self.auto_button = ttk.Button(controls, text="Partida automática", command=self.toggle_auto)
        self.auto_button.pack(side="left", padx=6)
        self.speed = tk.IntVar(value=STEP_MILLISECONDS)
        ttk.Scale(
            controls, from_=400, to=10, variable=self.speed, orient="horizontal", length=140
        ).pack(side="right")
        ttk.Label(controls, text="Velocidad:").pack(side="right", padx=(0, 4))

        self.enabled = False
        self._build_params()
        self._set_buttons(False)

    # Habilita los controles si hay escenario válido; "Animar" solo existe para búsquedas de camino
    def _set_buttons(self, enabled: bool) -> None:
        self.enabled = enabled
        state = "normal" if enabled else "disabled"
        for button in (self.run_button, self.reset_button):
            button.configure(state=state)
        adversarial = SPECS[self.algorithm.get()].adversarial
        animate = enabled and not adversarial
        self.step_button.configure(state="normal" if animate else "disabled")
        playable = enabled and adversarial and not self.busy and not self._game_over()
        self.apply_button.configure(state="normal" if playable else "disabled")
        # la partida automática se puede pausar mientras corre; si no, solo arrancar con juego vivo
        can_auto = (
            enabled and adversarial and (self.auto or (not self.busy and not self._game_over()))
        )
        self.auto_button.configure(
            text="Pausar" if self.auto else "Partida automática",
            state="normal" if can_auto else "disabled",
        )
        if self.busy:  # mientras el rival responde no se puede ejecutar nada más
            self.run_button.configure(state="disabled")

    # Reconstruye el panel de parámetros con los controles del algoritmo elegido
    def _build_params(self) -> None:
        for child in self.params_frame.winfo_children():
            child.destroy()
        self.param_vars = {}
        spec = SPECS[self.algorithm.get()]
        if spec.description:
            ttk.Label(self.params_frame, text=spec.description, wraplength=320).pack(anchor="w")
        if not spec.params:
            ttk.Label(self.params_frame, text="Sin parámetros.").pack(anchor="w", pady=(4, 0))
        for param in spec.params:
            row = ttk.Frame(self.params_frame)
            row.pack(fill="x", pady=(4, 0))
            ttk.Label(row, text=param.label + ":").pack(side="left")
            default = self._default_for(param)
            var = tk.StringVar(value=default)
            self.param_vars[param.key] = var
            if param.kind == "choice":
                labels = {label: value for value, label in param.options}
                shown = tk.StringVar(
                    value=next(lbl for val, lbl in param.options if val == default)
                )
                box = ttk.Combobox(
                    row, textvariable=shown, values=list(labels), state="readonly", width=14
                )
                box.pack(side="right")

                # traduce la etiqueta mostrada al valor interno del parámetro
                def on_pick(
                    _event: object,
                    v: tk.StringVar = var,
                    s: tk.StringVar = shown,
                    m: dict[str, str] = labels,
                ) -> None:
                    self._on_param_changed(v, m[s.get()])

                box.bind("<<ComboboxSelected>>", on_pick)
            else:
                ttk.Spinbox(
                    row,
                    from_=param.minimum,
                    to=param.maximum,
                    increment=0.5 if param.kind == "float" else 1,
                    textvariable=var,
                    width=6,
                    command=self._clear_result,
                ).pack(side="right")

    # Estado que se dibuja y sobre el que se decide: el de la partida o el inicial
    def _state(self) -> GameState:
        assert self.scenario is not None
        return self.game_state or self.scenario.initial_state

    # La variante dinámica está elegida en el selector
    def _dynamic(self) -> bool:
        return SPECS[self.algorithm.get()].decide_dynamic is not None

    # Estado dinámico actual (contadores incluidos); si no hay partida dinámica, uno nuevo
    def _dstate(self) -> dynamic.DynamicState:
        state = self._state()
        if self.dyn_state is not None and self.dyn_state.base is state:
            return self.dyn_state
        return dynamic.initial_dynamic_state(state)

    # Acciones legales del bando con el turno según la variante elegida
    def _legal(self) -> list[Action]:
        assert self.scenario is not None
        board = self.scenario.board
        if self._dynamic():
            return dynamic.legal_actions(board, self._dstate())
        return legal_actions(board, self._state())

    # Aplica una acción legal al estado de la partida según la variante elegida
    def _apply(self, action: Action) -> None:
        assert self.scenario is not None
        board = self.scenario.board
        if self._dynamic():
            nxt = dynamic.apply(board, self._dstate(), action, self.scenario.dynamic_rules)
            self.dyn_state, self.game_state = nxt, nxt.base
        else:
            self.dyn_state = None
            self.game_state, _ = apply(board, self._state(), action)

    # Pasa el turno del bando bloqueado según la variante elegida
    def _pass(self) -> None:
        assert self.scenario is not None
        if self._dynamic():
            nxt = dynamic.pass_turn(self.scenario.board, self._dstate())
            self.dyn_state, self.game_state = nxt, nxt.base
        else:
            self.dyn_state = None
            self.game_state = skip_turn(self._state())

    # La partida terminó: hay ganador o se agotaron los turnos
    def _game_over(self) -> bool:
        return self.scenario is not None and is_terminal(self.scenario.board, self._state())

    # Vuelve la partida al estado inicial del escenario
    def _reset_game(self) -> None:
        self._cancel_animation()
        self.game_state, self.dyn_state, self.arrow, self.busy = None, None, None, False
        self.auto = False
        self.selected = None
        self.history = []

    # Valor inicial de un parámetro: el de la sección `prueba` del escenario si lo trae
    def _default_for(self, param: ParamSpec) -> str:
        if self.scenario is None:
            return param.default
        config = self.scenario.test_config
        if param.key == "heuristic" and config.heuristic is not None:
            key = {"H1": "h1", "MANHATTAN": "h1", "H2": "h2", "OBSTACLE_AWARE": "h2"}.get(
                config.heuristic.upper()
            )
            return key or param.default
        if param.key == "k" and config.beam_width is not None:
            return str(config.beam_width)
        if param.key == "depth" and config.minimax_depth is not None:
            return str(config.minimax_depth)
        if param.key == "order" and config.action_order in ("default", "reversed"):
            return config.action_order
        if param.key.startswith("w_"):
            return str(self.scenario.utility_weights.get(param.key[2:], param.default))
        return param.default

    # Guarda el valor elegido en un parámetro y descarta el resultado anterior
    def _on_param_changed(self, var: tk.StringVar, value: str) -> None:
        var.set(value)
        self._clear_result()

    # Cambio de algoritmo: nuevo panel de parámetros y se descarta el resultado anterior
    def on_algorithm_changed(self) -> None:
        self._build_params()
        self._reset_game()
        self._clear_result()
        self._set_buttons(self.enabled)
        self._ai_opens()

    # Descarta el resultado mostrado y vuelve a dibujar el tablero limpio
    def _clear_result(self) -> None:
        self._cancel_animation()
        self.trace = None
        self.decision = None
        self.busy = False
        self.auto = False
        self.verification = ""
        self.summary.configure(text="")
        self._write_trace("\n".join(self.history))
        if self.scenario is not None:
            self.draw(0)
        self._set_buttons(self.enabled)

    # Botón Reiniciar
    def reset(self) -> None:
        self._reset_game()
        self._clear_result()
        self._set_buttons(self.enabled)
        self._ai_opens()

    # Abre el selector de archivo y carga el escenario elegido
    def choose_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Seleccionar escenario", filetypes=[("Escenario JSON", "*.json")]
        )
        if path:
            self.load(path)

    def load(self, path: str) -> None:
        self._cancel_animation()
        self._write_trace("")
        try:
            self.scenario = load_scenario(path)
        except ScenarioError as exc:
            self.scenario = None
            self.file_label.configure(text=path)
            self.canvas.delete("all")
            self.summary.configure(text="Escenario inválido:\n" + "\n".join(exc.errors))
            self._set_buttons(False)
            return
        self.file_label.configure(text=path)
        self.summary.configure(text="")
        self._build_terrain_legend()
        # el escenario pide la variante dinámica: se preselecciona un algoritmo dinámico
        if self.scenario.variant == "dinamica" and not self._dynamic():
            self.algorithm.set("Alfa-beta dinámico")
        self._build_params()
        self._reset_game()
        self._set_buttons(True)
        self.trace = None
        self.decision = None
        self._write_trace("")
        self.draw(0)
        self._ai_opens()

    # Ejecuta el algoritmo elegido y muestra el resultado final de una vez
    def run_all_at_once(self) -> None:
        if self._compute():
            if self.decision is not None:
                self.draw(0)
            else:
                assert self.trace is not None
                self.draw(len(self.trace.expanded_cells), show_path=True)
            self._show_summary()

    # Ejecuta el algoritmo elegido y lo reproduce celda por celda
    def run_step_by_step(self) -> None:
        if self._compute():
            assert self.trace is not None
            self.summary.configure(text="")
            self._animate(0)

    # Aplica la jugada que decide el algoritmo para el bando con el turno y luego deja que
    # el rival responda con el mismo algoritmo y parámetros
    def apply_move(self) -> None:
        assert self.scenario is not None
        self._cancel_animation()
        params = {key: var.get() for key, var in self.param_vars.items()}
        name = self.algorithm.get()
        if self._game_over() or not self._play_turn(name, params):
            self._set_buttons(self.enabled)
            return
        self.draw(0)
        if self._game_over():
            self._announce_result()
        else:
            self.busy = True
            self.after_id = self.root.after(RESPONSE_MILLISECONDS, self._respond, name, params)
        self._set_buttons(self.enabled)

    # Celda del tablero bajo el clic, o None si cae fuera
    def _cell_at(self, event: tk.Event[tk.Misc]) -> Position | None:
        assert self.scenario is not None
        board = self.scenario.board
        size = CANVAS_PIXELS / max(board.rows, board.cols)
        cell = Position(int(event.y // size), int(event.x // size))
        return cell if board.in_bounds(cell) else None

    # Acciones legales de la unidad elegida, con la celda del tablero donde se hace clic
    def _targets(self) -> dict[Position, Action]:
        assert self.scenario is not None and self.selected is not None
        state = self._state()
        targets: dict[Position, Action] = {}
        for action in self._legal():
            if action.unit_id != self.selected:
                continue
            cell = action.dest if isinstance(action, Move) else state.position_of(action.target)
            targets[cell] = action
        return targets

    # Clic en el tablero: elige una unidad del bando con el turno o juega la acción elegida
    def _on_click(self, event: tk.Event[tk.Misc]) -> None:
        if self.scenario is None or self.busy or not SPECS[self.algorithm.get()].adversarial:
            return
        if self._game_over():
            return
        cell = self._cell_at(event)
        if cell is None:
            return
        state = self._state()
        if state.turn is not self._human_side():  # no es tu turno
            return
        if self.selected is not None:
            action = self._targets().get(cell)
            if action is not None:
                self._play_manual(action)
                return
        occupant = state.unit_at(cell)
        mine = occupant is not None and self.scenario.board.unit_sides[occupant] is state.turn
        self.selected = occupant if mine else None
        self.draw(0)

    # Aplica la jugada del usuario y deja que el rival responda con el algoritmo elegido
    def _play_manual(self, action: Action) -> None:
        assert self.scenario is not None
        self._cancel_animation()
        state = self._state()
        self.decision = None
        self.verification = ""
        self.arrow = action_arrow(state, action)
        self._apply(action)
        self.history.append(
            f"{state.turn_number + 1}. {state.turn.value}: {describe_action(action)}  (manual)"
        )
        self.selected = None
        self.summary.configure(text=f"Jugada manual: {describe_action(action)}")
        self._write_trace("\n".join(self.history))
        self.draw(0)
        if self._game_over():
            self._announce_result()
        else:
            params = {key: var.get() for key, var in self.param_vars.items()}
            self.busy = True
            name = self.algorithm.get()
            self.after_id = self.root.after(RESPONSE_MILLISECONDS, self._respond, name, params)
        self._set_buttons(self.enabled)

    # Bando de la persona: el elegido, o por defecto el que abre la partida
    def _human_side(self) -> Side:
        assert self.scenario is not None
        choice = self.human.get()
        if choice in ("A", "B"):
            return Side(choice)
        return self.scenario.initial_state.turn

    # Cambio del bando de la persona: la partida empieza de nuevo
    def _on_human_changed(self, choice: str) -> None:
        self.human.set(choice)
        if self.scenario is None:
            return
        self._reset_game()
        self._clear_result()
        self._set_buttons(self.enabled)
        self._ai_opens()

    # Si la IA abre la partida (la persona juega el bando que no tiene el turno), mueve primero
    def _ai_opens(self) -> None:
        if self.scenario is None or self.busy or self.auto or self._game_over():
            return
        if not SPECS[self.algorithm.get()].adversarial:
            return
        if self._state().turn is self._human_side():
            return
        params = {key: var.get() for key, var in self.param_vars.items()}
        self.busy = True
        self.after_id = self.root.after(
            RESPONSE_MILLISECONDS, self._respond, self.algorithm.get(), params
        )
        self._set_buttons(self.enabled)

    # Botón «Partida automática»: la IA juega los dos bandos hasta el final; otro clic la pausa
    def toggle_auto(self) -> None:
        if self.auto:
            self._stop_auto()
            return
        if self.scenario is None or self._game_over():
            return
        self._cancel_animation()
        self.auto, self.busy, self.selected = True, True, None
        self.after_id = self.root.after(RESPONSE_MILLISECONDS, self._auto_step)
        self._set_buttons(self.enabled)
        self.draw(0)

    # Un paso de la partida automática: decide y aplica la jugada del bando con el turno
    def _auto_step(self) -> None:
        self.after_id = None
        if not self.auto:
            return
        params = {key: var.get() for key, var in self.param_vars.items()}
        if self._game_over() or not self._play_turn(self.algorithm.get(), params):
            self._stop_auto()
            return
        self.draw(0)
        if self._game_over():
            self._announce_result()
            self._stop_auto()
            return
        self.after_id = self.root.after(RESPONSE_MILLISECONDS, self._auto_step)

    # Termina o pausa la partida automática; el estado de la partida se conserva
    def _stop_auto(self) -> None:
        self._cancel_animation()
        self.auto = self.busy = False
        if self.scenario is not None:
            self.draw(0)
        self._set_buttons(self.enabled)

    # Respuesta del rival tras la jugada aplicada
    def _respond(self, name: str, params: Params) -> None:
        self.after_id = None
        self.busy = False
        self._play_turn(name, params)
        self.draw(0)
        if self._game_over():
            self._announce_result()
        self._set_buttons(self.enabled)

    # Decide y aplica una jugada del bando con el turno; False si la decisión falla
    def _play_turn(self, name: str, params: Params) -> bool:
        assert self.scenario is not None
        state = self._state()
        try:
            result = trace_decision(
                self.scenario,
                name,
                params,
                state,
                self.verify.get(),
                self._dstate() if self._dynamic() else None,
            )
        except ValueError as exc:
            self.summary.configure(text=f"Error: {exc}")
            return False
        self.verification = ""
        if self.verify.get():
            self.verification = describe_verification(self._verify(result))
        side, number = state.turn, state.turn_number + 1
        self.decision = result
        action = result.action
        if action is None:  # sin jugadas legales: el turno se salta solo
            self.arrow = None
            self._pass()
            self.history.append(f"{number}. {side.value}: sin jugadas, pasa el turno")
        else:
            self.arrow = action_arrow(state, action)
            self._apply(action)
            self.history.append(
                f"{number}. {side.value}: {describe_action(action)}  valor {result.value:g}"
            )
        self._write_trace("\n".join(self.history))
        self._show_summary()
        return True

    # Anuncia al final de la partida quién ganó o si hubo empate
    def _announce_result(self) -> None:
        assert self.scenario is not None
        won = winner(self.scenario.board, self._state())
        text = f"Ganó el bando {won.value}" if won else "Empate: se agotaron los turnos"
        self.history.append(text)
        self._write_trace("\n".join(self.history))
        self.summary.configure(text=self.summary.cget("text") + "\n" + text)

    def _compute(self) -> bool:
        self._cancel_animation()
        assert self.scenario is not None
        params = {key: var.get() for key, var in self.param_vars.items()}
        name = self.algorithm.get()
        self.trace, self.decision = None, None
        try:
            if SPECS[name].adversarial:
                state = self._state()
                self.decision = trace_decision(
                    self.scenario,
                    name,
                    params,
                    state,
                    self.verify.get(),
                    self._dstate() if self._dynamic() else None,
                )
                action = self.decision.action
                self.arrow = None if action is None else action_arrow(state, action)
            else:
                self.trace = trace_search(self.scenario, name, params)
        except ValueError as exc:
            self.draw(0)
            self.summary.configure(text=f"Error: {exc}")
            self._write_trace("")
            return False
        self.verification = self._verification_for()
        if self.decision is not None:
            self._write_trace(
                "\n".join([self._decision_lines(self.decision), "", *self.history]).rstrip()
            )
        else:
            assert self.trace is not None
            self._write_trace(
                "\n".join(
                    f"{i}. ({cell.row}, {cell.col})"
                    for i, cell in enumerate(self.trace.expanded_cells, start=1)
                )
            )
        return True

    # Texto de la verificación RF-42 del resultado actual (vacío si no se pidió)
    def _verification_for(self) -> str:
        if not self.verify.get():
            return ""
        assert self.scenario is not None
        if self.decision is not None:
            report = self._verify(self.decision)
        else:
            assert self.trace is not None
            report = verify_search(self.trace.problem, self.trace.result)
        return describe_verification(report)

    # Chequeo RF-42 de una decisión con las reglas de la variante que la produjo
    def _verify(self, result: AdversarialResult | DynamicAdversarialResult) -> VerificationReport:
        assert self.scenario is not None
        board = self.scenario.board
        if isinstance(result, DynamicAdversarialResult):
            return verify_adversarial_dynamic(board, self._dstate(), result)
        return verify_adversarial(board, self._state(), result)

    # Una línea por acción de la raíz con su valor; la elegida va marcada con *
    def _decision_lines(self, result: AdversarialResult | DynamicAdversarialResult) -> str:
        if not result.root_values:
            return "Sin acciones: la raíz es terminal."
        return "\n".join(
            f"{'*' if action == result.action else ' '} {describe_action(action)}   valor {value:g}"
            for action, value in result.root_values
        )

    # Reemplaza el contenido del panel de traza
    def _write_trace(self, text: str) -> None:
        self.trace_text.configure(state="normal")
        self.trace_text.delete("1.0", "end")
        self.trace_text.insert("1.0", text)
        self.trace_text.configure(state="disabled")

    def _animate(self, step: int) -> None:
        assert self.trace is not None
        total = len(self.trace.expanded_cells)
        self.draw(step, show_path=step >= total)
        if step >= total:
            self.after_id = None
            self._show_summary()
            return
        self.after_id = self.root.after(self.speed.get(), self._animate, step + 1)

    def _cancel_animation(self) -> None:
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def _show_summary(self) -> None:
        if self.decision is not None:
            d = self.decision
            move = "sin acción (estado terminal)" if d.action is None else describe_action(d.action)
            self.summary.configure(
                text=f"{d.algorithm}: juega {move}, valor {d.value:g}\n"
                f"generados {d.generated} · evaluados {d.evaluated} · podados {d.pruned} · "
                f"profundidad {d.depth_reached} · {d.time_seconds * 1000:.2f} ms"
                + (f"\n{self.verification}" if self.verification else "")
            )
            return
        assert self.trace is not None
        r = self.trace.result
        head = (
            f"{r.algorithm}: camino encontrado, {r.length} movimientos, costo {r.cost}"
            if r.success
            else f"{r.algorithm} no encontró camino"
        )
        self.summary.configure(
            text=f"{head}\nexpandidos {r.expanded} · generados {r.generated} · "
            f"frontera máx. {r.max_frontier} · {r.time_seconds * 1000:.2f} ms"
            + (f"\n{self.verification}" if self.verification else "")
        )

    # Recurso (rombo dorado), portador (aro dorado) y flecha de la acción elegida
    def _draw_decision_layer(
        self, size: float, box: Callable[[Position], tuple[float, float, float, float]]
    ) -> None:
        assert self.scenario is not None
        state = self._state()
        if state.resource is not None:
            x0, y0, x1, y1 = box(state.resource)
            cx, cy, r = (x0 + x1) / 2, (y0 + y1) / 2, size * 0.3
            self.canvas.create_polygon(
                cx, cy - r, cx + r, cy, cx, cy + r, cx - r, cy, fill=RESOURCE, outline="black"
            )
        if state.carrier is not None:
            x0, y0, x1, y1 = box(state.position_of(state.carrier))
            self.canvas.create_oval(x0 + 2, y0 + 2, x1 - 2, y1 - 2, outline=RESOURCE, width=3)
        if self.arrow is not None:
            origin, dest = self.arrow
            x0, y0, x1, y1 = box(origin)
            tx0, ty0, tx1, ty1 = box(dest)
            self.canvas.create_rectangle(tx0, ty0, tx1, ty1, outline=PATH, width=4)
            self.canvas.create_line(
                (x0 + x1) / 2,
                (y0 + y1) / 2,
                (tx0 + tx1) / 2,
                (ty0 + ty1) / 2,
                fill=PATH,
                width=4,
                arrow=tk.LAST,
            )

    # Texto del panel «Estado»: turno, jugada y portador (o la búsqueda de camino en curso)
    def _update_status(self) -> None:
        assert self.scenario is not None
        if not SPECS[self.algorithm.get()].adversarial:
            config = self.scenario.test_config
            goal = "" if config.goal is None else f" → ({config.goal.row}, {config.goal.col})"
            self.turn_label.configure(text=f"Búsqueda de camino: unidad {config.start_unit}{goal}")
            return
        state = self._state()
        board = self.scenario.board
        won = winner(board, state)
        if won is not None:
            head = f"Terminó: ganó el bando {won.value}"
        elif is_terminal(board, state):
            head = "Terminó: empate por límite de turnos"
        else:
            head = f"Turno del bando {state.turn.value}"
        if state.carrier is not None:
            carrier = f"{state.carrier} (bando {board.unit_sides[state.carrier].value})"
        else:
            where = state.resource
            carrier = f"nadie (recurso en {where.row}, {where.col})" if where else "nadie"
        extra = ""
        if self._dynamic():
            waiting = [f"{uid} {turns}" for uid, turns in self._dstate().recovery if turns > 0]
            immunity = self._dstate().immunity
            extra = "\nrecuperación: " + (", ".join(waiting) or "ninguna")
            extra += f" · inmunidad del portador: {immunity}" if immunity else ""
        role = "IA contra IA" if self.auto else f"tú juegas el bando {self._human_side().value}"
        self.turn_label.configure(
            text=f"{head}\nJugada {state.turn_number} de {board.turn_limit} · portador: "
            f"{carrier}{extra}\n{role}"
        )

    # Leyenda de terrenos: un cuadro con el color, el nombre y el costo de cada tipo
    def _build_terrain_legend(self) -> None:
        for child in self.terrain_legend.winfo_children():
            child.destroy()
        if self.scenario is None:
            return
        styles = terrain_styles(self.scenario)
        for name, terrain in self.scenario.board.terrains.items():
            cost = "muro" if terrain.cost is None else f"costo {_cost_text(terrain.cost)}"
            kind, fill = styles[name]
            item = ttk.Frame(self.terrain_legend)
            item.pack(side="left", padx=(0, 10))
            swatch = tk.Canvas(item, width=24, height=24, highlightthickness=1)
            swatch.pack(side="left", padx=(0, 3))
            swatch.create_rectangle(0, 0, 24, 24, fill=fill, outline="")
            _draw_texture(swatch, kind, (0, 0, 24, 24), 7)
            ttk.Label(item, text=f"{name} ({cost})").pack(side="left")

    # Dibuja el tablero con las primeras `step` celdas expandidas (y el camino si se pide)
    def draw(self, step: int, show_path: bool = False) -> None:
        assert self.scenario is not None
        board = self.scenario.board
        size = CANVAS_PIXELS / max(board.rows, board.cols)
        self.canvas.delete("all")
        expanded = set(self.trace.expanded_cells[:step]) if self.trace else set()
        styles = terrain_styles(self.scenario)

        def box(pos: Position) -> tuple[float, float, float, float]:
            return pos.col * size, pos.row * size, (pos.col + 1) * size, (pos.row + 1) * size

        for row in range(board.rows):
            for col in range(board.cols):
                pos = Position(row, col)
                kind, fill = styles[board.grid[row][col]]
                x0, y0, x1, y1 = box(pos)
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="#6a6a6a")
                _draw_texture(self.canvas, kind, (x0, y0, x1, y1), row * 1000 + col)
                terrain = board.terrain_at(pos)
                if terrain.cost is None:  # muro: sin costo ni velo de expansión
                    continue
                if pos in expanded:  # velo naranja: deja ver el terreno de debajo
                    self.canvas.create_rectangle(
                        x0, y0, x1, y1, fill=EXPANDED, stipple="gray50", outline=""
                    )
                if size >= 24:  # insignia con el costo en la esquina, sin tapar a las unidades
                    text = _cost_text(terrain.cost)
                    font_size = max(8, int(size * 0.22))
                    width = font_size * (0.75 * len(text) + 0.9)
                    self.canvas.create_rectangle(
                        x0 + 2, y0 + 2, x0 + 2 + width, y0 + 2 + font_size * 1.9,
                        fill="#fffbe6", outline="#444444",
                    )  # fmt: skip
                    self.canvas.create_text(
                        x0 + 2 + width / 2,
                        y0 + 2 + font_size * 0.95,
                        text=text,
                        fill="black",
                        font=("TkDefaultFont", font_size, "bold"),
                    )
        for side, pos in board.bases.items():
            self.canvas.create_rectangle(*box(pos), outline=SIDE_COLORS[side], width=3)
        if SPECS[self.algorithm.get()].adversarial:
            self._draw_decision_layer(size, box)
        if self.trace and show_path and self.trace.result.success:
            points = [
                coord
                for cell in self.trace.result.path
                for coord in ((cell.col + 0.5) * size, (cell.row + 0.5) * size)
            ]
            if len(points) >= 4:
                self.canvas.create_line(*points, fill="white", width=7, capstyle="round")
                self.canvas.create_line(*points, fill=PATH, width=4, capstyle="round")
        if self.trace:
            self.canvas.create_rectangle(*box(self.trace.goal), outline=GOAL, width=4)
        for unit_id, pos in self._state().positions:
            x0, y0, x1, y1 = box(pos)
            pad = size * 0.2
            self.canvas.create_oval(
                x0 + pad,
                y0 + pad,
                x1 - pad,
                y1 - pad,
                fill=SIDE_COLORS[board.unit_sides[unit_id]],
                outline="white",
            )
            if size >= 24:
                self.canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=unit_id, fill="white")
            # variante dinámica: turnos propios que le faltan a la unidad para volver a moverse
            if self._dynamic() and size >= 24:
                turns = self._dstate().recovery_of(unit_id)
                if turns > 0:
                    self.canvas.create_text(x1 - 6, y0 + 7, text=str(turns), fill="black")
        if self.selected is not None and SPECS[self.algorithm.get()].adversarial:
            x0, y0, x1, y1 = box(self._state().position_of(self.selected))
            self.canvas.create_rectangle(x0, y0, x1, y1, outline="#00a050", width=3)
            for cell in self._targets():
                tx0, ty0, tx1, ty1 = box(cell)
                cx, cy, r = (tx0 + tx1) / 2, (ty0 + ty1) / 2, size * 0.14
                self.canvas.create_oval(
                    cx - r, cy - r, cx + r, cy + r, fill="#00a050", outline="white"
                )
        self._update_status()
        # la meta de la configuración se marca aunque aún no se haya ejecutado
        if self.trace is None and not SPECS[self.algorithm.get()].adversarial:
            goal = self.scenario.test_config.goal
            if goal is not None and board.in_bounds(goal):
                self.canvas.create_rectangle(*box(goal), outline=GOAL, width=4)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = tk.Tk()
    app = App(root)
    if args:
        app.load(args[0])
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
