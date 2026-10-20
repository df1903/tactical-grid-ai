import json
from pathlib import Path
from typing import Any

import pytest

from helpers import SCENARIOS
from tactical_grid.__main__ import main
from tactical_grid.domain.dynamic import DynamicRules
from tactical_grid.experiments.runner import RunError, RunOptions, run
from tactical_grid.scenario.loader import (
    DEFAULT_DYNAMIC_RULES,
    ScenarioError,
    build_scenario,
    load_scenario,
)

CASE_7 = SCENARIOS / "caso_07_decision_adversarial.json"
CASE_11 = SCENARIOS / "caso_11_dinamico.json"


def _raw(**juego: Any) -> dict[str, Any]:
    raw: dict[str, Any] = json.loads(CASE_7.read_text(encoding="utf-8"))
    raw["juego"] = {**raw["juego"], **juego}
    return raw


def test_existing_scenarios_keep_the_base_variant() -> None:
    scenario = load_scenario(CASE_7)
    assert scenario.variant == "base"
    assert scenario.dynamic_rules == DEFAULT_DYNAMIC_RULES


def test_the_dynamic_scenario_reads_its_parameters_from_the_json() -> None:
    scenario = build_scenario(_raw(variante="dinamica", penalizacion_placaje=4, inmunidad_robo=0))
    assert scenario.variant == "dinamica"
    assert scenario.dynamic_rules == DynamicRules(tackle_penalty=4, steal_immunity=0)


@pytest.mark.parametrize(
    "juego",
    [{"variante": "otra"}, {"penalizacion_placaje": -1}, {"inmunidad_robo": 1.5}],
)
def test_invalid_variant_fields_are_rejected(juego: dict[str, Any]) -> None:
    with pytest.raises(ScenarioError):
        build_scenario(_raw(**juego))


def test_the_base_report_is_unchanged_and_the_dynamic_one_is_tagged() -> None:
    scenario = load_scenario(CASE_7)
    base = run(scenario, RunOptions(depth=2))
    dynamic = run(scenario, RunOptions(depth=2, variant="dinamica", verify=True))
    assert "variante" not in base
    assert dynamic["variante"] == "dinamica"
    assert all(check["ok"] for check in dynamic["verificacion"])


def test_the_json_selects_the_variant_and_the_option_overrides_it() -> None:
    scenario = load_scenario(CASE_11)
    assert run(scenario, RunOptions(depth=2))["variante"] == "dinamica"
    assert "variante" not in run(scenario, RunOptions(depth=2, variant="base"))


def test_unknown_variant_option_is_a_run_error() -> None:
    with pytest.raises(RunError):
        run(load_scenario(CASE_7), RunOptions(depth=1, variant="otra"))


def test_alpha_beta_and_minimax_agree_through_the_runner() -> None:
    scenario = load_scenario(CASE_11)
    full = run(scenario, RunOptions(algorithm="MINIMAX", depth=3))
    pruned = run(scenario, RunOptions(algorithm="ALPHA_BETA", depth=3))
    assert (full["valor"], full["accion"]) == (pruned["valor"], pruned["accion"])


def test_the_cli_accepts_variant(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(CASE_7), "--variant", "dinamica", "--depth", "2"]) == 0
    assert json.loads(capsys.readouterr().out)["variante"] == "dinamica"


def test_the_base_case_files_were_not_modified(tmp_path: Path) -> None:
    out = tmp_path / "base.json"
    args = [str(CASE_7), "--algorithm", "MINIMAX,ALPHA_BETA", "--depth", "1,2,3"]
    assert main([*args, "--order", "default,reversed", "--json", str(out)]) == 0
    saved = json.loads(
        (Path(__file__).parent.parent / "docs/results/casos_07_10_adversarial.json").read_text(
            encoding="utf-8"
        )
    )
    expected = {
        (r["algoritmo"], r["profundidad"], r["orden_acciones"]): r
        for r in saved
        if r["profundidad"] <= 3
    }
    for report in json.loads(out.read_text(encoding="utf-8")):
        old = expected[(report["algoritmo"], report["profundidad"], report["orden_acciones"])]
        for key in ("accion", "valor", "nodos_generados", "nodos_evaluados", "nodos_podados"):
            assert report[key] == old[key]
