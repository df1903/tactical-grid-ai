# Estado actual

> Foto del momento: fase, tareas activas y avance. **Se sobrescribe en cada cierre de sesión**; el histórico va en `handoffs/`.

## Fase actual
Fase 3 — Informada: **código y casos 3–5 completos, commiteados en local (sin push)**. Falta documentar resultados en el informe y revisión cruzada. Siguiente: Fase 4 — Minimax y alfa-beta. Entrega: 2026-10-21 (quedan 5 días).

## Tareas activas
- [ ] Push de F3 a `main`
- [ ] Revisión cruzada de Jorge sobre `domain/`, `scenario/` y `algorithms/`
- [ ] Cerrar "Student validation" en docstrings de `legal_actions`, `apply`, `successors`, `load_scenario`, `bfs`, `dfs`, `ucs`, `verify_search`, `manhattan`, `obstacle_aware`, `a_star`, `beam_search`
- [ ] F4: Minimax y alfa-beta con la utilidad decidida el 2026-10-16 (casos 7–10) y chequeo 6 del verificador
- [ ] Conectar modo `busqueda` al punto de entrada (`__main__`) y a la GUI; definir campos de `prueba` (G10)
- [ ] Informe: tabla esperado-vs-obtenido de los casos 1–5, RF-13 y justificación RF-22 de las dos heurísticas

## Avance
| Bloque | Estado |
|---|---|
| Configuración de contexto (`.context/`) | completada |
| F0 Setup, F1 `domain/` y `scenario/` | completadas; "Student validation" pendiente |
| F2 BFS, DFS, UCS, verificador, casos 1–2 | completada (pusheada) |
| F3 heurísticas, A*, Beam, casos 3–5 | completada, sin push |
| Tests | 92 pasan; `ruff` y `mypy --strict` en verde |
| Commits F3 | autor y committer Daniel, sin trailers |
| F4–F6 | sin iniciar |
