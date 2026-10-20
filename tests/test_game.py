import json

import pytest

from helpers import SCENARIOS
from tactical_grid.__main__ import main
from tactical_grid.domain.model import Side
from tactical_grid.experiments.game import play_game
from tactical_grid.experiments.runner import RunError, RunOptions, run
from tactical_grid.scenario.loader import load_scenario

CASE_7 = SCENARIOS / "caso_07_decision_adversarial.json"


def test_ai_vs_ai_plays_to_a_terminal_state() -> None:
    scenario = load_scenario(CASE_7)
    report = run(scenario, RunOptions(mode="partida", play="auto", algorithm="ALPHA_BETA", depth=1))
    assert report["terminada"] is True and report["abandonada"] is False
    assert report["jugadores"] == {"A": "IA", "B": "IA"}
    assert report["ganador"] in ("A", "B", None)
    assert report["turnos_jugados"] >= len(report["jugadas"])
    # los bandos se alternan: las dos partes usan las mismas reglas y el mismo algoritmo
    sides = [move["bando"] for move in report["jugadas"]]
    assert sides[0] == "A" and all(a != b for a, b in zip(sides, sides[1:], strict=False))
    assert all(move["jugador"] == "IA" for move in report["jugadas"])


def test_minimax_and_alpha_beta_play_the_same_game() -> None:
    scenario = load_scenario(CASE_7)
    plain = run(scenario, RunOptions(mode="partida", play="auto", algorithm="MINIMAX", depth=1))
    pruned = run(scenario, RunOptions(mode="partida", play="auto", algorithm="ALPHA_BETA", depth=1))
    assert [m["accion"] for m in plain["jugadas"]] == [m["accion"] for m in pruned["jugadas"]]
    assert plain["ganador"] == pruned["ganador"]


def test_human_plays_and_the_ai_answers() -> None:
    scenario = load_scenario(CASE_7)
    answers = iter(["x", "0", "1", "q"])  # invalid, invalid, first legal action, then quits
    shown: list[str] = []
    report = play_game(
        scenario, "ALPHA_BETA", 1, "default", False, Side.A, lambda _p: next(answers), shown.append
    )
    assert report["abandonada"] is True and report["ganador"] is None
    assert report["jugadores"] == {"A": "persona", "B": "IA"}
    # primera jugada de A: la persona; luego responde la IA (B)
    assert [(m["bando"], m["jugador"]) for m in report["jugadas"]] == [
        ("A", "persona"),
        ("B", "IA"),
    ]
    assert any("Opción no válida" in line for line in shown)
    assert any("Partida abandonada" in line for line in shown)


def test_human_can_play_side_b_and_quit_on_closed_input() -> None:
    scenario = load_scenario(CASE_7)

    def closed(_prompt: str) -> str:
        raise EOFError

    report = play_game(scenario, "ALPHA_BETA", 1, "default", False, Side.B, closed, lambda _t: None)
    # A (IA) abre y B (persona) no responde: se abandona
    assert report["abandonada"] is True
    assert [m["jugador"] for m in report["jugadas"]] == ["IA"]


def test_dynamic_variant_also_plays() -> None:
    scenario = load_scenario(SCENARIOS / "caso_11_dinamico.json")
    report = run(
        scenario,
        RunOptions(mode="partida", play="auto", depth=1, variant="dinamica"),
    )
    assert report["variante"] == "dinamica" and report["terminada"] is True


@pytest.mark.parametrize(
    "options",
    [
        RunOptions(mode="partida", play="otro"),
        RunOptions(mode="partida", play="humano", side="C"),
        RunOptions(mode="partida", play="auto", side="A"),
        RunOptions(mode="partida", play="auto", depth=0),
        RunOptions(mode="partida", play="auto", algorithm="BFS"),
        RunOptions(mode="adversarial", play="auto", algorithm="MINIMAX"),
    ],
)
def test_invalid_game_options_raise_run_error(options: RunOptions) -> None:
    with pytest.raises(RunError):
        run(load_scenario(CASE_7), options)


def test_cli_plays_a_game_and_prints_the_report(capsys: pytest.CaptureFixture[str]) -> None:
    code = main([str(CASE_7), "--mode", "partida", "--play", "auto", "--depth", "1"])
    report = json.loads(capsys.readouterr().out)
    assert code == 0 and report["modo"] == "partida" and report["terminada"] is True


def test_partida_without_play_still_describes_the_game() -> None:
    report = run(load_scenario(CASE_7), RunOptions(mode="partida"))
    assert report["recurso"] == [8, 11] and "jugadas" not in report
