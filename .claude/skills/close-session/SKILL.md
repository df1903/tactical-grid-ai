---
name: close-session
description: Cierra una sesión de trabajo: actualiza el estado actual, crea el siguiente handoff numerado y registra decisiones. Úsala cuando el usuario diga "cerrar sesión", "guardar progreso" o "crear handoff".
disable-model-invocation: true
metadata:
  version: "1.0"
---
# Cierre de sesión

1. Lee `.context/state/current.md` y el último `.context/handoffs/NNN.md` (si existe).
2. **Sobrescribe** `.context/state/current.md` con la foto actual: fase, tareas activas (quita las cerradas), avance.
3. Si existe `.context/state/known-issues.md`, añade los bugs nuevos y quita los resueltos.
4. Crea `.context/handoffs/<NNN+1>.md` (3 dígitos, empieza en `001`) siguiendo `references/handoff-template.md`. Nunca edites un handoff anterior.
5. Registra decisiones nuevas: globales en `.context/project/decisions.md`; de una feature en su `sdd-NNN-<slug>/decisions.md`. Una entrada por decisión (contexto, decisión, alternativas descartadas, fecha). No borres entradas.
6. Muestra un resumen de 5 líneas máximo con lo que cambió. No hagas commit salvo que el usuario lo pida.
