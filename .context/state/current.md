# Estado actual

> Foto del momento: fase, tareas activas y avance. **Se sobrescribe en cada cierre de sesión**; el histórico va en `handoffs/`.

## Fase actual
F4 y F5 cerradas, F6 casi cerrada. Hecho en `main`: algoritmos, CLI, exportación/barridos, GUI mínima tkinter (`643dbf8`), medición de rendimiento, informe técnico, manual de usuario y tabla de casos (`docs/`). Siguiente: "Student validation", revisión cruzada, tag. Entrega: 2026-10-21 (quedan 4 días).

## Tareas activas
- [ ] Probar la GUI a mano con los escenarios del equipo
- [ ] Revisión cruzada de Jorge sobre `domain/`, `scenario/` y `algorithms/`
- [ ] Cerrar "Student validation" en los docstrings (`legal_actions`, `apply`, `successors`, `load_scenario`, `bfs`, `dfs`, `ucs`, `verify_search`, `manhattan`, `obstacle_aware`, `a_star`, `beam_search`, `utility`, `minimax`, `alpha_beta`, `verify_adversarial`, `run`, `expand`)
- [ ] Releer los documentos de `docs/` (informe, manual, casos) y confirmar RF-13 y justificación RF-22
- [ ] Tag de Git de la versión entregada y ensayo de sustentación

## Avance
| Bloque | Estado |
|---|---|
| Configuración de contexto (`.context/`) | completada |
| F0 Setup, F1 `domain/` y `scenario/` | completadas; "Student validation" pendiente |
| F2 BFS, DFS, UCS, verificador, casos 1–2 | completada |
| F3 heurísticas, A*, Beam, casos 3–5 | completada |
| F4 utilidad, Minimax, alfa-beta, chequeo 6, casos 7–10 | completada |
| Caso 6, CLI `__main__`, `experiments/runner.py`, campos de `prueba` (G10) | completada |
| Barridos y exportación CSV/JSON (`experiments/sweep.py`) | completada |
| Tests | 172 pasan (1 skip); `ruff` y `mypy --strict` en verde |
| Autoría de commits | F1–F2 y F4 Jorge; F3 y desde la CLI Daniel; sin trailers |
| Rendimiento Minimax 15×15 | medido; dentro de la meta (decisions.md 2026-10-17) |
| F5 GUI mínima (`python -m tactical_grid.gui`) | completada y commiteada |
| Documentos (`docs/technical-report.md`, `user-manual.md`, `cases.md`, `results/`) | redactados; falta releer |
| Tag | sin iniciar |
