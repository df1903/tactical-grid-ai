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

## 2026-10-14 — Base rival no pisable e interceptación sin transferencia
- Contexto: `rules.md` dejaba abiertos si se pisa la base rival y el detalle de la interceptación; bloqueaba F1.
- Decisión: la base rival no se puede pisar. Interceptación: se evalúa tras cualquier movimiento que deje a un rival adyacente al portador; el recurso cae en la celda del portador (sin transferencia, sin desempate); el portador original no lo recoge mientras siga en esa celda; otra unidad lo recoge al llegar.
- Alternativas descartadas: evaluar solo tras el movimiento del rival; transferir el recurso al interceptor (exigía desempate por ID).

## 2026-10-07 — Versiones de herramientas y proyecto `uv` como librería
- Contexto: F0 exigía fijar versiones de `pytest`, `ruff` y `mypy` y crear el proyecto.
- Decisión: `uv init --lib` (layout `src/`, build `uv_build`), Python 3.14, `pytest` 9.1.1, `ruff` 0.16.10 (reglas E, F, I, UP, B), `mypy` 2.4.0 en `--strict`; versiones fijadas por `uv.lock`.
- Alternativas descartadas: layout plano sin `src/`.

## 2026-10-14 — Supuestos de F1: costo de espera, límite de turnos y orden de resolución
- Contexto: implementar `domain/` y `scenario/` exigió fijar detalles que `rules.md` no cubría.
- Decisión: `Wait` cuesta 0; `juego.limite_turnos` es un campo propio opcional (default 100, definido en `scenario/`); en un mismo movimiento la entrega gana sobre la interceptación; recoger solo ocurre al llegar a la celda (`Wait` no recoge); `Wait` siempre es legal. No se exige el mínimo de 3 unidades por bando al cargar porque el Apéndice A trae 2; sí se rechaza que dos unidades compartan celda (validación extra a las 9).
- Alternativas descartadas: costo de espera 1 (penaliza quedarse quieto en UCS sin necesidad); exigir 3 unidades (rechazaría el ejemplo oficial).

## 2026-10-14 — Atribución de commits de F1 y saltos de línea fijos
- Contexto: el usuario pidió que los commits de F1 figuren con su compañero Jorge; Git avisaba LF→CRLF en cada commit.
- Decisión: los commits de F1 tienen a Jorge Iván Garcia Torres como autor y committer, sin trailers `Co-Authored-By` (ni de Claude); el uso de IA sigue declarado en docstrings e informe técnico. `.gitattributes` fija `* text=auto eol=lf`.
- Alternativas descartadas: Jorge solo como coautor (primera petición, corregida por el usuario); dejar `core.autocrlf` por defecto.

## 2026-10-14 — Modelo de la búsqueda de un solo agente (F2)
- Contexto: RF-14 ignora al adversario; el Apéndice A pone a B1 sobre la celda objetivo, así que tratar a los rivales como obstáculos dejaba el ejemplo sin solución.
- Decisión: el problema de búsqueda quita las unidades rivales (la base rival sigue sin poder pisarse), mueve solo la unidad de inicio (sus compañeros quedan quietos), no alterna turno, ignora el recurso y no usa `Wait`. El estado de búsqueda equivale a la posición de la unidad. Reglas y costos salen de `domain.successors`.
- Alternativas descartadas: rivales quietos como obstáculos (ejemplo oficial sin solución); estado compuesto completo con recurso y turno (infla estados sin aportar a un problema de camino).

## 2026-10-14 — Convenciones de BFS, DFS y UCS (F2)
- Contexto: el enunciado define las métricas pero no cuándo se prueba la meta ni cómo se cuentan duplicados.
- Decisión: búsqueda en grafo; meta probada al expandir; el estado inicial cuenta como generado; un estado no se genera dos veces (se omite si ya está en frontera o expandido); orden de sucesores arriba, abajo, izquierda, derecha; DFS empuja los hijos en orden inverso para expandir primero el primero. UCS: desempate por orden de entrada a la frontera, la actualización de costo conserva ese orden y no cuenta como generado; el máximo de frontera cuenta estados distintos en espera. El camino incluye la celda inicial y la longitud son los movimientos.
- Alternativas descartadas: meta al generar (menos generados, pero UCS exige expandir); árbol sin lista de explorados (explosión en DFS).

## 2026-10-14 — Atribución de commits de F2
- Contexto: el usuario pidió commits pequeños de F2 con Jorge como autor.
- Decisión: autor y committer Jorge Iván Garcia Torres, sin trailers `Co-Authored-By`, igual que en F1; el uso de IA sigue declarado en los docstrings y el informe técnico.
- Alternativas descartadas: dejar a Daniel como committer.
