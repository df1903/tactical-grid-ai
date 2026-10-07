# AGENTS.md

> Fuente portable de instrucciones para agentes de IA. Mantén este archivo corto: solo hechos y reglas.
> El detalle vive en `.context/` y se lee **bajo demanda** (no lo cargues todo de entrada).

## Proyecto
TacticalGrid: juego táctico 2D por turnos (cuadrícula, bandos A y B, un recurso que se lleva a la base propia) usado como entorno para BFS, DFS, UCS, A*, Beam Search, Minimax y alfa-beta. Proyecto 1 de Sistemas Inteligentes I (UCALDAS), equipo de 2 (Jorge Iván Garcia Torres, Daniel Felipe Franco Rincón). Entrega y sustentación: 2026-10-21. Estado: desde cero, fase F0.

## Comandos
- Instalar: `uv sync`
- Ejecutar: `uv run python -m tactical_grid`
- Tests: `uv run pytest`
- Lint/format: `uv run ruff check .` · `uv run ruff format --check .` · tipos: `uv run mypy src`
- *(propuestos, pendientes de crear el proyecto `uv` en F0)*

## Inicio de sesión (leer en este orden)
1. `.context/state/current.md`
2. El último `.context/handoffs/NNN.md` (si existe)
3. Si la tarea pertenece a una feature con spec: su `.context/sdd-NNN-<slug>/`

## Conocimiento del proyecto (leer solo si hace falta)
| Cuándo | Archivo |
|---|---|
| Antes de añadir una dependencia o tecnología | `.context/stack.md` (si no está aquí, no está aprobado: pregunta) |
| Antes de proponer algo estructural | `.context/constraints.md` (prevalece sobre tus propuestas) |
| Antes de crear un archivo o nombrar algo | `.context/conventions.md` |
| Al tocar la lógica del dominio | `.context/rules.md` *(si existe)* |
| Al cambiar componentes o su comunicación | `.context/architecture.md` *(si existe)* |
| Al tomar o consultar decisiones previas | `.context/project/decisions.md` |
| Bugs ya conocidos (no los redescubras ni arregles sin que se pida) | `.context/state/known-issues.md` *(si existe)* |

## Cómo trabajar
- Cambios pequeños y verificables; ejecuta los tests antes de dar algo por terminado.
- Si hay ambigüedad en el alcance, pregunta antes de implementar.
- No añadas dependencias, carpetas de primer nivel ni abstracciones que no se hayan pedido.
- Para features grandes, usa el flujo de specs (skill `new-feature-spec` si existe).
- Una decisión que persiste → regístrala en `project/decisions.md`.

## Reglas duras
- Nunca leas ni escribas `.env*`, claves ni credenciales (también lo bloquea un hook).
- Nunca hagas `push --force` ni borres historial de git.
- Ningún costo, nombre de terreno, dimensión ni posición va escrito en `domain/` ni `algorithms/`: todo sale del escenario JSON cargado.

## Cierre de sesión
Al terminar un bloque de trabajo relevante, ejecuta la skill `close-session`
(actualiza `state/`, crea el siguiente handoff y registra decisiones).
