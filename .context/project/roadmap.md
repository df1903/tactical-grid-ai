# Roadmap

> Fases planeadas del proyecto completo, con objetivo y criterio de salida. La fase actual vive en `state/current.md`; este archivo es el plan, no dónde estás.
> Fechas propuestas por Claude (delegadas por el usuario) el 2026-10-07; entrega y sustentación: 2026-10-21. El 2026-10-20 es colchón.

## Fase 0 — Setup (2026-10-07 a 2026-10-08)
- Objetivo: proyecto `uv`, estructura de carpetas, `pytest`/`ruff`/`mypy`.
- Criterio de salida: `uv run pytest` y `ruff` corren en verde.

## Fase 1 — Modelo y escenario (2026-10-08 a 2026-10-10)
- Objetivo: estado compuesto, sucesores, carga y validación atómica del JSON.
- Criterio de salida: las 9 validaciones tienen test; el caso 6 pasa.

## Fase 2 — No informada y costos (2026-10-10 a 2026-10-12)
- Objetivo: BFS, DFS, UCS, métricas y verificador.
- Criterio de salida: casos 1–2 con resultado esperado vs. obtenido.

## Fase 3 — Informada (2026-10-12 a 2026-10-14)
- Objetivo: A* con 2 heurísticas y Beam con k = 1, 2, 4, 8.
- Criterio de salida: casos 3–5 documentados.

## Fase 4 — Adversarial (2026-10-14 a 2026-10-17)
- Objetivo: Minimax, alfa-beta, utilidad, profundidad y orden configurables.
- Criterio de salida: casos 7–10; ambos algoritmos dan la misma decisión.

## Fase 5 — GUI mínima (2026-10-16 a 2026-10-18, solapa con F4)
- Objetivo: visualización de RF-40; GUI avanzada opcional.
- Criterio de salida: se carga un JSON externo y se ve todo lo exigido.

## Fase 6 — Cierre (2026-10-18 a 2026-10-20)
- Objetivo: experimentos, informe técnico, manual, README, tag de Git, ensayo de sustentación.
- Criterio de salida: lista de chequeo final del enunciado completa.

## Después de configurar (sin fecha)
- Crear un agente revisor que valide cada tarea contra su DoD y las convenciones, y responda sí o qué falta (petición del usuario). `<pendiente>`
