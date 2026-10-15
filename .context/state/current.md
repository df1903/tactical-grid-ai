# Estado actual

> Foto del momento: fase, tareas activas y avance. **Se sobrescribe en cada cierre de sesión**; el histórico va en `handoffs/`.

## Fase actual
Fase 1 — Modelo y escenario **completada y fusionada a `main`** (2026-10-14). Siguiente: Fase 2 — No informada y costos (BFS, DFS, UCS, métricas, verificador). Entrega: 2026-10-21; el plan va atrasado frente a `roadmap.md`.

## Tareas activas
- [ ] Revisión cruzada de Jorge sobre `domain/` y `scenario/` (se fusionó a `main` sin ella)
- [ ] Cerrar "Student validation" en los docstrings de `legal_actions`, `apply`, `successors` y `load_scenario`
- [ ] F2: BFS, DFS, UCS con las 6 métricas y verificador (casos 1–2)
- [ ] Re-planificar fechas F2–F6 y repartir trabajo entre los dos integrantes
- [ ] Decidir: función de utilidad y pesos (F4), librería de GUI (F5), formato de exportación (F6), meta de tiempo de Minimax y tamaño máximo de mapa
- [ ] Borrador de RF-13 (por qué el estado es suficiente) para el informe técnico

## Avance
| Bloque | Estado |
|---|---|
| Configuración de contexto (`.context/`) | completada |
| F0 Setup | completada |
| F1 `domain/` (`model.py`, `rules.py`) | completada; "Student validation" pendiente |
| F1 `scenario/loader.py` | completada: 9 validaciones + celda compartida, carga atómica |
| F1 tests | 38 pasan; `ruff` y `mypy --strict` en verde |
| Commits en `main` | `4015fe5` (F1), `bbb861b` (handoff 004), pusheados |
| F2–F6 | sin iniciar |
