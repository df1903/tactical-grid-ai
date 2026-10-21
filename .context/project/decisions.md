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
- Decisión: un solo tipo de unidad; acciones mover y esperar *(esperar eliminado el 2026-10-17)*; si un rival intercepta al portador (adyacente), el recurso cae en su celda; límite de turnos configurable que da empate; el bando sin movimientos pasa turno.
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
- Decisión: `Wait` cuesta 0 *(eliminado el 2026-10-17)*; `juego.limite_turnos` es un campo propio opcional (default 100, definido en `scenario/`); en un mismo movimiento la entrega gana sobre la interceptación; recoger solo ocurre al llegar a la celda (`Wait` no recoge) *(Wait eliminado el 2026-10-17)*. No se exige el mínimo de 3 unidades por bando al cargar porque el Apéndice A trae 2; sí se rechaza que dos unidades compartan celda (validación extra a las 9).
- Alternativas descartadas: costo de espera 1 (penaliza quedarse quieto en UCS sin necesidad); exigir 3 unidades (rechazaría el ejemplo oficial).

## 2026-10-14 — Atribución de commits de F1 y saltos de línea fijos
- Contexto: el usuario pidió que los commits de F1 figuren con su compañero Jorge; Git avisaba LF→CRLF en cada commit.
- Decisión: los commits de F1 tienen a Jorge Iván Garcia Torres como autor y committer, sin trailers `Co-Authored-By` (ni de Claude); el uso de IA sigue declarado en docstrings e informe técnico. `.gitattributes` fija `* text=auto eol=lf`.
- Alternativas descartadas: Jorge solo como coautor (primera petición, corregida por el usuario); dejar `core.autocrlf` por defecto.

## 2026-10-14 — Modelo de la búsqueda de un solo agente (F2)
- Contexto: RF-14 ignora al adversario; el Apéndice A pone a B1 sobre la celda objetivo, así que tratar a los rivales como obstáculos dejaba el ejemplo sin solución.
- Decisión: el problema de búsqueda quita las unidades rivales (la base rival sigue sin poder pisarse), mueve solo la unidad de inicio (sus compañeros quedan quietos), no alterna turno, ignora el recurso. El estado de búsqueda equivale a la posición de la unidad. Reglas y costos salen de `domain.successors`.
- Alternativas descartadas: rivales quietos como obstáculos (ejemplo oficial sin solución); estado compuesto completo con recurso y turno (infla estados sin aportar a un problema de camino).

## 2026-10-14 — Convenciones de BFS, DFS y UCS (F2)
- Contexto: el enunciado define las métricas pero no cuándo se prueba la meta ni cómo se cuentan duplicados.
- Decisión: búsqueda en grafo; meta probada al expandir; el estado inicial cuenta como generado; un estado no se genera dos veces (se omite si ya está en frontera o expandido); orden de sucesores arriba, abajo, izquierda, derecha; DFS empuja los hijos en orden inverso para expandir primero el primero. UCS: desempate por orden de entrada a la frontera, la actualización de costo conserva ese orden y no cuenta como generado; el máximo de frontera cuenta estados distintos en espera. El camino incluye la celda inicial y la longitud son los movimientos.
- Alternativas descartadas: meta al generar (menos generados, pero UCS exige expandir); árbol sin lista de explorados (explosión en DFS).

## 2026-10-14 — Atribución de commits de F2
- Contexto: el usuario pidió commits pequeños de F2 con Jorge como autor.
- Decisión: autor y committer Jorge Iván Garcia Torres, sin trailers `Co-Authored-By`, igual que en F1; el uso de IA sigue declarado en los docstrings y el informe técnico.
- Alternativas descartadas: dejar a Daniel como committer.

## 2026-10-16 — Función de utilidad y pesos (F4)
- Contexto: Minimax y alfa-beta necesitan una utilidad propia (RF-25 a RF-33); bloqueaba F4. Propuesta por Claude, aprobada por Daniel.
- Decisión: `U = 10·entregas + 3·(recurso cargado) − distancia_al_objetivo − 0.5·distancia_rival_al_portador`, desde la perspectiva del bando MAX. Los pesos salen del escenario JSON, no del código.
- Alternativas descartadas: utilidad solo por distancia al recurso (no distingue entre cargarlo y no cargarlo).

## 2026-10-16 — Librería de GUI: tkinter (F5)
- Contexto: RF-40 exige una GUI mínima; el stack no fijaba librería. Propuesta por Claude, aprobada por Daniel.
- Decisión: `tkinter`; viene con Python y no añade dependencia. Se registra en `stack.md` al empezar F5.
- Alternativas descartadas: Pygame (dependencia nueva sin necesidad para una GUI mínima).

## 2026-10-16 — Meta de tiempo de Minimax y tamaño máximo de mapa
- Contexto: el enunciado no fija límite de tiempo ni de mapa (G12 y pregunta 5). Propuesta por Claude, aprobada por Daniel.
- Decisión: meta de 5 s por jugada con profundidad configurable; mapa máximo de 15×15 para Minimax (BFS, DFS, UCS, A* y Beam no tienen tope más allá de la memoria).
- Alternativas descartadas: sin límite (riesgo en la sustentación).

## 2026-10-16 — Formato de exportación de resultados (F6)
- Contexto: RF-38 y RF-39 piden exportar resultados. Propuesta por Claude, aprobada por Daniel.
- Decisión: CSV para las métricas y JSON para las trazas.
- Alternativas descartadas: solo JSON (menos cómodo para tablas en el informe).

## 2026-10-16 — Reparto y calendario de F3–F6
- Contexto: el plan iba atrasado frente a `roadmap.md`; quedan 5 días. Propuesta por Claude, aprobada por Daniel.
- Decisión: F3 el 17, F4 el 18–19, F5 el 20, F6 el 21 (colchón absorbido). Daniel firma los commits de F3; la autoría de F4 en adelante queda por decidir.
- Alternativas descartadas: mantener las fechas originales del roadmap (ya vencidas).

## 2026-10-16 — Atribución de commits de F3
- Contexto: hasta F2 los commits salieron a nombre de Jorge; para F3 el usuario pidió firmarlos él.
- Decisión: los commits de F3 tienen a Daniel Felipe Franco Rincón como autor y committer, sin trailer `Co-Authored-By`; el uso de IA sigue declarado en docstrings e informe técnico.
- Alternativas descartadas: seguir con Jorge como autor (no participó en F3).

## 2026-10-16 — A* y Beam Search: heurísticas, desempate y criterio de poda (F3)
- Contexto: RF-20 a RF-24 y G9; el enunciado deja libres la segunda heurística y el criterio de Beam.
- Decisión: h1 = Manhattan × costo transitable mínimo del escenario; h2 (propuesta del equipo) = distancia en movimientos que rodea muros y la base rival (BFS inverso desde la meta) × costo mínimo; h2 ≥ h1 y ambas son admisibles y consistentes. A*: prioridad `f = g + h`, desempate por orden de entrada a la frontera (como UCS), con reapertura si aparece un camino más barato. Beam: por niveles, conserva los k candidatos con menor `f = g + h`, desempate por orden de generación; un estado ya conservado en un nivel anterior no vuelve a generarse; es incompleto (puede fallar). `max_frontier` cuenta los candidatos antes de podar.
- Alternativas descartadas: poda por `h` sola (Beam voraz, ignora el costo ya pagado); solo Manhattan escalada (la segunda heurística no aportaría nada que comparar en el caso 4).

## 2026-10-17 — Convenciones de Minimax, alfa-beta y utilidad (F4)
- Contexto: RF-25 a RF-33 y G11; la fórmula decidida el 2026-10-16 dejaba abiertos el signo del término del rival, la profundidad y los empates.
- Decisión: MAX es el bando que mueve en la raíz; una unidad de profundidad es una acción de un bando (los bandos alternan por ply; sin movimientos, el nodo se evalúa como hoja desde el 2026-10-17). Se evalúa utilidad en hojas de profundidad y en estados terminales. Utilidad: ±entrega (±10 si gana MAX/MIN) ± recurso cargado (±3), −1·distancia Manhattan al objetivo (base propia si MAX carga; el portador si MIN carga; el recurso si nadie carga; desde la unidad MAX más cercana o desde el portador) y +0.5·distancia del rival más cercano al portador solo cuando MAX carga (un rival cerca baja U). Los pesos salen de la sección opcional `utilidad` del JSON (`entrega`, `recurso_cargado`, `distancia_objetivo`, `distancia_rival`); los valores 10/3/1/0.5 solo aplican si falta la clave. En la raíz gana la primera acción (en el orden dado) con valor estrictamente mayor, así alfa-beta y Minimax coinciden en empates. `generated` cuenta cada estado hijo producido (alfa-beta genera perezosamente), `pruned` las acciones hermanas omitidas por un corte. Orden de acciones configurable: `default` (arriba, abajo, izquierda, derecha por unidad) o `reversed`. Profundidad mínima 1. Chequeo 6 del verificador: re-ejecución con `record=True` y comprobación de legalidad de cada acción considerada y de la elegida.
- Alternativas descartadas: término del rival siempre negativo (premiaba al rival cerca del portador propio); pesos fijos en el código (viola RNF-03).
- Limitación conocida: con estos pesos un recurso soltado bajo una unidad propia (U = 0) vale más que cargarlo a más de 3 pasos de la base (U < 0), y el efecto de horizonte hace que las profundidades pares aplanen valores (caso 10). Se resuelve ajustando los pesos en el JSON si se quiere otro comportamiento.

## 2026-10-17 — Atribución de commits de F4
- Contexto: el usuario pidió que F4 figure a nombre de Jorge.
- Decisión: autor y committer Jorge Iván Garcia Torres, sin trailers `Co-Authored-By`; el uso de IA sigue declarado en docstrings e informe técnico.
- Alternativas descartadas: Daniel como autor (como en F3).

## 2026-10-17 — Campos de `prueba` y línea de comandos (G10)
- Contexto: el enunciado (pregunta 3) no fija qué campos de `prueba` usar para algoritmo, heurística, `k` y orden; hacía falta un punto de entrada para escenarios externos. Propuesta por Claude, aprobada por Daniel.
- Decisión: campos opcionales propios (RNF-02) en `prueba`: `algoritmo`, `heuristica` (`H1` Manhattan, `H2` obstacle aware), `k`, `orden_acciones` (`default` o `reversed`); la profundidad sigue en `juego.profundidad_maxima_minimax`. Nombres canónicos de algoritmo con alias `A*`, `A_ESTRELLA`. CLI `python -m tactical_grid <escenario.json> [--mode --algorithm --heuristic --k --depth --order --unit --goal --verify]`: las opciones de la CLI mandan sobre el JSON; salida JSON con claves del Apéndice B; errores de escenario o de opciones salen por stderr con código 2. Modo `partida` solo describe la partida cargada (la continúa la GUI). Si no se da heurística, A* y Beam usan `H1`.
- Alternativas descartadas: exigir los campos en el JSON (impide probar escenarios del profesor sin editarlos); nombres de campo en inglés (el JSON del enunciado es en español).

## 2026-10-17 — Atribución de commits desde el punto de entrada (F4/F5)
- Contexto: el usuario pidió que los commits desde el punto de entrada en adelante vayan a nombre de Daniel.
- Decisión: autor y committer Daniel Felipe Franco Rincón, sin trailers `Co-Authored-By`; el uso de IA sigue declarado en docstrings e informe técnico.
- Alternativas descartadas: seguir con Jorge como autor.

## 2026-10-17 — Barridos y exportación de resultados (F6)
- Contexto: RF-29, RF-32 y RF-38/39 piden comparar profundidades, órdenes y algoritmos, y dejar los resultados accesibles; el formato CSV/JSON se aprobó el 2026-10-16.
- Decisión: `--algorithm`, `--heuristic`, `--k`, `--depth` y `--order` aceptan listas separadas por comas y se ejecutan las combinaciones que aplican (heurística para A* y Beam, `k` para Beam, profundidad y orden para Minimax y alfa-beta). `--csv` escribe una fila plana por corrida (el camino como `r,c;r,c` y los chequeos como `verificacion_ok`); `--json` escribe los informes completos, con camino, `valores_raiz` y chequeos. Los `valores_raiz` de alfa-beta de las acciones posteriores a la mejor pueden ser cotas, no valores exactos.
- Alternativas descartadas: un archivo de experimentos aparte (más formato que mantener); exportar siempre sin que se pida.

## 2026-10-17 — Pesos de utilidad: se conservan 10/3/1/0.5
- Contexto: la limitación de la utilidad (recurso soltado bajo una unidad propia vale más que llevarlo a más de 3 pasos de la base; profundidades pares aplanan valores) quedó pendiente de decisión. Elegida por Claude a petición de Daniel (delegó la elección).
- Decisión: no cambiar los valores por defecto. Cambiarlos invalidaría los casos 7–10 ya demostrados a 4 días de la entrega; los pesos ya son configurables en la sección `utilidad` del JSON (RNF-03), así que se documenta como limitación en el informe técnico y se ajusta por escenario si hace falta (por ejemplo `recurso_cargado` ≥ 8).
- Alternativas descartadas: subir `recurso_cargado` por defecto (riesgo de regresión sin tiempo de revalidar los casos).

## 2026-10-17 — Rendimiento de Minimax medido y GUI mínima (F5)
- Contexto: prueba pendiente de la meta de 5 s por jugada (decisión 2026-10-16) y GUI de RF-40.
- Medición (mapa 15×15 con pantanos y muro, 3 unidades por bando, profundidad contada en acciones de un bando): alfa-beta d=5 0.04 s, d=6 0.18 s, d=7 0.86 s; Minimax d=4 0.10 s, d=5 1.2 s, d=6 15.7 s (supera la meta). Con 5 unidades por bando: alfa-beta d=5 0.15 s, d=6 0.85 s. En 20×20 con 3 unidades, alfa-beta d=6 0.20 s. Conclusión: dentro de la meta alfa-beta hasta d=7 y Minimax simple hasta d=5.
- Decisión: GUI en `gui/app.py` (tkinter) sobre `gui/session.py` (sin tkinter, probado en `tests/test_gui_session.py`); se abre con `python -m tactical_grid.gui [escenario.json]`. Clic izquierdo selecciona o mueve, clic derecho fija la meta de la búsqueda; ejecuta los 7 algoritmos, dibuja el camino o la acción sugerida, permite jugar turnos (a mano o con IA), deshacer y reiniciar. Los colores de terreno salen del costo leído del JSON, no de nombres. No hay vista de estados explorados (RF-41, opcional).
- Alternativas descartadas: reutilizar `describe` del runner como estado de la GUI (no sirve para jugar); colores por nombre de terreno (viola RNF-03).
- Autoría: los commits de F5 los firma Daniel (continúa la decisión del 2026-10-17).

## 2026-10-17 — Se elimina la acción Wait
- Contexto: el enunciado no define la acción de esperar (la fijamos nosotros el 2026-10-07 / 2026-10-14). Con varias unidades por bando, mover una ya deja a las demás esperando, así que `Wait` sobra.
- Decisión: la única acción es `Move`. Si el bando activo no tiene ningún movimiento legal y la partida no terminó, pasa turno de forma implícita (`rules.skip_turn`, no es una acción): la sesión/GUI salta el turno y Minimax evalúa el nodo como hoja. Ramificación de Minimax: B ≤ 4U.
- Alternativas descartadas: empate si un bando queda bloqueado (cambia la regla de fin de partida); no manejar el caso (Minimax devolvería ±inf). Reemplaza lo dicho sobre `Wait` en las decisiones del 2026-10-07 y 2026-10-14.

## 2026-10-18 — Placaje como acción en lugar de interceptación automática
- Contexto: con la interceptación automática (recurso cae tras cualquier movimiento que deje un rival adyacente al portador) ninguna partida automática con Minimax/alfa-beta terminaba en entrega: todas empataban por límite de turnos, con profundidades 1–6, profundidades distintas por bando y 54 combinaciones de pesos.
- Decisión: se elimina la interceptación automática. Nueva acción `Tackle(unit_id, target)`, legal para una unidad del bando con el turno adyacente al portador rival; el recurso cae en la celda del portador, nadie se mueve, cuesta 0. Estar adyacente solo amenaza; el portador puede huir o entregar antes. Reemplaza la decisión del 2026-10-14 sobre interceptación (que se conserva arriba como histórico).
- Alternativas descartadas: contar solo el movimiento del rival (sigue empatando); zona segura junto a la base propia (decide `caso_07` en 3 turnos pero deja el resto en empate y favorece al primero en mover); transferir el recurso al atacante (exigía desempate).
- Consecuencias: cambian los valores de los casos 7–10 (`caso_07`: ahora A2 → (0,1) vale 14 desde profundidad 3); se regeneran `docs/results/casos_07_10_adversarial.json`, `docs/cases.md` y el informe. Los CSV de rendimiento (`rendimiento_*.csv`) no se regeneraron.

## 2026-10-18 — Utilidad por movimientos restantes con distancias reales
- Contexto: aun con el placaje como acción, en partidas completas de alfa-beta contra sí mismo los mapas de 20×20 empataban: la utilidad del 2026-10-16 cambiaba de objetivo al recoger (estar junto al recurso valía más que llevarlo lejos de la base, así que nadie lo recogía), ignoraba el progreso del rival y usaba Manhattan a través de los muros.
- Decisión: `U = progreso_rival·faltan(MIN) − distancia_objetivo·faltan(MAX) ± recurso_cargado ± distancia_rival·(pasos del perseguidor más cercano al portador)`, con `faltan(bando)` en pasos BFS reales (muros y base rival bloquean, unidades no; +2 si todas las entradas de la base propia están ocupadas; 2 pasos si una unidad está sobre el recurso caído). Triunfo = cota derivada del tablero y los pesos + entrega + turnos restantes; empate = 0. Nuevo peso `utilidad.progreso_rival` (default 0.5). En Minimax/alfa-beta, una raíz sin acciones legales devuelve la utilidad de la raíz (antes −∞). Reemplaza la fórmula del 2026-10-16.
- Alternativas descartadas: utilidad simétrica de suma cero (`progreso_rival = distancia_objetivo`): el portador daba vueltas para alargar el regreso hipotético del rival; distancias que cuentan las unidades como obstáculos (un BFS por hoja, demasiado lento a profundidad 5); ordenar jugadas dentro de alfa-beta (no hace falta para la meta de 5 s y cambia los conteos de los casos 8–9).
- Consecuencias: con profundidad 2–5 hay entrega en `prueba_20x20`, `caso_02`, `caso_03`, `caso_04`, `tamanos/escenario_20x20`, `prueba_15x15`, `caso_07` y `apendice_a`; `escenario_30x30` necesita `limite_turnos` ≥ 110. Alfa-beta en 20×20: 0.5 s a profundidad 6 y 3.3 s a profundidad 7, así que el tope de 15×15 del 2026-10-16 ya no aplica a alfa-beta. Cambian los valores de los casos 7–10 (`caso_07`: 8.5 / 7.5 / 239.5).

## 2026-10-18 — Una sola interfaz, escenarios en una carpeta y caso 7 en 20×20
- Contexto: había dos GUI (`gui/app.py` + `gui/session.py` y la ventana nueva con panel de parámetros por algoritmo), los escenarios estaban repartidos entre `scenarios/` y `scenarios/tamanos/`, y `caso_07` era de 5×7 con 2 unidades por bando (el enunciado pide 20×20 y al menos 3 unidades en los mapas propios). Pedido por el usuario.
- Decisión: la GUI entregada es la nueva (`gui/app.py`; se borran `session.py` y la ventana anterior). Se le añaden indicador de turno/portador, verificación RF-42 y juego manual por clics. Todos los escenarios quedan en `scenarios/`. `caso_07` se rehace en 20×20 con 3 unidades por bando (recurso en (8,11), A1 y A3 pegados a él, rivales desde el sur) y los casos 7–10 se recalculan; las pruebas unitarias que contaban a mano sobre el mapa de 5×7 usan el helper `tests/helpers.py::mini_race`. `escenario_30x30` sube `limite_turnos` a 200 para que la partida se decida (110 turnos).
- Alternativas descartadas: conservar las dos GUI (duplica mantenimiento y sustentación); dejar `caso_07` pequeño (incumple RF-01/RF-05 para un mapa propio).
- Consecuencias: se pierden de la GUI anterior el deshacer, la fijación de meta por clic y el modo automático continuo; «Aplicar jugada» y el juego manual cubren la partida. Los mapas `escenario_03x03` … `escenario_15x15` siguen empatando (el portador es placado al recoger), es un comportamiento de las reglas en mapas diminutos.

## 2026-10-19 — Variante dinámica de reglas (opcional, junto a las reglas base)
- Contexto: en la rama `feat/adversarial-dinamico` se añadió una versión alternativa de las reglas en la que el costo del terreno afecta el ritmo de las unidades y el placaje se vuelve robo, sin tocar el juego entregado (RNF-02: campos opcionales que no alteran los obligatorios).
- Decisión: nueva variante `dinamica`, elegida con `juego.variante` o `--variant`; la base sigue siendo el default. Vive en `domain/dynamic.py` (`DynamicState` envuelve `GameState` y añade contadores); `rules.py` no se modifica. Entrar a una celda de costo `c` deja a la unidad `ceil(c) − 1` turnos propios sin actuar (los contadores del bando bajan 1 al cerrar su turno; una unidad en recuperación no mueve ni placa, pero puede ser placada). El placaje pasa a ser **robo**: la unidad libre adyacente al portador rival pasa a ser el portador (el recurso nunca cae al suelo), la víctima espera `juego.penalizacion_placaje` turnos (máximo con lo que ya tenía, no suma; default 2) y el nuevo portador es inmune `juego.inmunidad_robo` turnos del rival (default 1, evita robos en cadena). Robar sobre la base propia gana. Bando bloqueado: pasa y en la búsqueda es un nodo de un hijo que consume un nivel de profundidad (en la base es una hoja).
- Utilidad propia (`utility_dynamic.py`): misma fórmula y pesos que la base, pero con distancias en turnos propios (suma de `ceil(costo)` de las celdas entradas más los turnos de recuperación pendientes). Minimax y alfa-beta propios (`adversarial_dynamic.py`) con la misma recursión y desempate; chequeo 6 del verificador propio (`verify_adversarial_dynamic`).
- Alternativas descartadas: modificar `rules.py` o `utility.py` (la variante se escribió aparte para no alterar los casos 1–10 ya demostrados; hay una prueba que comprueba que los archivos de los casos base no cambian).
- Consecuencias: `caso_11_dinamico.json` (mapa y unidades del caso 7); resultados en `docs/results/caso_11_dinamico.*`; en las simulaciones la IA casi no roba (0–1 por partida), así que robo e inmunidad están cubiertos por `tests/test_dynamic_rules.py`. Autoría de los commits: Jorge (autor), Daniel (committer), sin `Co-Authored-By` (decisión del usuario).

## 2026-10-19 — Modo partida completo por terminal y GUI (persona contra IA, IA contra IA)
- Contexto: el enunciado define el modo `partida` como «cargar el escenario completo para continuar el juego por turnos»; la CLI solo describía el escenario y el juego completo existía únicamente en la GUI (con la persona siempre en el bando que abre y sin partida automática).
- Decisión: `--mode partida --play auto|humano [--side A|B]` juega la partida entera (`experiments/game.py`). `auto` = IA contra IA con reporte JSON de todas las jugadas; `humano` = la persona elige entre las acciones legales numeradas (`q` abandona) y responde la IA. En cada turno MAX es el bando que mueve y la utilidad se reconstruye desde él, con el mismo algoritmo, profundidad, orden y pesos para los dos bandos. Sin `--play` el modo solo describe, como antes. La validación de algoritmo, profundidad, orden y variante se comparte con el modo adversarial (`_adversarial_settings`). En barridos, `partida` aplica `--depth` y no hereda un algoritmo de búsqueda del escenario. En la GUI: selector «Juegas» (bando que abre por defecto, A o B; si la persona no abre, la IA abre) y botón «Partida automática» con pausa; el comportamiento por defecto no cambia.
- Alternativas descartadas: cambiar `partida` para jugar siempre (rompe el resumen y su prueba); IA distinta por bando (contradice «mismas reglas y mismas capacidades»); reutilizar `gui/app.py` desde la CLI (importa tkinter).
- Consecuencias: 281 tests pasan, `ruff` y `mypy --strict` en verde. Límites: sin deshacer y sin pase automático para la persona bloqueada en la GUI.

## 2026-10-20 — Versión final v1.1.0 y elección de origen y meta por clic en la GUI
- Contexto: `main` quedó detrás de `origin/main` (manuales LaTeX de Jorge); la rama `feat/adversarial-dinamico` ya estaba fusionada.
- Decisión: se alinea `main` con rebase sin conflictos, se añade en la GUI la elección de unidad (clic en una unidad) y meta (clic en celda o clic derecho) en las búsquedas de camino (`trace_search` acepta `unit` y `goal`), y se etiqueta `v1.1.0` como versión final. `v1.0.0` no se mueve.
- Consecuencias: 283 tests, `ruff` y `mypy --strict` en verde.
