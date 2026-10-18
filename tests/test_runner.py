import json
from pathlib import Path

import pytest

from helpers import APENDICE_A, SCENARIOS
from tactical_grid.__main__ import main
from tactical_grid.domain.model import Position
from tactical_grid.experiments.runner import RunError, RunOptions, canonical, run
from tactical_grid.scenario.loader import load_scenario

CASE_7 = SCENARIOS / "caso_07_decision_adversarial.json"
CASE_5 = SCENARIOS / "caso_05_beam_k.json"


def test_json_prueba_section_drives_the_search() -> None:
    # Appendix A declares mode busqueda, unit A1 and goal (3,2); the algorithm is an override.
    report = run(load_scenario(APENDICE_A), RunOptions(algorithm="UCS", verify=True))
    assert report["exito"] is True
    assert report["camino"][0] == [0, 1] and report["camino"][-1] == [3, 2]
    assert all(check["ok"] for check in report["verificacion"])
    assert {"estados_generados", "estados_expandidos", "maximo_frontera", "costo"} <= set(report)


@pytest.mark.parametrize("alias", ["A*", "a_estrella", "A-STAR", "astar"])
def test_a_star_aliases(alias: str) -> None:
    assert canonical(alias) == "A_STAR"


def test_heuristic_and_beam_width_are_options() -> None:
    scenario = load_scenario(CASE_5)
    h1 = run(scenario, RunOptions(algorithm="A_STAR", heuristic="H1"))
    h2 = run(scenario, RunOptions(algorithm="A_STAR", heuristic="H2"))
    assert (h1["algoritmo"], h2["algoritmo"]) == ("A_STAR_H1", "A_STAR_H2")
    assert h1["costo"] == h2["costo"] == 28.0
    narrow = run(scenario, RunOptions(algorithm="BEAM", k=1))
    wide = run(scenario, RunOptions(algorithm="BEAM", k=4))
    assert narrow["exito"] is False and wide["exito"] is True


def test_adversarial_mode_uses_the_depth_of_the_json() -> None:
    scenario = load_scenario(CASE_7)  # juego.profundidad_maxima_minimax = 3
    report = run(scenario, RunOptions(mode="adversarial", algorithm="MINIMAX", verify=True))
    assert report["profundidad"] == 3 and report["valor"] == 3.0
    assert report["nodos_generados"] == 234 and report["nodos_podados"] == 0
    assert all(check["ok"] for check in report["verificacion"])
    deeper = run(scenario, RunOptions(mode="adversarial", algorithm="ALPHA_BETA", depth=4))
    assert deeper["profundidad_alcanzada"] == 4 and deeper["nodos_podados"] > 0


def test_game_mode_describes_the_loaded_game() -> None:
    report = run(load_scenario(CASE_7), RunOptions(mode="partida"))
    assert report["turno"] == "A" and report["portador"] is None
    assert report["recurso"] == [0, 1] and report["unidades"]["B1"]["celda"] == [1, 2]


@pytest.mark.parametrize(
    "options",
    [
        RunOptions(),  # Appendix A has mode but no algorithm
        RunOptions(algorithm="MINIMAX"),  # not a search algorithm
        RunOptions(algorithm="BEAM"),  # no k
        RunOptions(algorithm="BEAM", k=0),
        RunOptions(algorithm="A_STAR", heuristic="H9"),
        RunOptions(algorithm="BFS", unit="Z9"),
        RunOptions(algorithm="BFS", goal=Position(99, 99)),
        RunOptions(algorithm="BFS", mode="nonsense"),
        RunOptions(mode="adversarial", algorithm="BFS"),
        RunOptions(mode="adversarial", algorithm="MINIMAX", depth=0),
        RunOptions(mode="adversarial", algorithm="MINIMAX", order="random"),
    ],
)
def test_invalid_options_raise_run_error(options: RunOptions) -> None:
    with pytest.raises(RunError):
        run(load_scenario(APENDICE_A), options)


def test_cli_prints_a_json_report(capsys: pytest.CaptureFixture[str]) -> None:
    code = main([str(CASE_7), "--mode", "adversarial", "--algorithm", "MINIMAX", "--depth", "2"])
    report = json.loads(capsys.readouterr().out)
    assert code == 0 and report["algoritmo"] == "MINIMAX" and report["profundidad"] == 2


def test_cli_search_overrides(capsys: pytest.CaptureFixture[str]) -> None:
    code = main([str(APENDICE_A), "--algorithm", "BFS", "--goal", "3,2", "--unit", "A1"])
    assert code == 0 and json.loads(capsys.readouterr().out)["exito"] is True


def test_cli_reports_every_scenario_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    broken = json.loads(APENDICE_A.read_text(encoding="utf-8"))
    broken["mapa"]["filas"] = 9
    broken["turno"] = "x"
    path = tmp_path / "broken.json"
    path.write_text(json.dumps(broken), encoding="utf-8")
    assert main([str(path)]) == 2
    err = capsys.readouterr().err
    assert "invalid scenario" in err and err.count("  - ") >= 2


def test_cli_reports_run_errors_and_missing_files(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(APENDICE_A)]) == 2
    assert "error:" in capsys.readouterr().err
    assert main(["no_such_file.json"]) == 2
    assert "invalid scenario" in capsys.readouterr().err


def test_cli_without_arguments_prints_usage(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "usage" in capsys.readouterr().out


def test_20x20_scenario_with_three_units_per_side() -> None:
    scenario = load_scenario(SCENARIOS / "prueba_20x20.json")
    board = scenario.board
    assert (board.rows, board.cols) == (20, 20)
    sides = [side for side in board.unit_sides.values()]
    assert sides.count(sides[0]) == 3 and len(sides) == 6
    report = run(scenario, RunOptions(verify=True))
    assert report["algoritmo"] == "ALPHA_BETA" and report["profundidad"] == 4
    assert all(check["ok"] for check in report["verificacion"])
    search = run(
        scenario, RunOptions(mode="busqueda", algorithm="A_STAR", unit="A1", goal=Position(18, 17))
    )
    assert search["exito"] is True


def test_15x15_performance_scenario_decides_within_the_time_target() -> None:
    scenario = load_scenario(SCENARIOS / "prueba_15x15.json")
    assert (scenario.board.rows, scenario.board.cols) == (15, 15)
    report = run(scenario, RunOptions(depth=5))
    assert report["algoritmo"] == "ALPHA_BETA" and report["tiempo_segundos"] < 5.0
