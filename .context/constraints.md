# Constraints

> Restricciones no negociables. **Prevalecen si una propuesta choca con ellas; no se cambian sin una decisión registrada** en `project/decisions.md`.

## Técnicas
- Costos, posiciones, dimensiones y nombres de terreno nunca van codificados en los algoritmos; salen del JSON (RF-03, RNF-04).
- No se modifica el código para adaptarlo al mapa de la sustentación (RNF-03).
- Carga de escenario atómica: un JSON inválido se rechaza sin dejar el sistema parcialmente modificado (RF-34).
- Los nombres de campos y valores del JSON definidos por el enunciado se respetan; se permiten campos extra propios (RNF-01, RNF-02).
- MAX y MIN tienen exactamente las mismas reglas y capacidades; son roles del árbol (RF-07).
- Separación obligatoria entre lógica del juego, escenario, algoritmos e interfaz (RNF-05).
- Profundidad de Minimax configurable sin tocar código (RF-26).
- Mínimo 20×20 en desarrollo, pero se aceptan otras dimensiones; mínimo 3 unidades por bando.
- Documentación de métodos con lógica relevante: Purpose, Preconditions, Postconditions, Complexity, AI usage, AI intervention, Student validation; debe coincidir con la implementación (RD-01).
- Código, docstrings, README y documento técnico en inglés.
- Python 3.14 con `uv`.

## Infra / despliegue
- Solo Windows con Python 3.14 (confirmado). Sin servicios ni despliegue; se ejecuta en local.

## Legales o de negocio
- Todo uso de IA se declara (herramienta y propósito) en los docstrings y en el informe técnico; omitirlo deliberadamente es inconsistencia (integridad académica).
- Cada integrante debe poder explicar y modificar cualquier parte del código.
- El repositorio y los documentos corresponden a la misma versión sustentada (RE-02).
- Fecha límite: 2026-10-21.
- No hay otras restricciones de la universidad o del profesor conocidas.

## Rendimiento
- Meta de tiempo por decisión de Minimax a la profundidad por defecto (≈10 s): `<pendiente>` hasta medir.
- Tamaño máximo de mapa: `<pendiente>`.
