# Conventions

> Estilo no obvio, ubicación de archivos y nombres. Se lee **antes de crear un archivo nuevo**. Se actualiza al cambiar una convención.

## Estilo no obvio
<!-- Patrones a seguir/evitar que no se ven leyendo el código. No dupliques lo que ya aplica el linter/formatter. -->
- Type hints obligatorios; `mypy --strict` sobre `src`.
- Estados inmutables: `@dataclass(frozen=True)`.
- Docstrings con los 7 campos (Purpose, Preconditions, Postconditions, Complexity, AI usage, AI intervention, Student validation) solo en métodos con lógica relevante: búsquedas, heurísticas, sucesores, costos, utilidad, Minimax, alfa-beta, validadores.
- Convención de desempate en toda búsqueda: se expande primero el nodo que entró antes a la frontera; si aparece un camino más barato a un nodo conocido, se actualiza.
- Si se usa aleatoriedad, con semilla fija (reproducibilidad).
- Las claves del JSON en español (`fila`, `bando`) solo se leen en `scenario/`; el dominio usa inglés.
- Commits convencionales (`feat:`, `fix:`, `test:`, `docs:`); una rama por fase y revisión cruzada entre los dos integrantes antes de fusionar a `main`.

## Dónde va cada archivo (código)
<!-- Estructura de carpetas del código fuente: qué va en cada una. -->
- `src/tactical_grid/domain/` — estado compuesto, acciones, sucesores, costos, reglas del juego.
- `src/tactical_grid/scenario/` — carga y validación atómica del JSON.
- `src/tactical_grid/algorithms/` — BFS, DFS, UCS, A*, heurísticas, Beam, Minimax, alfa-beta, utilidad; sin conocer la GUI.
- `src/tactical_grid/gui/` — interfaz gráfica.
- `src/tactical_grid/experiments/` — métricas, verificador y casos mínimos.
- `tests/` — pruebas automáticas.
- `scenarios/` — escenarios JSON.
- `docs/` — informe técnico y manual de usuario.

## Nombres
- Archivos y funciones: `snake_case`; clases: `PascalCase`; identificadores en inglés.
- Nombres canónicos de algoritmo: `BFS`, `DFS`, `UCS`, `A_STAR`, `BEAM`, `MINIMAX`, `ALPHA_BETA`; se acepta `A_ESTRELLA` como alias.
- Archivos de `.context/`: `kebab-case-descriptivo.md`.
- Series numeradas con prefijo de 3 dígitos (`001`, `002`...). Nunca mezclar formatos en una misma serie.
- No existe carpeta "otros": elige la categoría más cercana.

## Dónde va la información en `.context/`
1. ¿Afecta a todo el proyecto y persiste más allá de una feature? → `project/decisions.md`.
2. ¿Es específico de una feature en curso? → `sdd-NNN-<slug>/decisions.md`.
3. ¿Es el estado actual (foto del momento)? → `state/`.
4. ¿Es historia de qué pasó en una sesión? → `handoffs/`.

Estado se sobrescribe; historia se acumula (`handoffs/`, `decisions.md`).

## Cuándo crear `sdd-NNN-<slug>/`
Cuando tiene ciclo propio (planning → implementación → testing → done) **y** no cabe en una sola tarea de `state/current.md`. Si es puntual, va en `state/current.md`.
