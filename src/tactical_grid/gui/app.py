"""Ventana mínima con tkinter (RF-40): cuadrícula, terrenos, obstáculos, bases, recurso,
unidades, bando, portador, turno y camino encontrado. Las reglas y los algoritmos vienen
de `Session`; aquí solo se dibuja y se reenvían los clics."""

import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from tactical_grid.domain.model import Action, Move, Position, Side, Wait
from tactical_grid.experiments.runner import (
    ADVERSARIAL_ALGORITHMS,
    RunError,
    RunOptions,
    canonical,
)
from tactical_grid.gui.session import Session
from tactical_grid.scenario.loader import ScenarioError, load_scenario

CANVAS_PIXELS = 640
SIDE_COLORS = {Side.A: "#1e6fd9", Side.B: "#d9381e"}
IMPASSABLE = "#3a3a3a"
GOLD = "#ffc400"
OVERLAY = "#8000c8"
SUGGESTION = "#00a050"
CHEAP, DEAR = (196, 232, 170), (150, 110, 60)

# Nombre que ve el usuario -> nombre canónico del algoritmo.
ALGORITHM_LABELS = {
    "BFS - Búsqueda en anchura": "BFS",
    "DFS - Búsqueda en profundidad": "DFS",
    "UCS - Costo uniforme": "UCS",
    "A* - Búsqueda informada": "A_STAR",
    "Beam Search - Haz local": "BEAM",
    "Minimax": "MINIMAX",
    "Alfa-beta": "ALPHA_BETA",
}
HEURISTIC_LABELS = {"H1 - Manhattan": "H1", "H2 - Esquiva obstáculos": "H2"}
ORDER_LABELS = {"Normal": "default", "Invertido": "reversed"}
INFORMED = {"A_STAR", "BEAM"}
HELP = (
    "CÓMO USAR\n"
    "• Jugar: clic en una unidad del bando que tiene el turno y luego en una celda\n"
    "  verde para moverla.\n"
    "• Buscar un camino: elige una unidad, fija la meta (modo «Fijar meta» o clic\n"
    "  derecho), elige BFS/DFS/UCS/A*/Beam y pulsa «Ejecutar».\n"
    "• Decisión del adversario: elige Minimax o Alfa-beta, pulsa «Ejecutar» y luego\n"
    "  «Aplicar jugada sugerida», o usa «Jugar turno con la IA».\n"
)


class App:
    def __init__(self, root: tk.Tk, session: Session) -> None:
        self.root = root
        self.session = session
        self.path: list[Position] = []
        self.suggestion: Action | None = None
        self.auto_job: str | None = None
        self.selected: str | None = None
        self.goal: Position | None = None
        root.title("TacticalGrid")
        self._build_widgets()
        self._load_defaults()
        self.redraw()

    # ---- widgets -------------------------------------------------------------------------
    def _build_widgets(self) -> None:
        left = ttk.Frame(self.root)
        left.grid(row=0, column=0, padx=8, pady=8, sticky="n")
        self.canvas = tk.Canvas(left, width=CANVAS_PIXELS, height=CANVAS_PIXELS, bg="white")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Motion>", self._on_hover)
        self.hover = tk.StringVar(value="Pasa el ratón sobre una celda para ver sus datos.")
        ttk.Label(left, textvariable=self.hover).pack(anchor="w", pady=(4, 0))
        self.legend = tk.Canvas(left, width=CANVAS_PIXELS, height=26, highlightthickness=0)
        self.legend.pack(anchor="w", pady=(2, 0))

        panel = ttk.Frame(self.root)
        panel.grid(row=0, column=1, sticky="n", padx=(0, 8), pady=8)

        game = ttk.LabelFrame(panel, text="Partida")
        game.pack(fill="x")
        self.turn_label = tk.Label(game, font=("Arial", 13, "bold"), anchor="w", fg="white")
        self.turn_label.pack(fill="x", padx=4, pady=4)
        self.status = tk.StringVar()
        ttk.Label(game, textvariable=self.status, justify="left").pack(anchor="w", padx=4)

        self.click_mode = tk.StringVar(value="mover")
        mode = ttk.LabelFrame(panel, text="Clic izquierdo sobre el mapa")
        mode.pack(fill="x", pady=(6, 0))
        ttk.Radiobutton(
            mode, text="Seleccionar / mover unidades", variable=self.click_mode, value="mover"
        ).pack(anchor="w")
        ttk.Radiobutton(
            mode, text="Fijar meta de la búsqueda", variable=self.click_mode, value="meta"
        ).pack(anchor="w")

        actions = ttk.Frame(panel)
        actions.pack(fill="x", pady=(6, 0))
        for index, (text, command) in enumerate(
            [
                ("Esperar (unidad elegida)", self.wait_selected),
                ("Deshacer", self.undo),
                ("Reiniciar partida", self.reset),
                ("Abrir escenario...", self.open_scenario),
            ]
        ):
            ttk.Button(actions, text=text, command=command).grid(
                row=index // 2, column=index % 2, sticky="we", padx=1, pady=1
            )
        actions.columnconfigure((0, 1), weight=1)

        algo = ttk.LabelFrame(panel, text="Algoritmo")
        algo.pack(fill="x", pady=(6, 0))
        self.algorithm = tk.StringVar()
        self.heuristic = tk.StringVar(value="H1 - Manhattan")
        self.beam_k = tk.StringVar(value="3")
        self.depth = tk.StringVar(value="3")
        self.order = tk.StringVar(value="Normal")
        self.verify = tk.BooleanVar(value=False)
        picker = ttk.Combobox(
            algo,
            textvariable=self.algorithm,
            values=list(ALGORITHM_LABELS),
            state="readonly",
            width=32,
        )
        picker.pack(fill="x", padx=4, pady=4)
        picker.bind("<<ComboboxSelected>>", lambda _e: self._refresh_params())
        self.params = ttk.Frame(algo)
        self.params.pack(fill="x", padx=4)
        self.heuristic_box = self._param(
            "Heurística",
            ttk.Combobox,
            0,
            self.heuristic,
            values=list(HEURISTIC_LABELS),
            state="readonly",
        )
        self.k_box = self._param("Ancho k del haz", ttk.Entry, 1, self.beam_k)
        self.depth_box = self._param("Profundidad", ttk.Entry, 2, self.depth)
        self.order_box = self._param(
            "Orden de acciones",
            ttk.Combobox,
            3,
            self.order,
            values=list(ORDER_LABELS),
            state="readonly",
        )
        ttk.Checkbutton(algo, text="Verificar resultado (RF-42)", variable=self.verify).pack(
            anchor="w", padx=4
        )
        ttk.Button(algo, text="▶ Ejecutar", command=self.run_algorithm).pack(
            fill="x", padx=4, pady=(4, 2)
        )
        self.adv_buttons = ttk.Frame(algo)
        self.adv_buttons.pack(fill="x", padx=4, pady=(0, 4))
        ttk.Button(
            self.adv_buttons, text="Aplicar jugada sugerida", command=self.apply_suggestion
        ).pack(fill="x", pady=1)
        ttk.Button(self.adv_buttons, text="Jugar turno con la IA", command=self.play_ai_turn).pack(
            fill="x", pady=1
        )

        auto = ttk.LabelFrame(panel, text="Modo automático (IA contra IA)")
        auto.pack(fill="x", pady=(6, 0))
        self.speed = tk.IntVar(value=600)
        row = ttk.Frame(auto)
        row.pack(fill="x", padx=4, pady=4)
        ttk.Label(row, text="Pausa entre jugadas (ms)").pack(side="left")
        ttk.Scale(row, from_=0, to=2000, variable=self.speed, orient="horizontal", length=130).pack(
            side="left", padx=4
        )
        self.auto_button = ttk.Button(
            auto, text="▶ Iniciar partida automática", command=self.toggle_auto
        )
        self.auto_button.pack(fill="x", padx=4, pady=(0, 4))

        self.hint = tk.StringVar()
        ttk.Label(panel, textvariable=self.hint, wraplength=330, foreground="#a02020").pack(
            anchor="w", pady=(6, 0)
        )
        notebook = ttk.Notebook(panel)
        notebook.pack(fill="both", pady=(4, 0))
        self.output = self._text_tab(notebook, "Resultados", 12)
        self.history = self._text_tab(notebook, "Jugadas", 12)

    def _param(
        self, label: str, widget_type: type, row: int, var: tk.StringVar, **options: Any
    ) -> list[tk.Widget]:
        name = ttk.Label(self.params, text=label)
        name.grid(row=row, column=0, sticky="w")
        field = widget_type(self.params, textvariable=var, width=24, **options)
        field.grid(row=row, column=1, sticky="we", pady=1)
        return [name, field]

    @staticmethod
    def _text_tab(notebook: ttk.Notebook, title: str, height: int) -> tk.Text:
        frame = ttk.Frame(notebook)
        text = tk.Text(frame, width=48, height=height, wrap="word", state="disabled")
        text.pack(fill="both")
        notebook.add(frame, text=title)
        return text

    def _refresh_params(self) -> None:
        """Show only the options that apply to the chosen algorithm."""
        name = self._algorithm_name()
        for widgets, visible in (
            (self.heuristic_box, name in INFORMED),
            (self.k_box, name == "BEAM"),
            (self.depth_box, name in ADVERSARIAL_ALGORITHMS),
            (self.order_box, name in ADVERSARIAL_ALGORITHMS),
        ):
            for widget in widgets:
                widget.grid() if visible else widget.grid_remove()
        if name in ADVERSARIAL_ALGORITHMS:
            self.adv_buttons.pack(fill="x", padx=4, pady=(0, 4))
        else:
            self.adv_buttons.pack_forget()

    def _algorithm_name(self) -> str:
        return ALGORITHM_LABELS.get(self.algorithm.get(), "A_STAR")

    def _load_defaults(self) -> None:
        config = self.session.scenario.test_config
        self.path, self.suggestion = [], None
        self.goal = config.goal
        self.selected = config.start_unit
        name = canonical(config.algorithm) if config.algorithm else "A_STAR"
        self.algorithm.set(next(k for k, v in ALGORITHM_LABELS.items() if v == name))
        if config.heuristic:
            self.heuristic.set(
                next(
                    (k for k, v in HEURISTIC_LABELS.items() if v == config.heuristic.upper()),
                    "H1 - Manhattan",
                )
            )
        if config.beam_width is not None:
            self.beam_k.set(str(config.beam_width))
        if config.minimax_depth is not None:
            self.depth.set(str(config.minimax_depth))
        if config.action_order == "reversed":
            self.order.set("Invertido")
        self.hint.set("")
        self.click_mode.set("mover")
        self._refresh_params()
        self._write(self.output, HELP)
        self._write(self.history, "")

    # ---- drawing -------------------------------------------------------------------------
    def _cell_size(self) -> float:
        board = self.session.scenario.board
        return CANVAS_PIXELS / max(board.rows, board.cols)

    def _center(self, pos: Position) -> tuple[float, float]:
        cell = self._cell_size()
        return (pos.col + 0.5) * cell, (pos.row + 0.5) * cell

    def _cost_range(self) -> tuple[float, float]:
        terrains = self.session.scenario.board.terrains.values()
        costs = [t.cost for t in terrains if t.passable and t.cost is not None]
        return (min(costs), max(costs)) if costs else (0.0, 0.0)

    def _terrain_color(self, pos: Position) -> str:
        """Passable terrains go from light green (cheap) to brown (expensive); read from JSON."""
        terrain = self.session.scenario.board.terrain_at(pos)
        if not terrain.passable or terrain.cost is None:
            return IMPASSABLE
        low, high = self._cost_range()
        share = 0.0 if high == low else (terrain.cost - low) / (high - low)
        red, green, blue = (int(a + (b - a) * share) for a, b in zip(CHEAP, DEAR, strict=True))
        return f"#{red:02x}{green:02x}{blue:02x}"

    def redraw(self) -> None:
        canvas = self.canvas
        board, state = self.session.scenario.board, self.session.state
        canvas.delete("all")
        cell = self._cell_size()
        for row in range(board.rows):
            for col in range(board.cols):
                x0, y0 = col * cell, row * cell
                terrain = board.terrain_at(Position(row, col))
                canvas.create_rectangle(
                    x0,
                    y0,
                    x0 + cell,
                    y0 + cell,
                    fill=self._terrain_color(Position(row, col)),
                    outline="#777",
                )
                if cell >= 30 and terrain.passable:
                    canvas.create_text(
                        x0 + 3, y0 + 2, anchor="nw", text=f"{terrain.cost:g}", font=("Arial", 7)
                    )
        self._draw_reachable()
        for side, base in board.bases.items():
            x0, y0 = base.col * cell, base.row * cell
            canvas.create_rectangle(
                x0 + 2,
                y0 + 2,
                x0 + cell - 2,
                y0 + cell - 2,
                outline=SIDE_COLORS[side],
                width=3,
            )
            canvas.create_text(
                x0 + cell - 4,
                y0 + cell - 3,
                anchor="se",
                text=f"Base {side.value}" if cell >= 48 else side.value,
                fill=SIDE_COLORS[side],
                font=("Arial", max(7, int(cell / 4)), "bold"),
            )
        if len(self.path) > 1:
            points = [c for p in self.path for c in self._center(p)]
            canvas.create_line(*points, fill=OVERLAY, width=3, arrow=tk.LAST)
        if self.goal is not None:
            gx, gy = self._center(self.goal)
            canvas.create_oval(
                gx - cell / 3,
                gy - cell / 3,
                gx + cell / 3,
                gy + cell / 3,
                outline=OVERLAY,
                width=3,
                dash=(3, 2),
            )
            canvas.create_text(
                gx,
                gy - cell / 2 + 6,
                text="meta",
                fill=OVERLAY,
                font=("Arial", max(7, int(cell / 4)), "bold"),
            )
        if state.resource is not None:
            rx, ry = self._center(state.resource)
            r = cell / 4
            canvas.create_polygon(
                rx, ry - r, rx + r, ry, rx, ry + r, rx - r, ry, fill=GOLD, outline="black"
            )
        for uid, pos in state.positions:
            ux, uy = self._center(pos)
            r = cell * 0.36
            carrying = uid == state.carrier
            canvas.create_oval(
                ux - r,
                uy - r,
                ux + r,
                uy + r,
                fill=SIDE_COLORS[board.unit_sides[uid]],
                outline=GOLD if carrying else "white",
                width=4 if carrying else 2,
            )
            if uid == self.selected:
                canvas.create_oval(
                    ux - r - 3,
                    uy - r - 3,
                    ux + r + 3,
                    uy + r + 3,
                    outline="black",
                    width=2,
                    dash=(4, 2),
                )
            canvas.create_text(
                ux, uy, text=uid, fill="white", font=("Arial", max(7, int(cell / 3.5)), "bold")
            )
        self._draw_suggestion()
        self._draw_legend()
        self._update_status()

    def _draw_reachable(self) -> None:
        """Mark the cells the selected unit can move to (only on its side's turn)."""
        if self.selected is None or self.click_mode.get() != "mover":
            return
        cell = self._cell_size()
        for dest in self.session.destinations(self.selected):
            x, y = self._center(dest)
            self.canvas.create_oval(
                x - cell / 6,
                y - cell / 6,
                x + cell / 6,
                y + cell / 6,
                fill=SUGGESTION,
                outline="white",
                width=1,
            )

    def _draw_suggestion(self) -> None:
        action = self.suggestion
        if isinstance(action, Move):
            start = self._center(self.session.state.position_of(action.unit_id))
            end = self._center(action.dest)
            self.canvas.create_line(*start, *end, fill=SUGGESTION, width=5, arrow=tk.LAST)
        elif isinstance(action, Wait):
            x, y = self._center(self.session.state.position_of(action.unit_id))
            self.canvas.create_text(
                x, y - 18, text="esperar", fill=SUGGESTION, font=("Arial", 9, "bold")
            )

    def _draw_legend(self) -> None:
        legend = self.legend
        legend.delete("all")
        low, high = self._cost_range()
        x = 2
        for label, color in (
            (f"terreno barato ({low:g})", f"#{CHEAP[0]:02x}{CHEAP[1]:02x}{CHEAP[2]:02x}"),
            (f"terreno caro ({high:g})", f"#{DEAR[0]:02x}{DEAR[1]:02x}{DEAR[2]:02x}"),
            ("obstáculo", IMPASSABLE),
        ):
            legend.create_rectangle(x, 6, x + 14, 20, fill=color, outline="#777")
            legend.create_text(x + 18, 13, anchor="w", text=label, font=("Arial", 8))
            x += 32 + 6 * len(label)
        legend.create_polygon(x + 7, 5, x + 14, 13, x + 7, 21, x, 13, fill=GOLD, outline="black")
        legend.create_text(x + 18, 13, anchor="w", text="recurso", font=("Arial", 8))
        x += 80
        for side in Side:
            legend.create_oval(x, 5, x + 16, 21, fill=SIDE_COLORS[side], outline="white")
            legend.create_text(
                x + 20, 13, anchor="w", text=f"bando {side.value}", font=("Arial", 8)
            )
            x += 78
        legend.create_oval(x, 5, x + 16, 21, fill="#888", outline=GOLD, width=3)
        legend.create_text(x + 20, 13, anchor="w", text="portador", font=("Arial", 8))

    def _update_status(self) -> None:
        state, board = self.session.state, self.session.scenario.board
        carrier = state.carrier
        if carrier:
            carrier_text = f"{carrier} (bando {board.unit_sides[carrier].value})"
        else:
            carrier_text = "nadie (el recurso está en el mapa)"
        goal = "sin fijar" if self.goal is None else f"({self.goal.row}, {self.goal.col})"
        outcome = self.session.outcome()
        self.turn_label.configure(
            text=outcome or f"Turno del bando {state.turn.value}",
            bg=SIDE_COLORS[state.turn] if not outcome else "#444",
        )
        self.status.set(
            f"Movimiento {state.turn_number} de {board.turn_limit}\n"
            f"Portador del recurso: {carrier_text}\n"
            f"Unidad elegida: {self.selected or 'ninguna'}\n"
            f"Meta de la búsqueda: {goal}"
        )
        self._write(self.history, "\n".join(self.session.log))
        self.history.see("end")

    # ---- events --------------------------------------------------------------------------
    def _cell_at(self, event: Any) -> Position | None:
        board = self.session.scenario.board
        cell = self._cell_size()
        row, col = int(event.y // cell), int(event.x // cell)
        if event.x < 0 or event.y < 0 or row >= board.rows or col >= board.cols:
            return None
        return Position(row, col)

    def _on_hover(self, event: Any) -> None:
        pos = self._cell_at(event)
        if pos is None:
            return
        board = self.session.scenario.board
        terrain = board.terrain_at(pos)
        name = board.grid[pos.row][pos.col]
        cost = f"costo {terrain.cost:g}" if terrain.passable else "no transitable"
        extra = ""
        unit = self.session.state.unit_at(pos)
        if unit:
            extra = f" · unidad {unit} (bando {board.unit_sides[unit].value})"
        if self.session.state.resource == pos:
            extra += " · recurso"
        self.hover.set(f"Celda ({pos.row}, {pos.col}): {name}, {cost}{extra}")

    def _on_left_click(self, event: Any) -> None:
        pos = self._cell_at(event)
        if pos is None:
            return
        if self.click_mode.get() == "meta":
            self._set_goal(pos)
            return
        occupant = self.session.state.unit_at(pos)
        if occupant is not None:
            self.selected = occupant
            self._clear_overlays()
            mine = self.session.scenario.board.unit_sides[occupant] is self.session.state.turn
            self.hint.set("" if mine else "Esa unidad es del otro bando: no es su turno.")
        elif self.selected is not None:
            action = self.session.move_for_click(self.selected, pos)
            if action is not None:
                self._play(action)
                return
            self.hint.set("Movimiento no permitido: elige una celda marcada en verde.")
        self.redraw()

    def _on_right_click(self, event: Any) -> None:
        pos = self._cell_at(event)
        if pos is not None:
            self._set_goal(pos)

    def _set_goal(self, pos: Position) -> None:
        if not self.session.scenario.board.is_passable(pos):
            self.hint.set("La meta debe ser una celda transitable.")
            return
        self.goal, self.path = pos, []
        self.hint.set("")
        self.redraw()

    def _clear_overlays(self) -> None:
        self.path, self.suggestion = [], None

    def _play(self, action: Action) -> None:
        self.session.play(action)
        self._clear_overlays()
        self.hint.set("")
        self.redraw()
        outcome = self.session.outcome()
        if outcome:
            messagebox.showinfo("Fin de la partida", outcome)

    # ---- commands ------------------------------------------------------------------------
    def run_algorithm(self) -> None:
        name = self._algorithm_name()
        try:
            if name in ADVERSARIAL_ALGORITHMS:
                self._run_adversarial(name)
            else:
                self._run_search(name)
        except (RunError, ValueError) as exc:
            self.hint.set(f"Error: {exc}")

    def _run_search(self, name: str) -> None:
        if self.selected is None:
            raise RunError("elige una unidad de inicio (clic sobre ella)")
        if self.goal is None:
            raise RunError("fija la meta (modo «Fijar meta» o clic derecho)")
        options = RunOptions(
            algorithm=name,
            heuristic=HEURISTIC_LABELS.get(self.heuristic.get(), "H1"),
            k=self._int(self.beam_k, "El ancho k") if name == "BEAM" else None,
            unit=self.selected,
            goal=self.goal,
            verify=self.verify.get(),
        )
        report = self.session.search(options)
        self.path = [Position(r, c) for r, c in report["camino"]]
        self.suggestion = None
        self.hint.set("" if report["exito"] else "El algoritmo no encontró camino a la meta.")
        self._write(self.output, json.dumps(report, indent=1, ensure_ascii=False))
        self.redraw()

    def _run_adversarial(self, name: str) -> None:
        result = self.session.decide(
            name,
            self._int(self.depth, "La profundidad"),
            ORDER_LABELS.get(self.order.get(), "default"),
            record=self.verify.get(),
        )
        self.path, self.suggestion = [], result.action
        self.hint.set("Jugada sugerida en verde. Pulsa «Aplicar jugada sugerida» para jugarla.")
        lines = [
            f"{result.algorithm}  valor {result.value:g}",
            f"jugada: {result.action!r}",
            f"nodos generados {result.generated}, evaluados {result.evaluated}, "
            f"podados {result.pruned}",
            f"profundidad alcanzada {result.depth_reached}, tiempo {result.time_seconds:.4f} s",
            "valores en la raíz:",
        ]
        lines += [f"  {action!r}: {value:g}" for action, value in result.root_values]
        self._write(self.output, "\n".join(lines))
        self.redraw()

    def apply_suggestion(self) -> None:
        if self.suggestion is None:
            self.hint.set("Primero pulsa «Ejecutar» con Minimax o Alfa-beta.")
            return
        self._play(self.suggestion)

    # ---- automatic mode ------------------------------------------------------------------
    def toggle_auto(self) -> None:
        if self.auto_job is not None:
            self.stop_auto()
        elif self.session.outcome() is None:
            self.auto_button.configure(text="⏸ Pausar partida automática")
            self.hint.set("")
            self.auto_job = self.root.after(0, self._auto_step)

    def stop_auto(self) -> None:
        if self.auto_job is not None:
            self.root.after_cancel(self.auto_job)
            self.auto_job = None
        self.auto_button.configure(text="▶ Iniciar partida automática")

    def _auto_step(self) -> None:
        """Both sides play with the chosen algorithm, depth and order until the game ends."""
        self.auto_job = None
        if self.session.outcome() is not None:
            self.stop_auto()
            return
        self.play_ai_turn()
        if self.hint.get().startswith("Error") or self.session.outcome() is not None:
            self.stop_auto()
            return
        self.auto_job = self.root.after(int(self.speed.get()), self._auto_step)

    def play_ai_turn(self) -> None:
        name = self._algorithm_name()
        if name not in ADVERSARIAL_ALGORITHMS:
            name = "ALPHA_BETA"
        try:
            result = self.session.decide(
                name,
                self._int(self.depth, "La profundidad"),
                ORDER_LABELS.get(self.order.get(), "default"),
            )
        except (RunError, ValueError) as exc:
            self.hint.set(f"Error: {exc}")
            return
        if result.action is None:
            self.hint.set("La partida ya terminó.")
            return
        self._play(result.action)

    def wait_selected(self) -> None:
        action = self.session.wait_for(self.selected) if self.selected else None
        if action is None:
            self.hint.set("Elige primero una unidad del bando que tiene el turno.")
        else:
            self._play(action)

    def undo(self) -> None:
        self.stop_auto()
        if self.session.undo():
            self._clear_overlays()
            self.redraw()

    def reset(self) -> None:
        self.stop_auto()
        self.session.reset()
        self._clear_overlays()
        self.redraw()

    def open_scenario(self) -> None:
        path = filedialog.askopenfilename(
            title="Abrir escenario",
            filetypes=[("Escenario JSON", "*.json")],
            initialdir=Path("scenarios") if Path("scenarios").is_dir() else None,
        )
        if path:
            self.load(Path(path))

    def load(self, path: Path) -> None:
        """Atomic: an invalid scenario leaves the current game untouched (RF-34)."""
        try:
            scenario = load_scenario(path)
        except ScenarioError as exc:
            messagebox.showerror("Escenario inválido", "\n".join(exc.errors))
            return
        self.stop_auto()
        self.session = Session.start(scenario)
        self._load_defaults()
        self.root.title(f"TacticalGrid - {path.name}")
        self.redraw()

    # ---- helpers -------------------------------------------------------------------------
    @staticmethod
    def _int(var: tk.StringVar, label: str) -> int:
        try:
            return int(var.get())
        except ValueError as exc:
            raise RunError(f"{label} debe ser un número entero") from exc

    @staticmethod
    def _write(widget: tk.Text, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = tk.Tk()
    path = (
        args[0]
        if args
        else filedialog.askopenfilename(
            title="Abrir escenario", filetypes=[("Escenario JSON", "*.json")]
        )
    )
    if not path:
        return 0
    try:
        scenario = load_scenario(path)
    except ScenarioError as exc:
        print("\n".join(exc.errors), file=sys.stderr)
        return 2
    App(root, Session.start(scenario))
    root.mainloop()
    return 0
