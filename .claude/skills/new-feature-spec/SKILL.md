---
name: new-feature-spec
description: Crea la carpeta de una feature con spec (Spec-Driven Development) cuando tiene ciclo propio y no cabe en una tarea de state/current.md. Úsala al iniciar una feature grande.
disable-model-invocation: true
metadata:
  version: "1.0"
---
# Nueva feature con spec

1. Verifica el criterio de creación: la feature tiene ciclo propio (planning → implementación → testing → done) **y** no cabe en una tarea de `state/current.md`. Si no se cumple, dilo y no la crees.
2. Calcula el siguiente `NNN` mirando las carpetas `sdd-*` de `.context/` (3 dígitos, empieza en `001`).
3. Crea `.context/sdd-NNN-<slug>/` con `spec.md` (objetivo, alcance, criterios de aceptación), `plan.md` (pasos), `testing.md` (casos y resultado) y `decisions.md` (decisiones de la feature). Plantillas en `references/sdd-templates.md`.
4. Añade la feature a `state/current.md` y a `project/roadmap.md` si existe.
5. Al terminar la feature, indica cómo archivarla: mover a `.context/archive/` (crea esa carpeta solo en ese momento).
