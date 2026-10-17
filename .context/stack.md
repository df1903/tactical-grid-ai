# Stack

> Tecnologías aprobadas con versión y para qué se usa cada una. **Si no está aquí, no está aprobado: pregunta** antes de añadir una dependencia. Se actualiza al aprobar o retirar una tecnología.

## Lenguajes y versiones
- Python 3.14 — todo el código del proyecto.

## Frameworks y librerías
- `tkinter` (librería estándar de Python 3.14) — GUI mínima (RF-40); sin dependencia nueva. *(aprobado 2026-10-16)*
- `pytest` 9.1.1 — pruebas. *(delegado por el usuario; aprobado en la conversación del 2026-10-07)*
- Resto de librerías de ejecución: `<pendiente>`; por defecto, solo librería estándar (`json`, `time`, `dataclasses`).

## Infra y servicios
- Ninguno. Sin base de datos ni servicios externos; los escenarios son archivos JSON en `scenarios/`.

## Herramientas
- `uv` — entorno virtual, dependencias y ejecución (`uv run`).
- `ruff` 0.16.10 — lint y formato (línea de 100 caracteres; reglas E, F, I, UP, B).
- `mypy` 2.4.0 — verificación de tipos (`--strict` sobre `src`).
- Git — control de versiones, con etiqueta de la versión entregada.
