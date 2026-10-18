import csv
import json
from pathlib import Path

import pytest

from helpers import APENDICE_A, SCENARIOS
from tactical_grid.__main__ import main
from tactical_grid.experiments.runner import RunOptions
from tactical_grid.experiments.sweep import Sweep, expand, flatten, run_sweep, write_csv
from tactical_grid.scenario.loader import load_scenario

CASE_5 = SCENARIOS / "caso_05_beam_k.json"
CASE_7 = SCENARIOS / "caso_07_decision_adversarial.json"


def test_expand_combines_only_what_applies() -> None:
    scenario = load_scenario(CASE_5)
    sweep = Sweep(
        algorithms=("BFS", "A_STAR", "BEAM"),
        heuristics=("H1", "H2"),
        ks=(1, 2, 4, 8),
        depths=(1, 2),  # ignored in search mode
    )
    runs = expand(scenario, sweep)
    assert len(runs) == 1 + 2 + 2 * 4
    assert [r.k for r in runs if r.algorithm == "BEAM"] == [1, 2, 4, 8, 1, 2, 4, 8]


def test_expand_adversarial_depth_and_order_grid() -> None:
    scenario = load_scenario(CASE_7)
    sweep = Sweep(
        base=RunOptions(mode="adversarial"),
        algorithms=("MINIMAX", "ALPHA_BETA"),
        depths=(1, 2, 3),
        orders=("default", "reversed"),
    )
    assert len(expand(scenario, sweep)) == 2 * 3 * 2


def test_depth_sweep_reproduces_case_10() -> None:
    reports = run_sweep(
        load_scenario(CASE_7),
        Sweep(base=RunOptions(mode="adversarial"), algorithms=("ALPHA_BETA",), depths=(1, 2, 3)),
    )
    assert [r["valor"] for r in reports] == [-2.5, -3.5, -1.0]
    assert [r["nodos_evaluados"] for r in reports] == [11, 25, 412]
    assert reports[2]["valores_raiz"][0]["accion"].startswith("Move(unit_id='A1'")


def test_flatten_makes_a_flat_row() -> None:
    report = run_sweep(
        load_scenario(APENDICE_A), Sweep(algorithms=("UCS",), base=RunOptions(verify=True))
    )[0]
    row = flatten(report)
    assert row["camino"].startswith("0,1;") and row["verificacion_ok"] is True
    assert all(not isinstance(value, list | dict) for value in row.values())


def test_csv_and_json_exports(tmp_path: Path) -> None:
    csv_path, json_path = tmp_path / "out.csv", tmp_path / "out.json"
    code = main(
        [
            str(CASE_5),
            "--algorithm", "BEAM",
            "--k", "1,2,4,8",
            "--csv", str(csv_path),
            "--json", str(json_path),
        ]
    )  # fmt: skip
    assert code == 0
    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["algoritmo"] for row in rows] == ["BEAM_K1", "BEAM_K2", "BEAM_K4", "BEAM_K8"]
    assert [row["exito"] for row in rows] == ["False", "True", "True", "True"]
    assert [row["estados_generados"] for row in rows] == ["9", "43", "50", "46"]
    saved = json.loads(json_path.read_text(encoding="utf-8"))
    assert [r["costo"] for r in saved][1:] == [30.0, 28.0, 28.0]
    assert saved[0]["camino"] == []


def test_csv_with_mixed_modes_uses_the_union_of_columns(tmp_path: Path) -> None:
    path = tmp_path / "mixed.csv"
    write_csv(path, [{"a": 1}, {"a": 2, "b": 3}])
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines == ["a,b", "1,", "2,3"]


def test_cli_prints_a_list_for_several_runs(capsys: pytest.CaptureFixture[str]) -> None:
    assert (
        main(
            [
                str(CASE_7),
                "--mode",
                "adversarial",
                "--algorithm",
                "MINIMAX,ALPHA_BETA",
                "--depth",
                "2",
            ]
        )
        == 0
    )
    reports = json.loads(capsys.readouterr().out)
    assert [r["algoritmo"] for r in reports] == ["MINIMAX", "ALPHA_BETA"]


def test_cli_rejects_a_bad_list(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main([str(CASE_5), "--k", "1,x"])
    assert "invalid list" in capsys.readouterr().err


def test_cli_reports_unwritable_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main([str(APENDICE_A), "--algorithm", "BFS", "--csv", str(tmp_path / "no" / "x.csv")])
    assert code == 2 and "error:" in capsys.readouterr().err
