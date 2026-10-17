# Estado actual

> Foto del momento: fase, tareas activas y avance. **Se sobrescribe en cada cierre de sesión**; el histórico va en `handoffs/`.

## Fase actual
Fase 4 — Adversarial (sin GUI): **Minimax, alfa-beta, utilidad, chequeo 6 y casos 7–10 completos, commiteados localmente (autor Jorge), sin push**. Siguiente: F5 GUI mínima y conectar los modos de `prueba`. Entrega: 2026-10-21.

## Tareas activas
- [ ] Revisión cruzada de Jorge sobre `domain/`, `scenario/` y `algorithms/`
- [ ] Cerrar "Student validation" en docstrings de `legal_actions`, `apply`, `successors`, `load_scenario`, `bfs`, `dfs`, `ucs`, `verify_search`, `manhattan`, `obstacle_aware`, `a_star`, `beam_search`
- [ ] Push de F4 a `main` (pendiente de confirmar)
- [ ] Decidir si se ajustan los pesos de utilidad (limitación en decisions.md 2026-10-17)
- [ ] Conectar modo `busqueda` al punto de entrada (`__main__`) y a la GUI; definir campos de `prueba` (G10)
- [ ] Informe: tabla esperado-vs-obtenido de los casos 1–5 y 7–10, RF-13 y justificación RF-22 de las dos heurísticas

## Avance
| Bloque | Estado |
|---|---|
| Configuración de contexto (`.context/`) | completada |
| F0 Setup, F1 `domain/` y `scenario/` | completadas; "Student validation" pendiente |
| F2 BFS, DFS, UCS, verificador, casos 1–2 | completada (pusheada) |
| F3 heurísticas, A*, Beam, casos 3–5 | completada (pusheada) |
| F4 utilidad, Minimax, alfa-beta, chequeo 6, casos 7–10 | completada (sin push) |
| Tests | 126 pasan; `ruff` y `mypy --strict` en verde |
| Commits F3 | autor y committer Daniel, sin trailers |
| Commits F4 | autor y committer Jorge, sin trailers |
| F5–F6 | sin iniciar |
