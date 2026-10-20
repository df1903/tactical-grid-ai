# Rules

> Reglas de negocio del dominio: validaciones, invariantes, cálculos. **Negocio, no estilo ni infra** (eso es `conventions.md` y `constraints.md`).

## Reglas
- Movimiento en 4 direcciones (arriba, abajo, izquierda, derecha). *(decisión 2026-10-07)*
- El costo se paga al entrar a la celda destino; la celda inicial no cuesta. Costos y transitabilidad salen del catálogo `tipos_terreno` del JSON.
- Una unidad por celda: no se comparte celda. Las bases y la celda del recurso pueden pisarse si están libres; la base rival **no** se puede pisar. *(decisión 2026-10-14)*
- Juego por turnos: en cada turno el bando activo elige una unidad y ejecuta una acción válida: mover o placar (no existe esperar: al mover una unidad las demás quedan quietas). Mover cuesta el costo del terreno destino. Si el bando activo no tiene ningún movimiento legal y la partida no terminó, pasa turno (no es una acción). *(decisión 2026-10-17)*
- Ambos bandos tienen las mismas reglas; MAX y MIN son roles del árbol, no agentes distintos.
- Un solo tipo de unidad (`estandar`), mínimo 3 por bando en los escenarios propios; el cargador no lo exige porque el Apéndice A trae 2. *(decisión 2026-10-14)*
- Una unidad recoge el recurso al llegar a su celda; mientras lo lleva, debe alcanzar su propia base. Gana el bando que lleva el recurso a su base. Recoger ocurre solo al llegar a la celda (una unidad quieta no recoge). Orden dentro de un movimiento: recoger, entrega (gana). Mover nunca hace perder el recurso por sí solo. *(decisión 2026-10-14; revisada 2026-10-18)*
- Pérdida del portador (placaje): `Tackle(unidad, portador)` es una acción legal para una unidad del bando con el turno que está **adyacente al portador rival** al empezar su turno. Efecto: el recurso cae en la celda del portador (no se transfiere; ninguna unidad se mueve), el turno pasa y cuesta 0. El portador original no puede recogerlo mientras siga en esa celda; debe salir y volver, y cualquier otra unidad lo recoge al llegar. Estar adyacente solo amenaza: el portador puede huir o entregar antes del placaje. *(reemplaza la interceptación automática del 2026-10-14; decisión 2026-10-18)*
- Fin de partida: victoria al entregar el recurso; empate al alcanzar el límite de turnos, campo propio `juego.limite_turnos` (opcional, default 100). Al terminar la partida no hay acciones legales. *(decisión 2026-10-14)*
- Estado compuesto: posición y bando de cada unidad, portador del recurso (o posición del recurso si nadie lo lleva) y turno. Dos estados con la misma posición pueden ser distintos (RF-11).
- Una heurística es admisible solo si no sobreestima con los costos del escenario: se escala por el costo transitable mínimo leído del JSON.
- Con misma profundidad, utilidad y orden de acciones, Minimax y alfa-beta producen la misma decisión.
- Variante dinámica (opcional, `juego.variante: dinamica`; la base es el default y no cambia): entrar a una celda de costo `c` deja a la unidad `ceil(c) − 1` turnos propios sin actuar (no mueve ni placa, pero puede ser placada); el placaje roba el recurso (el que placa pasa a ser el portador, la víctima espera `penalizacion_placaje` turnos como máximo con lo que tenía, el nuevo portador es inmune `inmunidad_robo` turnos del rival); robar sobre la base propia gana; un bando bloqueado pasa y sus contadores bajan. Parámetros del JSON, no del código. *(decisión 2026-10-19)*
- Modo `partida`: los dos bandos juegan con las mismas reglas, algoritmo, profundidad, orden y pesos; MAX es quien mueve en cada decisión. La persona elige entre las mismas `legal_actions` que usa la búsqueda. *(decisión 2026-10-19)*
- La utilidad se define desde un bando; MAX la maximiza y MIN la minimiza. Mide los movimientos que le faltan a cada bando para ganar con distancias reales en el mapa: `U = progreso_rival·faltan(MIN) − distancia_objetivo·faltan(MAX) ± recurso_cargado ± distancia_rival·(pasos del perseguidor más cercano al portador)`; un triunfo vale más que cualquier otro estado (y antes vale más), el empate vale 0. Pesos por defecto 10 / 3 / 1 / 0.5 / 0.5 desde el JSON. *(decisión 2026-10-18)*
- Normalización del JSON: bandos `A`/`a` se aceptan y se pasan a mayúscula; costos numéricos positivos (enteros o decimales); terrenos no transitables pueden omitir `costo`.
- Un escenario es válido solo si cumple las 9 validaciones mínimas (RF-35) y, además, ninguna unidad comparte celda con otra.
- La verificación comprueba movimientos válidos, sin obstáculos, costo coincidente, estado final objetivo, sin estados inválidos y acciones legales en Minimax (RF-42).
