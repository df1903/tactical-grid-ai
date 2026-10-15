# Estado actual

> Foto del momento: fase, tareas activas y avance. **Se sobrescribe en cada cierre de sesión**; el histórico va en `handoffs/`.

## Fase actual
Fase 2 — No informada y costos: **código y casos 1–2 completos y pusheados a `main` (`5441526`)**. Falta documentar los resultados en el informe y revisión cruzada. Siguiente: Fase 3 — A* y Beam Search. Entrega: 2026-10-21; el plan va atrasado frente a `roadmap.md`.

## Tareas activas
- [ ] Revisión cruzada de Jorge sobre `domain/`, `scenario/` y `algorithms/`
- [ ] Cerrar "Student validation" en docstrings de `legal_actions`, `apply`, `successors`, `load_scenario`, `bfs`, `dfs`, `ucs`, `verify_search`
- [ ] F3: A* con 2 heurísticas admisibles y Beam k = 1, 2, 4, 8 (casos 3–5)
- [ ] Re-planificar fechas F3–F6 y repartir trabajo entre los dos integrantes
- [ ] Decidir: función de utilidad y pesos (F4), librería de GUI (F5), formato de exportación (F6), meta de tiempo de Minimax y tamaño máximo de mapa
- [ ] Borrador de RF-13 y tabla esperado-vs-obtenido de los casos 1–2 para el informe técnico
- [ ] Conectar modo `busqueda` al punto de entrada (`__main__`) y a la GUI

## Avance
| Bloque | Estado |
|---|---|
| Configuración de contexto (`.context/`) | completada |
| F0 Setup | completada |
| F1 `domain/` y `scenario/` | completada; "Student validation" pendiente |
| F2 `algorithms/` (BFS, DFS, UCS, 6 métricas) | completada |
| F2 `experiments/verifier.py` (RF-42, chequeos 1–5) | completada; chequeo 6 queda para F4 |
| F2 casos 1–2 (`scenarios/caso_01_*`, `caso_02_*`) | completada, con test esperado vs. obtenido |
| Tests | 70 pasan; `ruff` y `mypy --strict` en verde |
| Commits F2 | 8 commits más cierre `5441526`, autor y committer Jorge, sin trailers; pusheados |
| F3–F6 | sin iniciar |
