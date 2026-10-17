import tkinter as tk
from types import SimpleNamespace

import pytest

from helpers import APENDICE_A, SCENARIOS
from tactical_grid.domain.model import Position
from tactical_grid.gui.app import App
from tactical_grid.gui.session import Session
from tactical_grid.scenario.loader import load_scenario


@pytest.fixture
def root():
    try:
        window = tk.Tk()
    except tk.TclError:
        pytest.skip("no display available for tkinter")
    window.withdraw()
    yield window
    window.destroy()


def test_window_draws_runs_a_search_and_plays_a_move(root: tk.Tk) -> None:
    app = App(root, Session.start(load_scenario(APENDICE_A)))
    assert app.canvas.find_all()
    app.algorithm.set("A* - Búsqueda informada")
    app.run_algorithm()
    assert app.path and app.path[-1] == Position(3, 2)

    app.load(SCENARIOS / "caso_07_decision_adversarial.json")
    app.algorithm.set("Alfa-beta")
    app.run_algorithm()
    assert app.suggestion is not None
    app.apply_suggestion()
    assert app.session.state.turn_number == 1
    assert "bando B" in app.turn_label.cget("text")


def test_click_selects_and_moves_a_unit(root: tk.Tk) -> None:
    app = App(root, Session.start(load_scenario(SCENARIOS / "caso_07_decision_adversarial.json")))
    cell = app._cell_size()

    def click(row: int, col: int) -> SimpleNamespace:
        return SimpleNamespace(x=(col + 0.5) * cell, y=(row + 0.5) * cell)

    app._on_left_click(click(1, 0))  # A1
    assert app.selected == "A1"
    app._on_left_click(click(2, 0))
    assert app.session.state.position_of("A1") == Position(2, 0)


def test_automatic_mode_plays_until_the_game_ends(
    root: tk.Tk, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("tactical_grid.gui.app.messagebox.showinfo", lambda *a, **k: None)
    app = App(root, Session.start(load_scenario(SCENARIOS / "caso_07_decision_adversarial.json")))
    app.algorithm.set("Alfa-beta")
    app.depth.set("2")
    app.speed.set(0)
    app.toggle_auto()
    for _ in range(400):
        root.update()
        if app.auto_job is None:
            break
    assert app.auto_job is None
    assert app.session.outcome() is not None
    assert app.auto_button.cget("text").startswith("▶")


def test_automatic_mode_can_be_paused(root: tk.Tk) -> None:
    app = App(root, Session.start(load_scenario(SCENARIOS / "caso_07_decision_adversarial.json")))
    app.speed.set(1000)
    app.toggle_auto()
    assert app.auto_job is not None
    app.toggle_auto()
    assert app.auto_job is None
