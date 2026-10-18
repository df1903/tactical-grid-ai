# Estado actual

> Foto del momento: fase, tareas activas y avance. **Se sobrescribe en cada cierre de sesión**; el histórico va en `handoffs/`.

## Fase actual
Primera versión estable lista para etiquetar (`v1.0.0`): algoritmos, reglas con placaje, utilidad por movimientos restantes, GUI única con parámetros por algoritmo, escenarios en una carpeta, resultados regenerados y documentos al día. Entrega y sustentación: 2026-10-21.

## Tareas activas
- [ ] Ensayo de sustentación (predicción razonada, modificación pequeña, escenario externo, explicar el placaje y la utilidad)
- [ ] Probar la GUI a mano con los escenarios del equipo (la lógica y la ventana tienen tests)
- [ ] Decidir si se añade un término de costo de terreno a la utilidad (known-issues.md)

## Avance
| Bloque | Estado |
|---|---|
| Configuración de contexto (`.context/`) | completada |
| Dominio, escenario, BFS/DFS/UCS, A*/Beam, Minimax/alfa-beta, verificador, CLI, barridos | completados |
| Placaje como acción (reemplaza la interceptación automática) | completado (decisions.md 2026-10-18) |
| Utilidad por movimientos restantes con distancias reales | completada (decisions.md 2026-10-18) |
| GUI única (`gui/app.py`) con verificación y juego manual | completada |
| Escenarios en `scenarios/` y `caso_07` en 20×20 con 3 unidades | completado |
| Casos 7–10 recalculados; resultados CSV/JSON regenerados | completado |
| Student validation y AI usage en docstrings | cerrado por el equipo |
| Documentos (`docs/`) | actualizados a esta versión |
| Tests | 200+ pasan; `ruff` y `mypy --strict` en verde |
| Tag | `v1.0.0` |
