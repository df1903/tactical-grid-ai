# Estado actual

> Foto del momento: fase, tareas activas y avance. **Se sobrescribe en cada cierre de sesión**; el histórico va en `handoffs/`.

## Fase actual
Versión final `v1.1.0` (en `main`): variante dinámica de reglas (opcional) y modo `partida` completo (terminal y GUI, persona contra IA e IA contra IA). Documentación al día. Entrega y sustentación: 2026-10-21.

## Tareas activas
- [ ] Ensayo de sustentación (predicción razonada, modificación pequeña, escenario externo, explicar el placaje, la utilidad y la variante dinámica)
- [ ] Probar a mano la GUI nueva («Juegas», «Partida automática», algoritmos dinámicos) y `--play humano` en una terminal real (la lógica y la ventana tienen tests)
- [ ] Decidir si se añade un término de costo de terreno a la utilidad base (known-issues.md)

## Avance
| Bloque | Estado |
|---|---|
| Configuración de contexto (`.context/`) | completada |
| Dominio, escenario, BFS/DFS/UCS, A*/Beam, Minimax/alfa-beta, verificador, CLI, barridos | completados |
| Placaje como acción y utilidad por movimientos restantes | completados (decisions.md 2026-10-18) |
| GUI única (`gui/app.py`) con verificación y juego manual | completada |
| Variante dinámica (`domain/dynamic.py`, utilidad, Minimax/alfa-beta, verificador, `--variant`, GUI, `caso_11`) | completada en la rama (decisions.md 2026-10-19) |
| Modo `partida` completo (`experiments/game.py`, `--play`, GUI «Juegas» y «Partida automática») | completado en la rama (decisions.md 2026-10-19) |
| Documentos (`docs/`, README) | actualizados: variante, partida, caso 11 extra, informe 3.1 y 10.6 |
| Tests | 283 pasan; `ruff` y `mypy --strict` en verde; cada commit de la rama pasa por separado |
| Tag | `v1.1.0` (versión final); `v1.0.0` = versión estable previa |
