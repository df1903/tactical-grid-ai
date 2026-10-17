# Entendimiento de TacticalGrid

> Documento de estudio para entender el proyecto completo antes de la sustentación (2026-10-21).
> Última actualización: 2026-10-17. Se lee en orden: **Parte 1** (qué se pide y por qué), **Parte 2** (cómo está organizado), **Parte 3** (en qué orden leer el código).
> Fuentes: `docs/enunciado.md`, `.context/` (reglas, decisiones, riesgos, estado), estructura real de `src/`, `tests/`, `scenarios/`, `docs/`.

## Índice
- Parte 1 — El proyecto y el enunciado
  - 1.1 Qué es · 1.2 Contexto académico y nota · 1.3 Reglas del juego · 1.4 Estado compuesto · 1.5 Algoritmos exigidos · 1.6 Escenarios JSON · 1.7 Verificación, métricas y GUI · 1.8 Documentación, Git e IA · 1.9 Sustentación · 1.10 Los 10 casos · 1.11 Requisitos, riesgos y decisiones · 1.12 Dónde estamos
- Parte 2 — Estructura (arquitectura, carpetas, flujos)
- Parte 3 — Código: ruta de lectura archivo por archivo

---

# PARTE 1 — El proyecto y el enunciado

## 1.1 Qué es TacticalGrid
Juego táctico 2D **por turnos** sobre una cuadrícula vista desde arriba. Dos bandos (A y B), varias unidades cada uno. Hay **un recurso** en zona neutral: una unidad lo recoge llegando a su celda y debe llevarlo a **su propia base**. Gana quien lo entrega primero.

**El juego no es el fin.** Lema del enunciado: *"El juego es el entorno de experimentación. El proyecto es el sistema inteligente que decide dentro de él."* Sobre el mismo problema, la pregunta va escalando:

| Etapa | Pregunta | Algoritmos |
|---|---|---|
| 1 | ¿Hay una ruta? | BFS, DFS |
| 2 | ¿Cuál es la ruta más **barata** (no la de menos pasos)? | UCS (costo uniforme) |
| 3 | ¿Cómo uso **conocimiento del mapa** para buscar mejor? | A* (≥ 2 heurísticas), Beam Search (memoria limitada, k = 1, 2, 4, 8) |
| 4 | ¿Qué hago si el **rival también razona**? | Minimax, poda alfa-beta |

**Pregunta central:** ¿cómo cambia la forma de decidir de un sistema inteligente al pasar de encontrar una ruta, a optimizar su costo, a usar heurísticas, y por último a actuar frente a un adversario?

**Criterio de éxito (clave):** no basta con que funcione. Hay que poder explicar **por qué** cada algoritmo se comporta así, **qué supuestos** sostienen las decisiones y **cómo reacciona ante un escenario nunca visto**.

Equipo: Jorge Iván Garcia Torres y Daniel Felipe Franco Rincón. Materia: Sistemas Inteligentes I, UCALDAS. Proyecto 1 (integra Unidades 2 y 3 del curso).

## 1.2 Contexto académico y cómo se califica
- Proyecto 1 = **20 %** de la nota del curso (Parciales 3×15 %, Proyecto 2 25 %, talleres 10 %).
- Del proyecto: **50 % grupal** (funcionalidad y calidad) + **50 % sustentación individual**. Si el producto funciona pero un integrante no domina el código, la nota individual puede bajar.

| Componente grupal | % | Qué lo cubre |
|---|---|---|
| Modelado del problema y representación de estados | 15 | `domain/`, caso 6, RF-10 a RF-13 |
| BFS, DFS, UCS | 15 | `algorithms/uninformed.py`, casos 1–2 |
| A*, heurísticas, Beam | 20 | `heuristics.py`, `informed.py`, casos 3–5 |
| Minimax y alfa-beta | 20 | `utility.py`, `adversarial.py`, casos 7–10 |
| Experimentación, métricas, interpretación | 10 | `experiments/`, `docs/results/`, informe |
| Calidad y documentación técnica del código | 10 | docstrings de 7 campos, tests, ruff/mypy |
| Interfaz y visualización | 5 | `gui/` |
| Validación de escenarios y soluciones | 5 | `scenario/loader.py`, `experiments/verifier.py` |

Se espera comprender, justificar y analizar, no solo implementar. Uso de IA permitido **si se declara** (ver 1.8).

## 1.3 Reglas del juego
**Impuestas por el enunciado (RF-01 a RF-09):**
- Mapa mínimo 20×20 en desarrollo, pero debe aceptar otras dimensiones por JSON.
- Terrenos mínimos: camino (barato), regular (medio), difícil (caro), obstáculo (no transitable), bases A/B, recurso.
- **Costos salen del escenario**, no del código (RF-03). Debe existir un mapa donde la ruta con menos movimientos cueste más (RF-04).
- ≥ 3 unidades por bando. Por turnos: un bando elige **una unidad** y hace **una acción válida**.
- **MAX y MIN tienen las mismas reglas**: son roles del árbol Minimax, no jugadores distintos (RF-07). MIN no está en desventaja: minimizar la utilidad de MAX es favorecer sus propios intereses (RF-28).
- El equipo define reglas **deterministas** para bloqueos, falta de ruta y pérdida del portador (RF-09).

**Decididas por el equipo** (el enunciado las deja abiertas; ver `.context/rules.md`):

| Tema | Regla adoptada |
|---|---|
| Movimiento | 4 direcciones (arriba, abajo, izquierda, derecha). Por eso Manhattan es admisible |
| Costo | Se paga al **entrar** a la celda destino. La celda inicial no cuesta |
| Ocupación | Una unidad por celda. Se pueden pisar la base propia y la celda del recurso si están libres; la **base rival no** |
| Acciones | `Move` (cuesta el terreno destino) y `Wait` (cuesta 0, siempre legal). Un solo tipo de unidad (`estandar`) |
| Recoger | Solo **al llegar** a la celda del recurso (esperar no recoge) |
| Entregar | Llegar a la base propia con el recurso: victoria inmediata |
| Perder el recurso (interceptación) | Tras **cualquier** movimiento que deje a una unidad rival **adyacente al portador**, el recurso **cae en la celda del portador**. No se transfiere al rival. El portador original no lo recoge mientras siga en esa celda; otra unidad lo recoge al llegar |
| Orden dentro de un movimiento | recoger → entrega (gana y evita la interceptación) → interceptación |
| Fin | Victoria por entrega; **empate** al llegar al límite de turnos (`juego.limite_turnos`, default 100). Terminada la partida no hay acciones legales |
| Bando sin movimientos | Pasa turno |

Regla de oro del repo: **ningún costo, nombre de terreno, dimensión ni posición va escrito en `domain/` ni `algorithms/`**.

## 1.4 El estado compuesto (parte central: 15 %)
RF-10: un estado `(fila, columna)` **no alcanza** con varias unidades, turnos y posesión del recurso. RF-11: dos estados con una unidad en la misma casilla pueden ser **distintos** (p. ej. en uno carga el recurso y en otro no). Eso es el **caso 6**.

`GameState` (en `domain/model.py`) contiene:
- `positions`: posición de cada unidad (tupla ordenada por id, hashable).
- `carrier`: unidad que lleva el recurso, o `None`.
- `resource`: celda del recurso cuando nadie lo lleva.
- `turn`: bando que mueve. `turn_number`: contador (para el límite de turnos).

`Board` es la parte **estática** (filas, columnas, matriz de terrenos, catálogo de terrenos, bases, bando de cada unidad, límite de turnos). Separar estático/dinámico evita copiar el mapa en cada estado.

RF-12: debe poder identificarse inequívocamente estado inicial, acciones válidas, sucesores, meta y costo → `legal_actions`, `apply`, `successors`, `winner`. RF-13: hay que **explicar por qué la representación basta** para decidir bien (porque cualquier cosa que cambie las acciones legales o el resultado está en el estado: posiciones, portador/recurso, turno).

## 1.5 Algoritmos exigidos
**No informada (RF-14 a RF-16).** Se ignora al adversario: una unidad va de un punto a un objetivo. BFS y DFS. 6 métricas por corrida: éxito, longitud (movimientos), generados, expandidos, máximo de frontera, tiempo.

**Costos (RF-17 a RF-19).** UCS minimiza el costo acumulado g(n), no los pasos. Convención del curso: menor g primero; **empate → el que entró antes a la frontera**; si aparece un camino más barato a un nodo conocido, **se actualiza**. Debe existir un escenario donde BFS y UCS dan caminos distintos (caso 2).

**Informada (RF-20 a RF-22).** A* con f = g + h. Mínimo 2 heurísticas (una puede ser Manhattan; la otra la propone el equipo). Para **cada** heurística hay que explicar: (1) qué estima, (2) qué información del estado usa, (3) su costo computacional, (4) si es admisible y por qué, (5) dónde orienta bien y dónde pierde poder de discriminación.

**Beam Search (RF-23, RF-24).** Memoria limitada: conserva solo k candidatos. k = 1, 2, 4, 8 como mínimo. Hay que mostrar si recortar puede descartar un camino que luego era el bueno.

**Adversarial (RF-25 a RF-33).** Minimax y alfa-beta con **profundidad limitada y configurable sin tocar código**. Función de utilidad propia, medida desde un bando (MAX maximiza, MIN minimiza). 7 métricas: nodos generados, evaluados, podados, profundidad alcanzada, tiempo, acción seleccionada, valor. Con misma profundidad, utilidad y orden de acciones, **Minimax y alfa-beta deben dar la misma decisión** (RF-31). Hay que experimentar con distintas profundidades (RF-29) y distinto orden de acciones (RF-32) y poder explicar por qué una acción vale más que otra (RF-33).

### Conceptos que hay que dominar (checklist)
- Espacio de estados: estado inicial, operadores, prueba de meta, costo.
- Generado (entró a la búsqueda) vs. expandido (se analizaron sus sucesores). Frontera = generados no expandidos.
- g(n), h(n), f(n). **Admisible** = nunca sobreestima el costo restante real. **Consistente** = h(n) ≤ costo(n,n') + h(n').
- Complejidad con variables: b (ramificación), d (profundidad de la solución), m (profundidad máxima).
- Minimax: árbol de juego, MAX/MIN, horizonte (profundidad limitada) y función de evaluación. Alfa-beta: poda ramas que no pueden cambiar la decisión; **su eficacia depende del orden de los sucesores**.

## 1.6 Escenarios JSON (el contrato con el profesor)
**Clave:** el profesor entrega en la sustentación al menos un escenario **no visto**. Debe cargarse y funcionar **sin modificar código** (RNF-03, RNF-04). Por eso nada codificado.

Campos obligatorios: `version`, `mapa.filas/columnas`, `tipos_terreno`, `terreno`, `bases.A/B`, `recurso`, `unidades`, `turno`, `juego.portador_recurso`, `prueba` (opcional). Se respetan los nombres (RNF-01); se permiten campos propios que no cambien el significado (RNF-02).

`prueba.modo`: `busqueda` (navegación con BFS/DFS/UCS/A*/Beam), `partida` (cargar y seguir jugando), `adversarial` (Minimax/alfa-beta sobre un estado).

**Carga atómica (RF-34):** todo o nada; un JSON inválido se rechaza sin dejar nada a medias y se explica cada error. **Las 9 validaciones (RF-35):** (1) filas/columnas positivas y consistentes con la matriz, (2) terrenos usados existen, (3) transitables con costo > 0, (4) bases/recurso/unidades dentro del mapa, (5) ninguna unidad sobre celda no transitable, (6) ids únicos, (7) bando a/b, (8) turno a/b, (9) `portador_recurso` null o unidad existente. El equipo añadió una más: dos unidades no comparten celda.

Ambigüedades del enunciado resueltas: bandos `a`/`A` se aceptan ambos y se normalizan a mayúscula; costos pueden ser decimales; `muro` no trae `costo`.

Campos propios añadidos por el equipo (decisión 2026-10-17): en `prueba`: `algoritmo`, `heuristica` (`H1`/`H2`), `k`, `orden_acciones` (`default`/`reversed`); en `juego`: `limite_turnos`; sección `utilidad` con los pesos.

## 1.7 Verificación, métricas y GUI
- **Verificación (RF-42), 6 chequeos:** (1) cada movimiento del camino es válido, (2) nadie atraviesa obstáculos, (3) el costo reportado coincide con las transiciones, (4) el estado final cumple la meta, (5) no hay estados inválidos, (6) las acciones consideradas por Minimax son legales. Los 5 primeros son de búsqueda (`verify_search`); el 6 es adversarial (`verify_adversarial`).
- **Métricas (RF-38/39):** deben mostrarse y ser accesibles (formato Apéndice B: `algoritmo, exito, camino, costo, estados_generados, estados_expandidos, maximo_frontera`). Exportar es opcional; aquí se hace con CSV/JSON.
- **GUI (RF-40) mínima:** cuadrícula, terrenos, obstáculos, bases, recurso, unidades, bando de cada unidad, portador, turno actual y camino encontrado. RF-41 (ver estados explorados/frontera) se valora pero no es obligatoria. La estética no importa. Peso 5 %.

## 1.8 Documentación, Git e IA
- **Docstring de 7 campos** en métodos con lógica relevante (algoritmos, heurísticas, sucesores, costos, utilidad, Minimax, alfa-beta, validadores): *Purpose, Preconditions, Postconditions, Complexity, AI usage (Yes/No), AI intervention, Student validation*. Debe corresponder a la **implementación real** (RD-01); si no, es "documentación inconsistente".
- **Git:** repositorio con aportes visibles por integrante y `README.md` con nombres (RE-01). Repo y documentos = **misma versión** presentada (RE-02) → hay que poner un **tag**.
- **Reproducibilidad (RE-03/04):** estado inicial declarado, esperado vs. obtenido por caso, evidencia para repetir los experimentos.
- **IA:** permitida y no baja la nota por sí sola, pero **debe declararse** (herramienta y propósito) en docstrings e informe técnico. **Omitirla deliberadamente = inconsistencia.** Cada integrante responde por **todo** el código: lo que funciona pero no se puede explicar, justificar o adaptar no demuestra dominio.
- **Entregables:** repo, código + instrucciones de instalación/ejecución, escenarios y casos mínimos, manual de usuario, documento técnico (modelado, estados, reglas, costos, heurísticas, utilidad, metodología, resultados, complejidad, limitaciones, reporte de IA), evidencia reproducible.

## 1.9 La sustentación (50 % de la nota, individual)
Cada integrante debe poder explicar **cualquier parte relevante**, aunque no sea el autor. Pueden pedirle:
- Explicar la representación del estado y por qué basta.
- Ejecutar BFS/DFS/UCS/A*/Beam sobre un **escenario externo**.
- Justificar una heurística y su admisibilidad.
- Explicar una decisión de Minimax, la utilidad y **por qué MIN no está en desventaja**.
- Analizar el efecto de cambiar profundidad u orden de acciones.
- Explicar complejidad, el uso de IA declarado y la validación hecha.
- **Una modificación pequeña** de un método elegido al azar.
- **Predecir antes de ejecutar** (p. ej. el profesor cambia el pantano de costo 7 a 15: ¿qué pasa con UCS y A*?).

Entrenamiento recomendado: cambiar costos/profundidad/orden en un JSON, **predecir el resultado por escrito**, ejecutar y comparar.

## 1.10 Los 10 casos mínimos
Archivos y comandos exactos en `docs/cases.md`; resultados guardados en `docs/results/`; verificados por `tests/test_cases_f*.py` y `tests/test_case_6.py`.

| # | Qué demuestra | Escenario | Idea del resultado |
|---|---|---|---|
| 1 | BFS vs DFS: ambos llegan, recorren distinto | `caso_01_bfs_vs_dfs.json` | BFS 4 movimientos (39 generados); DFS 42 movimientos (152 generados) |
| 2 | Ruta corta vs. barata | `caso_02_bfs_vs_ucs.json` | BFS cruza el pantano: 7 movimientos, costo 25. UCS rodea: 17 movimientos, costo 17 |
| 3 | Obstáculo y heurística | `caso_03_obstaculo_heuristica.json` | Meta a 7 celdas pero hay que rodear un muro; Manhattan engaña, `H2` no |
| 4 | Comparar las 2 heurísticas | `caso_04_comparacion_heuristicas.json` | A* con H1 vs H2 sobre el mismo mapa |
| 5 | Beam: k cambia la exploración | `caso_05_beam_k.json` | k = 1, 2, 4, 8 (mapa 7×9) |
| 6 | Misma posición, estados distintos | `caso_07_decision_adversarial.json` + `test_case_6.py` | Portador/turno diferencian estados con igual casilla |
| 7 | Minimax ≠ avanzar directo | `caso_07_decision_adversarial.json` | Depth 1, 2, 3 |
| 8 | Minimax = alfa-beta, y alfa-beta evalúa menos | ídem | Depth 4 |
| 9 | Orden de acciones cambia la poda | ídem | `default` vs `reversed` |
| 10 | Profundidad cambia la decisión/valor | ídem | Depth 1–5 |

Casos 6–10 comparten un mapa 5×7, costo 1, dos unidades por bando.

## 1.11 Requisitos, riesgos y decisiones

### Requisitos (resumen de `.context/project/requirements.md`)
- **Funcionales:** cargar JSON atómico; estado compuesto con sucesores/meta/costo; BFS, DFS, UCS (6 métricas); A* ≥ 2 heurísticas y Beam k=1,2,4,8; Minimax y alfa-beta (7 métricas); modos `busqueda`/`partida`/`adversarial`; verificación (6 chequeos); GUI mínima; 10 casos esperado vs. obtenido; entregables.
- **No funcionales:** separación en 5 componentes (RNF-05); cero constantes de mapa (RNF-03/04); reproducibilidad; docstrings consistentes (RD-01); `pytest`, `ruff` y `mypy --strict` en verde; aportes visibles en Git; versión etiquetada.
- **Fuera de alcance:** nada más allá del enunciado; combate complejo; Greedy; aprendizaje por refuerzo; multiagente; GUI avanzada.

### Restricciones no negociables (`.context/constraints.md`)
Costos/posiciones/dimensiones/nombres de terreno siempre desde el JSON; carga atómica; MAX y MIN con iguales reglas; profundidad configurable; código y docs en inglés; Python 3.14 + `uv`, solo Windows; uso de IA declarado; cada integrante explica todo; fecha límite 2026-10-21; meta de 5 s por decisión de Minimax y mapa ≤ 15×15 para Minimax.

### Riesgos (`.context/project/risks.md`) y cómo se cubren

| Riesgo | Prob. | Impacto | Mitigación | Estado |
|---|---|---|---|---|
| Minimax explota con mapa/profundidad grande | alta | alta | Profundidad configurable, alfa-beta, orden de sucesores, meta 5 s | Medido: alfa-beta hasta d=7, Minimax simple hasta d=5 en 15×15 |
| Heurística no admisible con costos externos | media | alta | Escalar Manhattan por el costo transitable **mínimo** del JSON | Hecho (`min_step_cost`) |
| Mapa externo rompe supuestos | media | alta | Cero constantes, mapas variados (15×15, 20×20) | Hecho; verificar con JSON propio |
| **Un integrante no defiende código ajeno** | media | alta | Revisión cruzada, ensayo | **Pendiente: es el riesgo más real hoy** |
| Documentación ≠ código (RD-01) | media | media | Revisar docstrings antes del tag | **Pendiente** ("Student validation") |
| GUI consume tiempo | media | media | GUI mínima primero | Hecha |

Riesgo extra de contenido: la utilidad tiene una limitación conocida (ver abajo) que hay que poder explicar, no esconder.

### Decisiones clave (resumen de `.context/project/decisions.md`; el detalle completo está allí)
1. **Stack:** Python 3.14, `uv`, pytest, ruff, mypy `--strict`, sin dependencias runtime. GUI con **tkinter** (viene con Python).
2. **Reglas:** ver tabla en 1.3.
3. **Búsqueda de un solo agente (F2):** el problema quita las unidades rivales (la base rival sigue sin poder pisarse), mueve solo la unidad de inicio, ignora recurso y turno, no usa `Wait`. Razón: en el Apéndice A, B1 está sobre la celda objetivo; tratarlo como obstáculo dejaba el ejemplo sin solución.
4. **Convenciones BFS/DFS/UCS:** búsqueda en grafo (con explorados), meta probada **al expandir**, orden de sucesores arriba-abajo-izquierda-derecha, el estado inicial cuenta como generado, desempate por orden de entrada a la frontera. DFS empuja hijos en orden inverso para expandir primero el primero.
5. **Heurísticas:** `H1` = Manhattan × costo transitable mínimo. `H2` = distancia en movimientos que **rodea muros y la base rival** (BFS inverso desde la meta) × costo mínimo. H2 ≥ H1; ambas admisibles y consistentes.
6. **A*:** f = g + h, desempate por orden de entrada, **reapertura** si aparece camino más barato. **Beam:** por niveles, conserva los k de menor f = g + h; es **incompleto** (puede fallar); `max_frontier` cuenta candidatos antes de podar.
7. **Utilidad (desde MAX = el bando que mueve en la raíz):** `U = 10·entrega + 3·(recurso cargado) − distancia_al_objetivo + 0.5·distancia_rival_al_portador` (el último término solo cuando MAX carga). Pesos en la sección `utilidad` del JSON; 10/3/1/0.5 solo son defaults. Una unidad de profundidad = **una acción de un bando**. En la raíz gana la primera acción con valor **estrictamente** mayor → Minimax y alfa-beta coinciden en empates.
8. **Limitación conocida:** un recurso soltado bajo una unidad propia (U = 0) puede valer más que cargarlo a > 3 pasos de la base; y profundidades pares aplanan valores (efecto horizonte, caso 10). Decidido **no cambiar los pesos** (invalidaría los casos 7–10 a 4 días de la entrega); se documenta y se ajusta por JSON.
9. **CLI y exportación:** `python -m tactical_grid <json> --algorithm A,B --heuristic .. --k .. --depth .. --order .. --verify --csv .. --json ..`; las listas con coma hacen **barridos**; CSV para métricas, JSON para trazas; errores a stderr con código 2.
10. **GUI:** `gui/session.py` (lógica sin tkinter, testeable) + `gui/app.py` (tkinter). Colores del terreno salen del costo, no del nombre.
11. **Autoría de commits:** F1–F2 y F4 de Jorge; F3 y desde la CLI de Daniel; sin trailers `Co-Authored-By`; IA declarada en docstrings e informe.

## 1.12 Dónde estamos (2026-10-17, quedan 4 días)
- **Completado:** F0 a F5 y casi todo F6. Algoritmos (BFS, DFS, UCS, A*, Beam, Minimax, alfa-beta), CLI, barridos y exportación, GUI tkinter, medición de rendimiento, informe técnico, manual y tabla de casos. 172 tests pasan (1 skip), `ruff` y `mypy --strict` en verde.
- **Pendiente:**
  - Probar la GUI a mano con los escenarios del equipo.
  - **Revisión cruzada** de Jorge sobre `domain/`, `scenario/`, `algorithms/`.
  - **Cerrar "Student validation"** en docstrings (`legal_actions`, `apply`, `successors`, `load_scenario`, `bfs`, `dfs`, `ucs`, `verify_search`, `manhattan`, `obstacle_aware`, `a_star`, `beam_search`, `utility`, `minimax`, `alpha_beta`, `verify_adversarial`, `run`, `expand`).
  - Releer `docs/` (informe, manual, casos); confirmar RF-13 y justificación RF-22.
  - **Tag de Git** y ensayo de sustentación.

---

# PARTE 2 — Estructura

## 2.1 Arquitectura: 5 componentes, dependencias en una sola dirección
Todo en un proceso Python: sin red, sin servicios, sin base de datos, **cero dependencias externas en runtime**.

```
scenario ──► domain ◄── algorithms ◄── experiments
                ▲            ▲              ▲
                └────────────┴──── gui ─────┘   (gui orquesta; nadie depende de gui)
```
- `domain` no importa a nadie. `algorithms` no lee JSON ni conoce la GUI. `scenario` no ejecuta búsquedas.
- Por qué: RNF-05 pide separar lógica/escenario/algoritmos/interfaz; RF-07 pide que MAX y MIN usen las mismas reglas (un único motor `domain` que usan todos); cambiar de mapa sin tocar código (solo `scenario` conoce el JSON); comparar algoritmos con justicia (todos usan la misma interfaz de sucesores/costos/meta).

| Paquete | Responsabilidad | NO hace |
|---|---|---|
| `domain/` | Qué es un estado, qué acciones hay, qué cuestan, cuándo se gana | Leer JSON, buscar, dibujar |
| `scenario/` | JSON → objetos de `domain`, todo o nada | Reglas, algoritmos |
| `algorithms/` | BFS, DFS, UCS, A*, Beam, utilidad, Minimax, alfa-beta | Leer JSON, GUI, definir costos |
| `experiments/` | Orquestar corridas, verificar, barridos, exportar | Implementar algoritmos |
| `gui/` | Mostrar y controlar | Lógica de juego |

## 2.2 Estructura de carpetas

```
tactical-grid-ai/
├─ src/tactical_grid/        el producto
│  ├─ __main__.py            CLI (python -m tactical_grid)
│  ├─ domain/                model.py, rules.py
│  ├─ scenario/              loader.py
│  ├─ algorithms/            common.py, uninformed.py, heuristics.py, informed.py,
│  │                         utility.py, adversarial.py
│  ├─ experiments/           verifier.py, runner.py, sweep.py
│  └─ gui/                   session.py, app.py, __main__.py
├─ tests/                    pytest (172 tests)
├─ scenarios/                JSON de datos (apendice_a, casos 1-5 y 7, prueba_15x15, prueba_20x20)
├─ docs/                     enunciado.md, technical-report.md, user-manual.md, cases.md, results/
├─ .context/                 memoria del proyecto para agentes IA (no es código)
├─ .claude/                  configuración de Claude Code (hooks, skills, agents)
└─ pyproject.toml, uv.lock, .python-version, README.md, AGENTS.md, CLAUDE.md, ENTENDIMIENTO.md
```
Layout `src/`: el paquete se instala con `uv sync` y los tests importan exactamente lo que usa el usuario.

### Tamaño de cada archivo de código (para planificar la lectura)
| Archivo | Líneas | Contiene |
|---|---|---|
| `domain/model.py` | 109 | `Side`, `Position`, `Terrain`, `Board`, `GameState`, `Move`, `Wait` |
| `domain/rules.py` | 119 | `winner`, `is_draw`, `is_terminal`, `legal_actions`, `apply`, `successors` |
| `scenario/loader.py` | 358 | `load_scenario`, `build_scenario`, 9+ lectores `_read_*`, `Scenario`, `TestConfig`, `ScenarioError` |
| `algorithms/common.py` | 131 | `SearchResult`, `PathProblem`, `make_problem`, `reconstruct`, `found`, `failed` |
| `algorithms/uninformed.py` | 151 | `bfs`, `dfs`, `ucs` |
| `algorithms/heuristics.py` | 79 | `min_step_cost`, `manhattan`, `obstacle_aware` |
| `algorithms/informed.py` | 134 | `a_star`, `beam_search` |
| `algorithms/utility.py` | 80 | `UtilityWeights`, `make_utility` |
| `algorithms/adversarial.py` | 157 | `AdversarialResult`, `minimax`, `alpha_beta`, `_decide` |
| `experiments/verifier.py` | 150 | `Check`, `VerificationReport`, `verify_search`, `verify_adversarial` |
| `experiments/runner.py` | 215 | `RunOptions`, `canonical`, `run`, `describe`, `_run_search`, `_run_adversarial` |
| `experiments/sweep.py` | 99 | `Sweep`, `expand`, `run_sweep`, `flatten`, `write_csv`, `write_json` |
| `__main__.py` | 98 | Parser de la CLI y `main` |
| `gui/session.py` | 125 | `Session` (estado de la partida, deshacer, buscar, decidir) |
| `gui/app.py` | 701 | Ventana tkinter (dibujo, clics, paneles) |

### Tests (qué prueba cada uno)
`helpers.py` (utilidades: cargar escenarios, mapas ASCII) · `test_domain_state/rules` (modelo y reglas) · `test_scenario_validation` (cada validación, atomicidad) · `test_search_common`, `test_bfs`, `test_dfs`, `test_ucs`, `test_astar`, `test_beam`, `test_heuristics` · `test_utility`, `test_adversarial` · `test_verifier` · `test_runner`, `test_sweep` · `test_gui_session`, `test_gui_app` · `test_cases_f2/f3/f4`, `test_case_6` (los 10 casos) · `test_smoke`.

### `.context/` y `.claude/` (no se ejecutan)
`.context/`: `architecture.md`, `rules.md`, `constraints.md`, `conventions.md`, `stack.md`, `project/{requirements,roadmap,decisions,risks}.md`, `state/{current,known-issues}.md`, `handoffs/001..011.md` (historia de cada sesión). `.claude/`: permisos, hook que bloquea `.env`/claves, agente `code-reviewer`, skills `close-session` y `new-feature-spec`.

## 2.3 Flujos de ejecución
**Modo búsqueda (CLI):**
```
load_scenario(path) ─► Scenario (board, initial_state, test_config, pesos)
   make_problem(board, initial, unit_id, goal) ─► PathProblem  (adapta el juego a "una unidad busca camino")
      bfs / dfs / ucs / a_star / beam_search (problem [, heuristic]) ─► SearchResult
         verify_search(problem, result) ─► VerificationReport (chequeos 1-5)
```
**Modo adversarial:**
```
Scenario ─► make_utility(board, max_side, weights) ─► Utility
   minimax / alpha_beta(board, state, depth, utility, order) ─► AdversarialResult
      verify_adversarial(...) ─► chequeo 6
```
Todo lo orquesta `experiments/runner.py::run`; `sweep.py` repite `run` por cada combinación y exporta; la GUI usa `Session` que llama a esas mismas funciones.

**Idea clave del repo:** `domain.successors` es el **único** lugar donde se definen movimientos y costos. Los buscadores (vía `PathProblem.expand`) y Minimax (vía `legal_actions`/`apply`) lo consumen; por eso las reglas son idénticas para todos.

## 2.4 Convenciones
- Código, docstrings y README en **inglés**; las claves del JSON (español) solo se leen en `scenario/`.
- Estados inmutables (`frozen=True`), type hints obligatorios (`mypy --strict`), `ruff` con línea 100.
- Docstring de 7 campos en métodos con lógica relevante.
- Commits convencionales; sin trailers `Co-Authored-By`.

---

# PARTE 3 — Código: ruta de lectura

**Cómo usar esta ruta.** Va de lo que no depende de nada (modelo) hacia lo que usa todo (GUI). Para cada archivo: léelo línea por línea, responde las **preguntas de control** (si no puedes responder una sin mirar, relee), y luego abre su test para ver el comportamiento con ejemplos. No pases al siguiente hasta contestar las preguntas. Tiempo estimado: ~1 h por bloque grande.

Regla práctica de lectura: primero firmas y docstrings, luego el cuerpo; en cada función anota qué recibe, qué devuelve y de quién depende.

### Paso 1 — `domain/model.py` (109 líneas): el vocabulario
Lee primero: es lo que todos los demás archivos importan.
- `Side` (A/B y `.opponent`), `Position` (`neighbors` en orden arriba-abajo-izq-der, `is_adjacent`), `Terrain` (costo `None` si no transitable), `Board` (estático), `GameState` (dinámico), `Move`/`Wait`, `Action = Move | Wait`.
- Preguntas: ¿por qué `Board` y `GameState` están separados? ¿por qué `positions` es una tupla ordenada por id y no un dict? (hashable + igualdad). ¿qué distingue dos `GameState` con igual posición de una unidad (caso 6)? ¿por qué `frozen=True`?
- Test: `tests/test_domain_state.py`.

### Paso 2 — `domain/rules.py` (119 líneas): el motor del juego
Importa solo de `model`. Lee en este orden: `winner` → `is_draw` → `is_terminal` → `legal_actions` → **`apply`** (el más importante) → `_rival_adjacent` → `successors`.
- Sigue en `apply` el orden: mover → recoger → entrega → interceptación; y qué cuesta cada cosa.
- Preguntas: ¿cuándo `Wait` es legal? ¿por qué no se puede pisar la base rival? ¿dónde cae el recurso al interceptar y quién puede recogerlo? ¿por qué la entrega gana sobre la interceptación? ¿qué devuelve `successors` (acción, nuevo estado, costo)?
- Test: `tests/test_domain_rules.py` (174 líneas, es una lista de ejemplos de las reglas). **Este es el archivo que más hay que dominar** (15 % de la nota: modelado).

### Paso 3 — `scenario/loader.py` (358 líneas): del JSON al objeto
Importa de `domain.model`. Lee en este orden:
1. Clases `ScenarioError`, `TestConfig`, `Scenario` (qué se devuelve).
2. `load_scenario` (lee texto y parsea) → **`build_scenario`** (llama a todos los lectores, acumula errores en **una lista**, solo si está vacía construye).
3. Los lectores en el orden en que `build_scenario` los llama: `_read_dimensions`, `_read_terrains`, `_read_grid`, `_read_side`, `_read_position`, `_read_bases`, `_read_units`, `_read_carrier`, `_read_turn_limit`, `_read_utility_weights`, `_read_test_config`. Los auxiliares `_is_int`, `_is_number`, `_text` al final.
- Preguntas: ¿cómo se garantiza la atomicidad? ¿qué validación (1–9) hace cada lector? ¿dónde se traduce `mapa/filas` → `rows`? ¿por qué se reportan todos los errores y no el primero? ¿dónde se normaliza `a` → `A`? ¿cuál es el default de `limite_turnos`?
- Test: `tests/test_scenario_validation.py`.
- Abre `scenarios/apendice_a.json` al lado y recorre cómo cada campo termina en `Board`/`GameState`.

### Paso 4 — `algorithms/common.py` (131 líneas): el contrato de los buscadores
Importa de `domain`. Lee: `SearchResult` (las 6 métricas) → `PathProblem` (`is_goal`, `expand`) → **`make_problem`** (adapta el juego a búsqueda de un solo agente: quita rivales, mueve solo una unidad) → `_normalize` → `reconstruct` → `found` / `failed`.
- Preguntas: ¿por qué el estado de búsqueda equivale a la posición de la unidad? ¿por qué se quitan los rivales (ver decisión del Apéndice A)? ¿cómo `expand` reutiliza `domain.successors`? ¿cómo se reconstruye el camino?
- Test: `tests/test_search_common.py`.

### Paso 5 — `algorithms/uninformed.py` (151 líneas): BFS, DFS, UCS
Lee **BFS primero** (el más simple), luego **UCS** (añade la cola de prioridad y costos), y por último **DFS** (cambia la pila).
- Compara los tres lado a lado: qué estructura usa la frontera (cola FIFO / pila / heap), cuándo se prueba la meta (al expandir), cuándo cuenta un estado como "generado", qué es el desempate por orden de entrada.
- Preguntas: ¿por qué DFS empuja los hijos en orden inverso? ¿cuándo UCS "actualiza" un nodo y por qué eso no cuenta como generado? ¿qué mide `max_frontier`? ¿por qué BFS no es óptimo en costo (caso 2)? ¿complejidad en b, d, m de cada uno?
- Tests: `test_bfs.py`, `test_dfs.py`, `test_ucs.py`, y luego `test_cases_f2.py` + `docs/cases.md` casos 1–2.

### Paso 6 — `experiments/verifier.py`, parte de búsqueda (primeras ~100 líneas)
Lee `Check`, `VerificationReport`, **`verify_search`** y `_valid_state`. Aún no leas `verify_adversarial`.
- Preguntas: ¿cómo comprueba cada uno de los 5 chequeos *sin reutilizar* el buscador? (independencia: recalcula costo y valida cada transición contra las reglas). ¿Qué hace si el resultado dice "sin solución"?
- Test: `tests/test_verifier.py`.

### Paso 7 — `algorithms/heuristics.py` (79 líneas)
Lee `min_step_cost` → `manhattan` (H1) → `obstacle_aware` (H2).
- Preguntas: ¿por qué se multiplica por el costo mínimo? (admisibilidad con costos del JSON). ¿cómo calcula H2 el BFS inverso desde la meta y por qué H2 ≥ H1? ¿qué complejidad tiene precalcular H2 vs. evaluar H1? ¿en qué mapa H1 "engaña" (caso 3) y en cuál H1 y H2 empatan? Prepara las 5 respuestas de RF-22 para cada una.
- Test: `tests/test_heuristics.py`.

### Paso 8 — `algorithms/informed.py` (134 líneas): A* y Beam
Lee `a_star` (es UCS con `f = g + h`; compáralo con `ucs`), luego `beam_search`.
- Preguntas: ¿qué cambia respecto a UCS? ¿qué es reabrir un nodo y cuándo ocurre? ¿por qué A* con H admisible y consistente es óptimo? ¿cómo poda Beam por niveles y por qué es incompleto? ¿qué pasa con k=1 vs k=8? ¿por qué `max_frontier` cuenta antes de podar?
- Tests: `test_astar.py`, `test_beam.py`, `test_cases_f3.py` + casos 3–5 en `docs/cases.md`.

### Paso 9 — `algorithms/utility.py` (80 líneas)
Lee `UtilityWeights` (defaults 10/3/1/0.5, `from_mapping`) → `_distance` → **`make_utility`** (devuelve una función de estado a número desde la perspectiva de MAX).
- Preguntas: ¿qué cuatro términos tiene y qué signo? ¿por qué la distancia objetivo cambia según quién carga el recurso? ¿qué valor tiene un estado terminal? Explica la **limitación conocida** (recurso soltado vale más que cargarlo lejos) y cómo se ajusta por JSON.
- Test: `tests/test_utility.py`.

### Paso 10 — `algorithms/adversarial.py` (157 líneas): Minimax y alfa-beta
Lee `AdversarialResult` (7 métricas) → `minimax` y `alpha_beta` (ambos son envoltorios) → **`_decide`** (el núcleo: `ordered`, `value_of` recursivo).
- Preguntas: ¿cómo decide `value_of` si maximizar o minimizar (por el bando que mueve)? ¿qué es una unidad de profundidad? ¿cuándo se evalúa la utilidad (hoja o terminal)? ¿dónde corta alfa-beta y qué cuenta como `pruned`? ¿por qué ambos eligen la misma acción en empates (primera con valor estrictamente mayor)? ¿cómo cambia la poda con `reversed`?
- Tests: `test_adversarial.py`, `test_cases_f4.py`, `test_case_6.py` + casos 6–10.

### Paso 11 — `experiments/verifier.py`, parte adversarial (`verify_adversarial`)
- Preguntas: ¿cómo prueba la legalidad de cada acción considerada? (re-ejecuta con `record=True`). Es el chequeo 6.

### Paso 12 — `experiments/runner.py` (215 líneas): el director de orquesta
Lee `RunError`, `RunOptions` → `canonical` (alias de nombres) → **`run`** → `describe` → `_run_search` → `_run_adversarial` → `_search_report` / `_adversarial_report` / `_checks` / `_cell`.
- Preguntas: ¿cómo decide entre modo búsqueda y adversarial? ¿qué manda: la CLI o el JSON? ¿cómo arma el informe con las claves del Apéndice B? ¿dónde se elige la heurística y su default?
- Test: `tests/test_runner.py`.

### Paso 13 — `experiments/sweep.py` (99 líneas) y `__main__.py` (98 líneas)
`sweep.py`: `Sweep` → `expand` (qué combinaciones aplican) → `run_sweep` → `flatten` → `write_csv` / `write_json`. `__main__.py`: `_goal`, `_list_of`, `build_parser`, `main` (códigos de salida).
- Preguntas: ¿por qué `--k` solo aplica a Beam y `--heuristic` solo a A*/Beam? ¿cómo se aplanan los informes a una fila de CSV?
- Tests: `test_sweep.py`; ejecuta a mano 2–3 comandos de `docs/cases.md`.

### Paso 14 — `gui/session.py` (125 líneas) y luego `gui/app.py` (701 líneas)
`Session`: `start`, `reset`, `undo`, `outcome`, `play`, `move_for_click`, `destinations`, `wait_for`, `search`, `decide`, `side_to_move`. Luego `app.py` **solo a nivel de estructura** (qué método dibuja, cuál maneja clics, cuál lanza búsquedas); no hace falta línea por línea: es 5 % de la nota y no tiene lógica de juego.
- Tests: `test_gui_session.py`, `test_gui_app.py`. Ejecuta `uv run python -m tactical_grid.gui scenarios/caso_02_bfs_vs_ucs.json` y juega unos turnos.

### Paso 15 — Documentos que conectan todo
`docs/cases.md` (esperado vs. obtenido) → `docs/technical-report.md` (modelado, heurísticas, utilidad, complejidad, limitaciones, reporte de IA) → `docs/user-manual.md`. Confirma que lo escrito coincide con lo que leíste en el código (RD-01).

### Ruta rápida si el tiempo aprieta (prioridad para la sustentación)
1. `domain/rules.py::apply` y `successors` (reglas y costos) → 2. `uninformed.py` (BFS/UCS) → 3. `heuristics.py` + `informed.py::a_star` → 4. `adversarial.py::_decide` + `utility.py` → 5. `loader.py::build_scenario` → 6. `runner.py::run`. Con eso se responde la mayoría de lo que pregunta el profesor.

### Autoevaluación antes de la sustentación
- Sin mirar: explica el estado compuesto y por qué basta (RF-13).
- Predice en papel qué hace UCS si el pantano pasa de 7 a 15 en el caso 2; luego ejecútalo.
- Cambia profundidad y `orden_acciones` en el caso 7 y explica cada cambio en `pruned` y en el valor.
- Explica por qué MIN no está en desventaja.
- Pide a tu compañero que elija un método al azar y haz una modificación pequeña (p. ej. cambiar el desempate de UCS o un peso de la utilidad).
- Explica el uso de IA declarado y qué validaste tú.
