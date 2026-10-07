# Estado actual

> Foto del momento: fase, tareas activas y avance. **Se sobrescribe en cada cierre de sesión**; el histórico va en `handoffs/`.

## Fase actual
Fase 0 — Setup **cerrada** (2026-10-07). Siguiente: Fase 1 — Modelo y escenario (2026-10-08 a 2026-10-10).

## Tareas activas
- [ ] F1: estado compuesto inmutable y sucesores en `domain/` (usar plan mode; leer `rules.md`)
- [ ] F1: carga y validación atómica del JSON en `scenario/` (9 validaciones con test; caso 6)
- [ ] **Primero**: resolver (ver `rules.md`, líneas 8 y 13): si se puede pisar la base rival; detalle de la interceptación (quién intercepta y desempate)

## Avance
| Bloque | Estado |
|---|---|
| Configuración de contexto (`.context/`) | completada |
| Permisos en `.claude/settings.json` | aplicados (`ruff format --check*`) |
| F0 Setup | completada (100 %); `README.md` creado, enunciado en `docs/enunciado.md` |
| Commits en `main` | `ec50e7b` (F0), `f231726` (README y `docs/`); cambio de `current.md` sin commit |
| F1–F6 | sin iniciar |
