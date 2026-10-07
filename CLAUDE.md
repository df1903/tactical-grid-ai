@AGENTS.md

## Específico de Claude Code
- Skills del proyecto: `.claude/skills/`. Subagentes: `.claude/agents/`.
- Usa plan mode antes de cambios que toquen `src/tactical_grid/domain/` (estado, sucesores, costos).
- Los archivos de `.context/` NO se importan: léelos con Read solo cuando la tabla de AGENTS.md lo indique.
- Preferencias personales (idioma, tono) van en `CLAUDE.local.md` o en `~/.claude/CLAUDE.md`, no aquí.
