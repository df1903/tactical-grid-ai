import tkinter as tk
from dataclasses import replace
from types import SimpleNamespace

import pytest

from helpers import APENDICE_A, SCENARIOS
from tactical_grid.domain.model import Move, Position, Tackle
from tactical_grid.gui import app as gui
from tactical_grid.gui.app import (
    SPECS,
    App,
    action_arrow,
    describe_action,
    trace_decision,
    trace_search,
)
from tactical_grid.scenario.loader import load_scenario

CASE_3 = SCENARIOS / "caso_03_obstaculo_heuristica.json"
CASE_5 = SCENARIOS / "caso_05_beam_k.json"
CASE_7 = SCENARIOS / "caso_07_decision_adversarial.json"
CASE_11 = SCENARIOS / "caso_11_dinamico.json"
ADVERSARIAL_PARAMS = {
    "depth": "2",
    "order": "default",
    "w_delivery": "10",
    "w_carry": "3",
    "w_goal_distance": "1",
    "w_rival_distance": "0.5",
    "w_rival_progress": "0.5",
}


# ---------------------------------------------------------------- lógica sin pantalla
def test_every_algorithm_of_the_selector_is_registered() -> None:
    assert list(SPECS) == [
        "BFS",
        "DFS",
        "UCS",
        "A*",
        "Beam",
        "Minimax",
        "Alfa-beta",
        "Minimax dinámico",
        "Alfa-beta dinámico",
    ]
    assert [name for name, spec in SPECS.items() if spec.adversarial] == [
        "Minimax",
        "Alfa-beta",
        "Minimax dinámico",
        "Alfa-beta dinámico",
    ]


def test_dfs_neighbor_order_changes_the_expansion() -> None:
    scenario = load_scenario(SCENARIOS / "caso_01_bfs_vs_dfs.json")
    default = trace_search(scenario, "DFS", {"neighbor_order": "default"})
    reverse = trace_search(scenario, "DFS", {"neighbor_order": "reversed"})
    assert default.expanded_cells != reverse.expanded_cells
    assert reverse.result.cost < default.result.cost


def test_informed_searches_use_the_chosen_heuristic_and_width() -> None:
    scenario = load_scenario(CASE_3)
    h1 = trace_search(scenario, "A*", {"heuristic": "h1"}).result
    h2 = trace_search(scenario, "A*", {"heuristic": "h2"}).result
    assert h1.cost == h2.cost and h2.expanded < h1.expanded
    beam = load_scenario(CASE_5)
    assert not trace_search(beam, "Beam", {"heuristic": "h1", "k": "1"}).result.success
    assert trace_search(beam, "Beam", {"heuristic": "h1", "k": "4"}).result.success


@pytest.mark.parametrize("bad", ["x", "0", ""])
def test_a_bad_beam_width_is_a_readable_error(bad: str) -> None:
    with pytest.raises(ValueError, match="ancho k"):
        trace_search(load_scenario(CASE_5), "Beam", {"heuristic": "h1", "k": bad})


def test_decision_matches_between_minimax_and_alpha_beta() -> None:
    scenario = load_scenario(CASE_7)
    plain = trace_decision(scenario, "Minimax", ADVERSARIAL_PARAMS)
    pruned = trace_decision(scenario, "Alfa-beta", ADVERSARIAL_PARAMS)
    assert (plain.action, plain.value) == (pruned.action, pruned.value)
    assert pruned.generated < plain.generated


def test_a_path_algorithm_is_not_a_decision_and_vice_versa() -> None:
    scenario = load_scenario(APENDICE_A)
    with pytest.raises(ValueError, match="adversarial"):
        trace_decision(scenario, "BFS")
    with pytest.raises(ValueError, match="camino"):
        trace_search(scenario, "Minimax")


def test_actions_are_described_and_drawn_from_the_unit() -> None:
    state = load_scenario(CASE_7).initial_state
    move = Move("A1", Position(8, 11))
    tackle = Tackle("A1", "B1")
    assert describe_action(move) == "A1 -> (8, 11)"
    assert describe_action(tackle) == "A1 placa a B1"
    assert action_arrow(state, move) == (Position(9, 11), Position(8, 11))
    assert action_arrow(state, tackle) == (Position(9, 11), state.position_of("B1"))


# ---------------------------------------------------------------- ventana (necesita pantalla)
@pytest.fixture(scope="module")
def root():
    # one Tk for the whole module: creating and destroying many of them is flaky on Windows
    try:
        tk_root = tk.Tk()
    except tk.TclError:
        pytest.skip("no display available for tkinter")
    tk_root.withdraw()
    yield tk_root
    tk_root.destroy()


@pytest.fixture
def window(root: tk.Tk):
    gui.RESPONSE_MILLISECONDS = 1
    app = App(root)
    yield app
    app._cancel_animation()
    for child in root.winfo_children():
        child.destroy()


def _click(app: App, row: int, col: int) -> SimpleNamespace:
    size = gui.CANVAS_PIXELS / max(app.scenario.board.rows, app.scenario.board.cols)  # type: ignore[union-attr]
    return SimpleNamespace(x=(col + 0.5) * size, y=(row + 0.5) * size)


def test_window_switches_parameters_with_the_algorithm(window: App) -> None:
    window.load(str(CASE_3))
    window.algorithm.set("DFS")
    window.on_algorithm_changed()
    assert list(window.param_vars) == ["neighbor_order"]
    window.algorithm.set("Beam")
    window.on_algorithm_changed()
    assert list(window.param_vars) == ["heuristic", "k"]
    window.algorithm.set("Alfa-beta")
    window.on_algorithm_changed()
    assert "depth" in window.param_vars and "w_rival_progress" in window.param_vars
    assert str(window.step_button.cget("state")) == "disabled"


def test_window_runs_a_search_and_verifies_it(window: App) -> None:
    window.load(str(APENDICE_A))
    window.algorithm.set("A*")
    window.on_algorithm_changed()
    window.verify.set(True)
    window.run_all_at_once()
    assert window.trace is not None and window.trace.result.success
    assert "todo correcto" in window.summary.cget("text")
    assert "Búsqueda de camino" in window.turn_label.cget("text")


def test_window_applies_a_move_and_the_rival_answers(window: App) -> None:
    window.load(str(CASE_7))
    window.algorithm.set("Alfa-beta")
    window.on_algorithm_changed()
    window.param_vars["depth"].set("2")
    window.verify.set(True)
    window.apply_move()
    assert window.game_state is not None and window.game_state.turn_number == 1
    assert "todo correcto" in window.summary.cget("text")
    window.root.update()
    window.root.after(20)
    window.root.update()
    assert window.game_state.turn_number == 2 and not window.busy
    assert window.history[0].startswith("1. A:") and window.history[1].startswith("2. B:")


def test_window_plays_a_manual_move_by_clicks(window: App) -> None:
    window.load(str(CASE_7))
    window.algorithm.set("Alfa-beta")
    window.on_algorithm_changed()
    window.param_vars["depth"].set("1")
    window._on_click(_click(window, 9, 11))  # A1, next to the resource
    assert window.selected == "A1"
    window._on_click(_click(window, 9, 12))  # a free neighbor
    assert window.game_state is not None
    assert window.game_state.position_of("A1") == Position(9, 12)
    assert window.history[0].endswith("(manual)")
    assert "Turno del bando" in window.turn_label.cget("text")


def test_clicking_a_rival_unit_does_not_select_it(window: App) -> None:
    window.load(str(CASE_7))
    window.algorithm.set("Minimax")
    window.on_algorithm_changed()
    window._on_click(_click(window, 10, 8))  # B1 on A's turn
    assert window.selected is None


def test_dynamic_decisions_agree_and_are_verified() -> None:
    scenario = load_scenario(CASE_11)
    full = trace_decision(scenario, "Minimax dinámico", ADVERSARIAL_PARAMS)
    pruned = trace_decision(scenario, "Alfa-beta dinámico", ADVERSARIAL_PARAMS)
    assert (full.value, full.action) == (pruned.value, pruned.action)


def test_window_preselects_the_dynamic_algorithm_and_plays_with_recovery(window: App) -> None:
    window.load(str(CASE_11))
    assert window.algorithm.get() == "Alfa-beta dinámico"
    window.on_algorithm_changed()
    window.param_vars["depth"].set("1")
    window.verify.set(True)
    window._on_click(_click(window, 9, 11))  # A1, next to the resource
    window._on_click(_click(window, 9, 12))  # camino: no recovery
    assert window.dyn_state is not None and window.dyn_state.recovery_of("A1") == 0
    assert window.game_state is window.dyn_state.base
    window.root.update()
    window.root.after(20)
    window.root.update()
    assert window.game_state.turn_number == 2 and not window.busy
    assert "recuperación" in window.turn_label.cget("text")


def test_window_shows_the_recovery_after_entering_a_swamp(window: App) -> None:
    window.load(str(CASE_11))
    window.on_algorithm_changed()
    base = window._state()
    # A2 junto al pantano (5, 6) de caso_11
    moved = tuple((uid, Position(6, 6) if uid == "A2" else pos) for uid, pos in base.positions)
    window.game_state = replace(base, positions=moved)
    window._apply(Move("A2", Position(5, 6)))
    assert window.dyn_state is not None
    assert window.dyn_state.recovery_of("A2") == 2
    window.draw(0)
    assert "A2 2" in window.turn_label.cget("text")
