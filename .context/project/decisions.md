# Decisiones (globales del proyecto)

> Decisiones que afectan a todo el proyecto (las de una feature van en `sdd-NNN-<slug>/decisions.md`). Cronológico, **nunca se borra**. Una entrada por decisión.

## 2026-10-07 — Stack: Python 3.14 con uv, pytest, ruff y mypy
- Contexto: el enunciado no fija lenguaje ni herramientas; el curso usa Python.
- Decisión: Python 3.14, `uv` para entorno y ejecución; calidad con `pytest`, `ruff`, `mypy --strict` (el usuario delegó la elección). GUI sin elegir.
- Alternativas descartadas: `<pendiente>` (no se discutieron otras).

## 2026-10-07 — Reglas del juego: 4 direcciones, costo al entrar, una unidad por celda
- Contexto: el enunciado deja abiertas vecindad, semántica del costo y ocupación (G2–G4).
- Decisión: 4 direcciones, costo al entrar a la celda destino (la inicial no cuesta), una unidad por celda. Con 4 direcciones Manhattan es admisible.
- Alternativas descartadas: 8 direcciones y celdas compartidas (mayor ramificación en Minimax).

## 2026-10-07 — Unidades, acciones, pérdida del portador y fin de partida
- Contexto: el enunciado exige reglas deterministas (RF-09) sin definir el mecanismo.
- Decisión: un solo tipo de unidad; acciones mover y esperar; si un rival intercepta al portador (adyacente), el recurso cae en su celda; límite de turnos configurable que da empate; el bando sin movimientos pasa turno.
- Alternativas descartadas: tipos de unidad distintos y acciones de bloqueo o protección (complejidad innecesaria).

## 2026-10-07 — Arquitectura en cinco componentes
- Contexto: RNF-05 exige separar lógica, escenario, algoritmos e interfaz.
- Decisión: `domain`, `scenario`, `algorithms`, `gui`, `experiments`; datos en `scenarios/*.json`, sin base de datos.
- Alternativas descartadas: `<pendiente>`.

## 2026-10-07 — Idioma, compatibilidad del JSON y convenciones
- Contexto: el JSON de ejemplo mezcla mayúsculas/minúsculas y puede traer costos decimales.
- Decisión: código y documentos en inglés (`.context/` queda en español); bandos `A`/`a` normalizados; costos numéricos positivos; terrenos no transitables sin `costo`; commits convencionales y revisión cruzada.
- Alternativas descartadas: identificadores en español.

## 2026-10-07 — Alcance: solo lo que pide el enunciado; GUI mínima obligatoria
- Contexto: el usuario planteó la GUI como opcional, pero RF-40 exige una GUI que muestre ciertos elementos (5 % de la nota).
- Decisión: GUI mínima obligatoria, GUI avanzada opcional; nada fuera del enunciado.
- Alternativas descartadas: omitir la GUI (incumple RF-40).

## 2026-10-07 — Permisos de Claude Code para el flujo de calidad
- Contexto: evitar prompts repetidos al ejecutar tests, lint y la app.
- Decisión: `permissions.allow` incluye `uv sync`, `uv run pytest*`, `ruff check*`, `ruff format*`, `mypy*` y `python -m tactical_grid*`; sin `bypassPermissions`.
- Alternativas descartadas: `bypassPermissions` (prohibido por el usuario); `ruff format --check*` solo (pendiente de revisar).

## 2026-10-07 — Permiso de formato limitado a `--check`
- Contexto: `ruff format*` permitía reescribir archivos sin confirmación (pendiente de la decisión anterior).
- Decisión: `permissions.allow` usa `uv run ruff format --check*`; el formato que modifica archivos pide confirmación.
- Alternativas descartadas: mantener `ruff format*` abierto.

## 2026-10-07 — Versiones de herramientas y proyecto `uv` como librería
- Contexto: F0 exigía fijar versiones de `pytest`, `ruff` y `mypy` y crear el proyecto.
- Decisión: `uv init --lib` (layout `src/`, build `uv_build`), Python 3.14, `pytest` 9.1.1, `ruff` 0.16.10 (reglas E, F, I, UP, B), `mypy` 2.4.0 en `--strict`; versiones fijadas por `uv.lock`.
- Alternativas descartadas: layout plano sin `src/`.
