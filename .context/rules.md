# Rules

> Reglas de negocio del dominio: validaciones, invariantes, cálculos. **Negocio, no estilo ni infra** (eso es `conventions.md` y `constraints.md`).

## Reglas
- Movimiento en 4 direcciones (arriba, abajo, izquierda, derecha). *(decisión 2026-10-07)*
- El costo se paga al entrar a la celda destino; la celda inicial no cuesta. Costos y transitabilidad salen del catálogo `tipos_terreno` del JSON.
- Una unidad por celda: no se comparte celda. Las bases y la celda del recurso pueden pisarse si están libres; la base rival `<pendiente>` confirmar si se puede pisar.
- Juego por turnos: en cada turno el bando activo elige una unidad y ejecuta una acción válida. Acciones: mover y esperar.
- Ambos bandos tienen las mismas reglas; MAX y MIN son roles del árbol, no agentes distintos.
- Un solo tipo de unidad (`estandar`), mínimo 3 por bando.
- Una unidad recoge el recurso al llegar a su celda; mientras lo lleva, debe alcanzar su propia base. Gana el bando que lleva el recurso a su base.
- Pérdida del portador: si una unidad rival queda adyacente al portador (interceptación), el recurso cae en la celda del portador. *(propuesta aprobada; detalle del desempate y de quién intercepta `<pendiente>`)*
- Fin de partida: victoria al entregar el recurso; empate al alcanzar el límite de turnos configurable. Un bando sin movimientos pasa turno.
- Estado compuesto: posición y bando de cada unidad, portador del recurso (o posición del recurso si nadie lo lleva) y turno. Dos estados con la misma posición pueden ser distintos (RF-11).
- Una heurística es admisible solo si no sobreestima con los costos del escenario: se escala por el costo transitable mínimo leído del JSON.
- Con misma profundidad, utilidad y orden de acciones, Minimax y alfa-beta producen la misma decisión.
- La utilidad se define desde un bando; MAX la maximiza y MIN la minimiza. Función exacta y pesos: `<pendiente>`.
- Normalización del JSON: bandos `A`/`a` se aceptan y se pasan a mayúscula; costos numéricos positivos (enteros o decimales); terrenos no transitables pueden omitir `costo`.
- Un escenario es válido solo si cumple las 9 validaciones mínimas (RF-35).
- La verificación comprueba movimientos válidos, sin obstáculos, costo coincidente, estado final objetivo, sin estados inválidos y acciones legales en Minimax (RF-42).
