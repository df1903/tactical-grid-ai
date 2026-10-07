# Contexto integral — Proyecto 1 · TacticalGrid

> **Materia:** Sistemas Inteligentes I — Ingeniería de Sistemas y Computación, UCALDAS (Universidad de Caldas)
> **Corte / tipo:** Primer corte · Proyecto 1 (20 % de la nota total del curso)
> **Subtítulo oficial:** *Juego táctico 2D con búsqueda y toma de decisiones*
> **Lema del enunciado:** *El juego es el entorno de experimentación. El proyecto es el sistema inteligente que decide dentro de él.*
> **Fuentes usadas:** enunciado "Primer proyecto" (íntegro), presentación del curso (`2_presentacion`) y diapositivas de búsquedas (`3_busquedas`) para convenciones.

---

## 0. Cómo leer este documento

Cada requisito está etiquetado con su origen para que sepas qué es obligatorio y qué es una recomendación mía:

| Etiqueta | Significado |
|---|---|
| **[E]** | Está textualmente en el enunciado del proyecto. Es obligatorio. |
| **[C]** | Viene del material del curso (presentación o diapositivas), no del enunciado del proyecto. Aplica como convención o norma general. |
| **[A]** | **Análisis mío**: vacío, ambigüedad o requisito implícito que el enunciado no define. No es obligatorio por sí mismo, pero hay que decidirlo y documentarlo (ver sección 18). |

Los identificadores (RF = requisito funcional, RNF = no funcional, RD = documentación, RE = entrega/evaluación) permiten referenciar requisitos en tu repositorio, tu documento técnico o la lista de chequeo final.

---

## 1. Resumen ejecutivo

Se construye un **juego táctico 2D por turnos** sobre una cuadrícula vista desde arriba. Dos bandos (A y B) compiten por un **recurso** ubicado en una zona neutral: una unidad debe llegar a él, tomarlo y llevarlo a **su propia base** antes que el adversario.

No es un videojuego comercial: la interfaz solo debe permitir **observar y experimentar con la inteligencia del sistema**. Los gráficos, animaciones y efectos visuales no son el centro de la evaluación.

Sobre ese mismo problema, la pregunta va cambiando por etapas:

1. Encontrar **una ruta** → BFS y DFS.
2. Encontrar la ruta de **menor costo** → Costo Uniforme (UCS).
3. Usar **conocimiento del entorno** para orientar la búsqueda → A\* (con ≥ 2 heurísticas) y Beam Search (memoria limitada).
4. Decidir frente a **otro jugador que también razona** → Minimax y Minimax con poda alfa-beta.

**Pregunta central [E]:** ¿Cómo cambia la forma de decidir de un sistema inteligente cuando pasa de encontrar una ruta, a optimizar su costo, utilizar conocimiento heurístico y finalmente actuar frente a un adversario que también toma decisiones?

**Criterio de éxito [E]:** no basta con que los algoritmos funcionen; el equipo debe poder explicar *por qué* se comportan como lo hacen, *qué supuestos* sostienen sus decisiones y *cómo reaccionan ante un escenario que no habían visto*.

---

## 2. Contexto académico

### 2.1 El curso [C]

- Sistemas Inteligentes I introduce fundamentos conceptuales y prácticos para implementar sistemas capaces de resolver problemas, tomar decisiones, interactuar con su entorno y aprender de su experiencia.
- Seis unidades encadenadas: (1) Introducción a Sistemas Inteligentes, (2) Resolución de problemas, (3) Juegos como estrategia de búsqueda, (4) Procesos estocásticos y simulación, (5) Agentes, sistemas multiagente y automatización, (6) Aprendizaje por refuerzo.
- Metodología en cinco verbos: Comprender → Observar → Experimentar → Aplicar → Integrar. Cuatro hitos: Presentación, Taller/Práctica, Notebook (Python) y **Proyecto** ("integración de varias técnicas del curso en problemas más completos").
- Este proyecto integra las **Unidades 2 y 3**.

### 2.2 Peso en la nota del curso [C]

| Componente | % |
|---|---|
| Parcial 1 / 2 / 3 | 15 % c/u |
| **Proyecto 1** | **20 %** |
| Proyecto 2 | 25 % |
| Talleres y actividades | 10 % |

### 2.3 Qué se espera del estudiante [C]

Más que implementar algoritmos: comprenderlos, justificarlos, analizarlos y usarlos responsablemente. Se espera participación activa, comprensión real, trabajo autónomo, experimentación, responsabilidad en el uso de IA, integridad académica, trabajo colaborativo y pensamiento crítico (cuestionar resultados, supuestos y limitaciones).

---

## 3. Temas (conceptos) que el proyecto exige dominar

| Tema | Unidad | Dónde aparece en el proyecto |
|---|---|---|
| Formulación como espacio de estados (estado inicial, operadores, prueba de meta, costo) | 2 | Modelado del problema y del estado |
| Búsqueda en anchura (BFS) y en profundidad (DFS) | 2 | Búsqueda no informada |
| Costo uniforme (UCS), costo acumulado g(n) | 2 | Búsqueda basada en costos |
| Heurísticas: h(n), admisibilidad, distancia Manhattan | 2 | Búsqueda informada |
| A\*: f(n) = g(n) + h(n) | 2 | Búsqueda informada |
| Beam Search (memoria limitada, parámetro k) | 2 | Búsqueda con memoria limitada |
| Juegos de dos jugadores, árbol de juego, MAX/MIN | 3 | Decisión adversarial |
| Minimax con profundidad limitada y función de utilidad/evaluación | 3 | Decisión adversarial |
| Poda alfa-beta y su dependencia del orden de sucesores | 3 | Profundidad y poda alfa-beta |
| Complejidad en tiempo y espacio de cada método | 2–3 | Documentación de métodos, informe técnico, sustentación |
| Métricas y metodología experimental | transversal | Experimentación e interpretación |
| Uso responsable y declarado de IA generativa | 1 / reglas del curso | Documentación e informe técnico |

---

## 4. Reglas del juego

### 4.1 Reglas comunes (iguales para todos los equipos) [E]

- **RF-01** Escenario: cuadrícula 2D. Los mapas de **desarrollo** deben ser de **mínimo 20 × 20**; la aplicación debe admitir **otras dimensiones válidas** que lleguen por JSON.
- **RF-02** Elementos mínimos del mapa:

| Elemento | Regla mínima |
|---|---|
| Camino | Transitable, costo bajo |
| Terreno regular | Transitable, costo intermedio |
| Terreno difícil | Transitable, costo mayor |
| Obstáculo | No transitable |
| Base A / Base B | Zona de llegada de cada bando |
| Recurso | Objetivo estratégico de la partida |

- **RF-03** Los **costos salen del escenario cargado**, no de constantes dentro de los algoritmos.
- **RF-04** Deben existir mapas donde **una ruta con menos movimientos cueste más que una ruta más larga**.
- **RF-05** Cada bando controla **al menos 3 unidades**. Pueden ser idénticas o de tipos distintos, siempre que la diferencia tenga una función clara y no vuelva el proyecto "un sistema de combate excesivamente complejo".
- **RF-06** Juego **por turnos**: en cada turno un bando selecciona **una unidad** y realiza **una acción válida**. No hay concurrencia, movimiento simultáneo ni tiempo real.
- **RF-07** **Ambos bandos operan bajo las mismas reglas.** MAX y MIN no son inteligencias distintas ni de distinto nivel: son **roles** dentro del árbol Minimax.
- **RF-08** Objetivo: el recurso empieza en zona neutral; una unidad lo recoge al alcanzar su posición y, mientras lo transporta, intenta llegar a la base de su equipo. **Gana el bando que lleva el recurso a su propia base.**
- **RF-09** El equipo define **reglas deterministas** para: bloqueos, imposibilidad de continuar, ausencia de ruta válida y pérdida del portador del recurso. Deben ser coherentes con el modelo de estados y verificables en la sustentación.

### 4.2 Decisiones abiertas (las toma el equipo) [E]

Deben quedar **implementadas, documentadas y sustentadas**:

- Estructura interna del software.
- Representación interna del estado y estructuras auxiliares.
- **Segunda heurística** de A\*.
- **Función de utilidad** de Minimax.
- Detalles de las unidades (tipos, capacidades).
- Acciones adversariales adicionales (el enunciado menciona como ejemplos: avanzar, proteger una zona, bloquear una posición, aproximarse al recurso, interceptar al portador, "u otras definidas por el equipo").
- Reglas deterministas de la sección 4.1 (RF-09).

---

## 5. Modelado del problema y del estado

El enunciado lo declara **parte central** del proyecto (15 % del puntaje grupal): antes de pensar en algoritmos hay que definir qué información describe completamente una situación y qué acciones llevan de un estado a otro.

- **RF-10** Un estado basado solo en (fila, columna) **no es suficiente** cuando hay varias unidades, turnos, posesión del recurso y acciones adversariales.
- **RF-11** Principio clave [E]: *dos estados con una unidad en la misma casilla pueden ser distintos* (p. ej., si en uno la unidad transporta el recurso y en el otro no).
- **RF-12** La solución debe permitir identificar **inequívocamente**: estado inicial, acciones válidas, estados sucesores, condición objetivo y costo de las acciones.
- **RF-13** El equipo debe **explicar por qué su representación contiene la información suficiente** para decidir correctamente.

Contenido mínimo que, por lo que dicen el enunciado y el JSON, el estado compuesto necesita cubrir [A]: posición de cada unidad, bando de cada unidad, quién transporta el recurso (o posición del recurso si nadie lo lleva), y de quién es el turno. Cualquier otro campo (puntos de vida, tipo, etc.) depende de tus decisiones de diseño.

---

## 6. Algoritmos: requisitos por etapa

### 6.1 Búsqueda no informada — BFS y DFS (parte de 15 % grupal junto con UCS)

- **RF-14** Se ignora temporalmente al adversario. Una unidad va de una posición inicial a un objetivo sobre el mismo modelo de escenario.
- **RF-15** Implementar **BFS** y **DFS**.
- **RF-16** Métricas a registrar por ejecución:

| Métrica | Qué registrar |
|---|---|
| Solución encontrada | Sí / No |
| Longitud | Número de movimientos del camino |
| Estados generados | Estados incorporados a la búsqueda |
| Estados expandidos | Estados cuyos sucesores fueron analizados |
| Máximo de frontera | Mayor número de estados almacenados simultáneamente |
| Tiempo | Tiempo de ejecución medido por la aplicación |

### 6.2 Búsqueda basada en costos — UCS

- **RF-17** Implementar **Costo Uniforme**. Objetivo: minimizar el costo acumulado g(n), **no** la cantidad de movimientos.
- **RF-18** Preparar **al menos un escenario donde BFS y UCS den caminos distintos** y explicar el motivo a partir de los costos del mapa.
- **RF-19** [C] Convención del curso en UCS: prioridad = menor g(n); **en caso de empate se expande primero el nodo que entró primero a la frontera**; si aparece un camino más barato a un nodo ya conocido, se **actualiza** su costo.

### 6.3 Búsqueda informada — A\* (parte de 20 % grupal junto con Beam Search)

- **RF-20** Implementar A\* con **f(n) = g(n) + h(n)**.
- **RF-21** Trabajar con **al menos dos heurísticas**: una puede ser distancia Manhattan; **la segunda la propone y justifica el equipo**.
- **RF-22** Para cada heurística se debe explicar:
  1. Qué intenta estimar.
  2. Qué información del estado utiliza.
  3. Cuál es su costo computacional.
  4. Si se considera **admisible** y por qué.
  5. En qué escenarios orienta bien la búsqueda y en cuáles **pierde capacidad de discriminación**.

### 6.4 Búsqueda con memoria limitada — Beam Search

- **RF-23** Implementar **Beam Search** y experimentar con **k = 1, 2, 4 y 8 como mínimo**.
- **RF-24** El análisis debe discutir el efecto de restringir las alternativas conservadas y **mostrar si esa restricción puede descartar un camino que después habría sido conveniente**.

### 6.5 Decisión adversarial — Minimax y alfa-beta (20 % grupal)

- **RF-25** La pregunta cambia de "¿cuál es mi mejor camino?" a "¿cuál es mi mejor acción teniendo en cuenta las respuestas posibles del adversario?".
- **RF-26** Implementar **Minimax** y **Minimax con poda alfa-beta**, con **profundidad limitada**. La profundidad máxima **debe poder modificarse sin alterar el código** (en el JSON de ejemplo existe `juego.profundidad_maxima_minimax`).
- **RF-27** **Función de utilidad:** se define desde la perspectiva de **uno** de los bandos; MAX la maximiza y MIN la minimiza. Cada equipo construye **su propia** función de evaluación (no se entrega fórmula). Factores sugeridos: posesión del recurso, distancias relevantes, proximidad del adversario, unidades disponibles, costo acumulado, control de posiciones estratégicas.
- **RF-28** Aclaración conceptual obligatoria: **MIN no está en desventaja**; minimizar la utilidad de MAX es favorecer sus propios intereses en un modelo adversarial.
- **RF-29** Experimentar con **diferentes profundidades** y analizar cómo cambian los estados evaluados, el tiempo y, cuando ocurra, la acción seleccionada.
- **RF-30** Métricas de Minimax / alfa-beta:

| Métrica | Qué registrar |
|---|---|
| Nodos generados | Cantidad total generada durante la exploración |
| Nodos evaluados | Estados en los que se calculó utilidad |
| Nodos podados | Ramas evitadas por alfa-beta |
| Profundidad alcanzada | Profundidad efectiva de la búsqueda |
| Tiempo | Tiempo de ejecución |
| Acción seleccionada | Movimiento recomendado |
| Valor obtenido | Valor Minimax del estado analizado |

- **RF-31** Con **misma profundidad, misma función de utilidad y mismo orden de acciones**, Minimax y alfa-beta **deben producir la misma decisión**.
- **RF-32** Cambiar el **orden de generación de acciones** y **analizar cómo afecta la cantidad de poda**.
- **RF-33** En la sustentación se debe poder explicar por qué una acción recibe mejor valoración que otra y cómo cambiaría el comportamiento si se modifican los pesos o criterios de la utilidad.

---

## 7. Formato común de escenarios JSON (contrato de interoperabilidad)

La representación interna puede ser distinta, pero **cualquier archivo válido que respete el formato debe cargarse sin modificar el código fuente.** El profesor entregará **al menos un escenario no visto** durante la sustentación y la aplicación debe cargarlo y usarlo directamente.

### 7.1 Campos obligatorios [E]

| Campo | Descripción |
|---|---|
| `version` | Versión del formato de escenario |
| `mapa.filas` / `mapa.columnas` | Dimensiones de la cuadrícula |
| `tipos_terreno` | Catálogo de terrenos, costos y transitabilidad |
| `terreno` | Matriz que describe cada celda del mapa |
| `bases.A` / `bases.B` | Posiciones de las bases |
| `recurso` | Posición del recurso cuando no está siendo transportado |
| `unidades` | Listado de unidades: id, bando, tipo, posición |
| `turno` | Bando que debe actuar |
| `juego.portador_recurso` | Id de la unidad que transporta el recurso; `null` si nadie lo posee |
| `prueba` | Configuración **opcional** para ejecutar una prueba concreta |

- **RNF-01** Los nombres de campos y valores definidos por la especificación **deben respetarse**.
- **RNF-02** Se permiten **campos adicionales propios** si no alteran ni cambian el significado de los obligatorios.

### 7.2 Modos de prueba (campo `prueba.modo`) [E]

| Modo | Propósito |
|---|---|
| `busqueda` | Resolver una navegación concreta con BFS, DFS, UCS, A\* o Beam Search |
| `partida` | Cargar el escenario completo para continuar el juego por turnos |
| `adversarial` | Evaluar un estado mediante Minimax o alfa-beta y seleccionar una acción |

El ejemplo oficial usa `prueba: { "modo": "busqueda", "unidad_inicio": "A1", "objetivo": {"fila": 3, "columna": 2} }`. Ver el ejemplo completo en el Apéndice A.

### 7.3 Validación del escenario [E]

- **RF-34** La carga es **completa o no se aplica** (atómica). Antes de reemplazar el escenario actual se valida y se **explica con claridad cada error**. Un escenario inválido se rechaza **sin dejar el sistema parcialmente modificado**.
- **RF-35** Validaciones mínimas:
  1. Filas y columnas positivas y consistentes con la matriz.
  2. Todos los terrenos usados existen en `tipos_terreno`.
  3. Los terrenos transitables tienen **costo positivo**.
  4. Bases, recurso y unidades están dentro del mapa.
  5. Ninguna unidad está sobre una celda no transitable.
  6. Los identificadores de unidad son únicos.
  7. Cada unidad pertenece a `a` o `b`.
  8. El turno corresponde a `a` o `b`.
  9. Si `portador_recurso` no es `null`, identifica una unidad existente.

### 7.4 Compatibilidad con escenarios externos [E]

- **RF-36** Debe funcionar correctamente con escenarios válidos que cambien: dimensiones, distribución de terrenos, costos, obstáculos, posiciones de bases, unidades y recurso.
- **RF-37** Los costos se toman del JSON, **no de constantes dispersas**. Ejemplo del enunciado: el profesor puede cambiar el costo del pantano de 7 a 15 y pedir que el equipo **anticipe y luego observe** el efecto sobre UCS y A\*.
- **RNF-03** **No se realizarán modificaciones de código** para adaptar la aplicación al mapa suministrado en la sustentación.
- **RNF-04** Los algoritmos **no pueden depender de un mapa particular ni de posiciones escritas en el código**.

---

## 8. Resultados, visualización y verificación

### 8.1 Resultados y métricas comparables [E]

- **RF-38** La interfaz debe mostrar de forma clara las métricas con que se comparan los algoritmos. Para una prueba de búsqueda, la información mínima es **equivalente** a (ver Apéndice B): `algoritmo`, `exito`, `camino`, `costo`, `estados_generados`, `estados_expandidos`, `maximo_frontera`.
- **RF-39** No es obligatorio exportar cada resultado a JSON, pero la información equivalente debe ser **accesible** para que los experimentos sean **reproducibles y comparables**.

### 8.2 Visualización [E]

- **RF-40** Como mínimo mostrar: cuadrícula, tipos de terreno, obstáculos, bases, recurso, unidades, **bando de cada unidad**, **portador del recurso**, **turno actual**, y el **camino encontrado** cuando se ejecuta una búsqueda.
- **RF-41** (Se valora, no es obligatorio) observar **estados explorados, fronteras o decisiones consideradas**.
- La calidad artística **no** es criterio importante.

### 8.3 Verificación de soluciones [E]

- **RF-42** La aplicación debe incorporar una **opción de verificación** que compruebe que:
  1. Cada movimiento del camino es válido.
  2. Ninguna unidad atraviesa obstáculos.
  3. El costo reportado coincide con las transiciones realizadas.
  4. El estado final satisface la condición objetivo.
  5. No se generan estados inválidos.
  6. Las acciones consideradas por Minimax son legales según las reglas.

---

## 9. Estándares solicitados

### 9.1 Arquitectura y estructura del software [E]

- **RNF-05** Separación clara entre: **lógica del juego**, **representación del escenario**, **algoritmos de búsqueda/decisión** e **interfaz gráfica**.
- **RNF-06** Libertad para elegir la estructura interna, siempre cumpliendo lo anterior.

### 9.2 Documentación técnica de métodos [E]

Obligatoria para métodos con lógica relevante, **especialmente**: algoritmos de búsqueda, heurísticas, generación de sucesores, cálculo de costos, funciones de utilidad, Minimax, alfa-beta y validadores. No se exige para métodos triviales. Un comentario que solo diga "qué hace" **no es suficiente**.

| Elemento | Contenido esperado |
|---|---|
| **Purpose** | Responsabilidad concreta del método dentro de la solución |
| **Preconditions** | Condiciones que deben cumplirse antes de ejecutarlo |
| **Postconditions** | Condiciones que deben cumplirse tras una ejecución correcta |
| **Complexity** | Costo temporal y, cuando corresponda, espacial |
| **AI usage** | Indicar explícitamente **Yes** o **No** |
| **AI intervention** | Si hubo IA, describir con precisión en qué parte intervino |
| **Student validation** | Cómo se revisó, probó, modificó o validó el aporte generado con IA |

- **RD-01** La documentación debe corresponder a la **versión real** del método. Si describe una solución distinta de la implementada se considera **documentación inconsistente**.

### 9.3 Control de versiones [E]

- **RE-01** Repositorio **Git** que permita **evidenciar los aportes de cada integrante**, con `README.md` que incluya como mínimo los **nombres de los integrantes**.
- **RE-02** El repositorio y los documentos deben corresponder a **la misma versión presentada en la sustentación**.

### 9.4 Reproducibilidad [E]

- **RE-03** Datos reproducibles, **estado inicial declarado** y comparación de **resultados esperados vs. obtenidos** para cada caso mínimo.
- **RE-04** Evidencia suficiente para reproducir los experimentos reportados.

---

## 10. Uso de IA generativa e integridad académica

**Del enunciado [E]:**

- La IA generativa **puede usarse como apoyo**; su uso **no disminuye por sí mismo la calificación**, pero **debe declararse**.
- Cada estudiante es responsable de **todo el código** de la entrega y debe poder **explicarlo, modificarlo y defenderlo**.
- Una funcionalidad que opera bien pero que el estudiante no puede explicar, justificar o adaptar **no demuestra dominio suficiente**.
- La trazabilidad se verifica en la **documentación de métodos** (campos AI usage / AI intervention / Student validation) y en el **informe técnico** (reporte del uso de IA).
- **Omitir deliberadamente** el uso realizado se considera una **inconsistencia en la documentación del desarrollo**.

**Del curso [C]:**

- La IA es herramienta de apoyo al aprendizaje, no sustituto del aprendizaje ni de la autoría.
- Todo uso se declara indicando **herramienta utilizada y propósito**.
- El estudiante responde por todo lo que entrega.
- Ocultar ayudas externas o usar recursos no autorizados puede constituir vulneración de la integridad académica; aplican el Reglamento Estudiantil y el Estatuto Disciplinario de la Universidad de Caldas.
- En **exámenes parciales** el uso de IA está **prohibido** (no aplica a este proyecto, que sí la permite con declaración).
- Código de honor: reconocer fuentes, herramientas y aportes externos; no presentar como propio lo que no se comprende.

---

## 11. Restricciones y reglas duras (resumen)

**Prohibido / no permitido**

- Costos, posiciones o mapas **codificados** dentro de los algoritmos. [E]
- Modificar el código para adaptarlo al mapa de la sustentación. [E]
- Dejar el sistema en estado parcial tras una carga de escenario inválida. [E]
- Alterar el significado de los campos obligatorios del JSON. [E]
- Documentar un método de forma distinta a como está implementado. [E]
- Omitir deliberadamente el uso de IA. [E]
- Dar a MAX y MIN reglas o capacidades distintas. [E]
- Convertir el proyecto en un sistema de combate excesivamente complejo. [E]

**Obligatorio**

- Mínimo 20×20 en desarrollo, pero aceptar otras dimensiones. [E]
- ≥ 3 unidades por bando. [E]
- Reglas deterministas para bloqueos / sin ruta / pérdida del portador. [E]
- Profundidad de Minimax configurable sin tocar código. [E]
- Al menos 2 heurísticas, k ∈ {1,2,4,8} en Beam. [E]
- Opción de verificación en la aplicación. [E]
- Todo integrante capaz de explicar cualquier parte relevante. [E]

---

## 12. Stack tecnológico

**El enunciado NO especifica lenguaje, framework gráfico, librerías ni plataforma.** Lo único relacionado que aparece es:

- Que la interfaz sea **gráfica** (GUI) y muestre lo indicado en la sección 8.2. [E]
- Que los escenarios se carguen en **JSON** [E] y haya **Git** [E].
- Que en el curso las demostraciones prácticas se hacen con **notebooks en Python** [C] (esto describe los notebooks del curso, no obliga al proyecto).

Por tanto, el stack es **decisión del equipo** [A] y debe quedar justificado y documentado (instrucciones de instalación y ejecución son entregable [E]). Criterios útiles para decidirlo: soporte sólido de JSON, facilidad para construir una GUI simple, facilidad para medir tiempos, capacidad de que todos los integrantes puedan leer y modificar cualquier archivo en vivo (la sustentación incluye pedir una modificación pequeña), y facilidad para escribir pruebas.

---

## 13. Los 10 casos mínimos de demostración [E]

| # | Caso | Qué debe demostrarse |
|---|---|---|
| 1 | BFS frente a DFS | Ambos encuentran solución pero recorren el espacio de manera diferente |
| 2 | Ruta corta vs. ruta económica | BFS y UCS producen soluciones distintas por el costo del terreno |
| 3 | Obstáculo y heurística | El objetivo parece cercano, pero una barrera obliga a rodearlo |
| 4 | Comparación de heurísticas | A\* con las dos heurísticas sobre el mismo escenario |
| 5 | Beam Search | Cambiar k modifica la exploración y, cuando sea posible, la solución |
| 6 | Estado compuesto | La misma posición física representa estados distintos por información adicional del juego |
| 7 | Decisión adversarial | La mejor decisión según Minimax no coincide necesariamente con avanzar directo al recurso |
| 8 | Minimax vs. alfa-beta | Seleccionan la misma acción y alfa-beta evita evaluar parte del árbol |
| 9 | Orden de acciones | Cambiar el orden de sucesores modifica la cantidad de poda |
| 10 | Profundidad | El mismo estado se evalúa con distintas profundidades y se analizan los efectos |

Estos casos **no reemplazan** las pruebas externas del profesor.

---

## 14. Entregables [E]

1. Repositorio Git (aportes por integrante visibles; `README.md` con nombres).
2. Código fuente completo + instrucciones de instalación y ejecución.
3. Escenarios JSON usados en el desarrollo + casos mínimos de prueba.
4. Manual de usuario.
5. **Documento técnico** con: modelado del problema, representación de estados, reglas del juego, costos, heurísticas, función de utilidad, metodología experimental, resultados, análisis de complejidad, limitaciones y **reporte del uso de IA**.
6. Evidencia suficiente para reproducir los experimentos reportados.

Todo debe corresponder a la **misma versión** presentada en la sustentación.

---

## 15. Sustentación [E]

Tiene un **componente individual**: cada integrante debe poder explicar **cualquier parte relevante**, aunque no sea el autor principal del archivo o método. Puede pedírsele:

- Explicar la representación de un estado.
- Ejecutar BFS, DFS, UCS, A\* o Beam Search sobre un **escenario externo**.
- Justificar una heurística y discutir su admisibilidad.
- Explicar una decisión de Minimax y la función de utilidad.
- Explicar por qué MIN no está en desventaja frente a MAX.
- Analizar el efecto de cambiar la profundidad o el orden de acciones.
- Explicar la complejidad de un método.
- Explicar el uso de IA declarado y la validación realizada.
- **Realizar una modificación pequeña** si se solicita.

### Pruebas de comprensión y adaptación

El profesor puede introducir cambios no conocidos: cambiar costos de terreno en el JSON; mover obstáculos, bases, unidades o recurso; cambiar el objetivo de una prueba de navegación; modificar la profundidad de Minimax; cambiar el orden de generación de acciones; pedir otro algoritmo sobre el mismo escenario; **pedir una predicción razonada antes de ejecutar**; o **elegir un método al azar y pedir una modificación pequeña**. El propósito es comprobar comprensión, no agregar funcionalidades.

---

## 16. Evaluación [E]

**50 % grupal** (funcionalidad y calidad) + **50 % sustentación individual**. La valoración individual **puede afectar la nota final del estudiante** si hay una diferencia importante entre el funcionamiento del producto y su dominio real.

| Componente del 50 % grupal | % |
|---|---|
| Modelado del problema y representación de estados | 15 |
| BFS, DFS y Costo Uniforme | 15 |
| A\*, heurísticas y Beam Search | 20 |
| Minimax y poda alfa-beta | 20 |
| Experimentación, métricas e interpretación | 10 |
| Calidad y documentación técnica del código | 10 |
| Interfaz y visualización | 5 |
| Validación de escenarios y soluciones | 5 |
| **Total** | **100** |

---

## 17. Mapa de trazabilidad: componente evaluado → requisitos

| Componente | Requisitos clave |
|---|---|
| Modelado y estado (15) | RF-10 a RF-13, RF-09, caso 6 |
| BFS/DFS/UCS (15) | RF-14 a RF-19, casos 1–2 |
| A\*/heurísticas/Beam (20) | RF-20 a RF-24, casos 3–5 |
| Minimax/alfa-beta (20) | RF-25 a RF-33, casos 7–10 |
| Experimentación (10) | RF-16, RF-29, RF-30, RF-38, RF-39, RE-03, RE-04 |
| Interfaz (5) | RF-40, RF-41 |
| Validación (5) | RF-34, RF-35, RF-42 |
| Calidad/documentación (10) | RNF-05, RD-01, sección 9.2, RE-01, RE-02 |

---

## 18. Análisis de cobertura: ¿el enunciado cubre todo lo que el proyecto necesita?

**Respuesta corta:** cubre muy bien *qué se evalúa* y los contratos duros (JSON, métricas, validación, documentación, sustentación). **No cubre** varias decisiones de diseño que el proyecto necesita para ser implementable y defendible. Eso no es un error del enunciado: en su mayoría son "decisiones del equipo", pero hay que tomarlas **explícitamente** y documentarlas. Todo lo de esta sección es **[A]**.

### 18.1 Vacíos de definición (hay que decidirlos y documentarlos)

| # | Vacío | Por qué importa |
|---|---|---|
| G1 | **Stack** (lenguaje, GUI, librerías) no especificado | Condiciona todo; debe justificarse y quedar en las instrucciones de instalación |
| G2 | **Vecindad de movimiento** (4 vs 8 direcciones) no definida | Cambia estados sucesores, BFS/DFS, y qué heurística es admisible (Manhattan asume 4 direcciones) |
| G3 | **Semántica del costo**: ¿se paga al *entrar* a la celda? ¿la celda inicial cuesta? ¿cuánto cuestan las acciones que no son mover? | Afecta g(n), UCS, A\* y la verificación del costo (RF-42) |
| G4 | **Ocupación y colisiones**: ¿pueden dos unidades compartir celda? ¿se puede pisar la base rival o la celda del recurso? ¿qué significa "interceptar", "bloquear", "proteger"? | Define el conjunto de acciones legales y, con ello, el factor de ramificación de Minimax |
| G5 | **Pérdida del portador**: ¿cómo se pierde el recurso y dónde queda? | El enunciado exige regla determinista pero no el mecanismo |
| G6 | **Fin de partida**: ¿empate? ¿límite de turnos? ¿qué pasa si un bando no tiene movimientos? | Necesario para los estados terminales de Minimax |
| G7 | **Estados repetidos**: ¿búsqueda sobre grafo (con conjunto de visitados) o sobre árbol? ¿DFS con límite de profundidad? | Afecta completitud, terminación de DFS y las métricas de generados/expandidos |
| G8 | **Orden de expansión y desempate** no definidos en el enunciado | Solo el curso lo define para UCS; conviene extender una convención a todos los algoritmos y documentarla |
| G9 | **Beam Search**: ¿con qué criterio se ordenan y recortan los k candidatos (h, f, g)? ¿por niveles? | Cambia el comportamiento y el análisis de si descarta caminos buenos |
| G10 | **Campos de `prueba` insuficientes**: el ejemplo solo trae `modo`, `unidad_inicio`, `objetivo`; no hay campos estándar para algoritmo, heurística, k, bando MAX o profundidad por prueba. Solo el nombre `"A_ESTRELLA"` aparece como ejemplo de algoritmo | Hay que definir (y documentar) cómo se elige el algoritmo; los campos propios están permitidos si no alteran los obligatorios (RNF-02). Conviene confirmarlo con el profesor |
| G11 | **Perspectiva de la utilidad**: ¿desde qué bando se mide? ¿cómo se cuenta una unidad de profundidad (una acción de un bando)? ¿cómo se valoran victoria/derrota? | Necesario para explicar valores Minimax y casos 7–10 |
| G12 | **Tipo numérico de los costos** (¿enteros o decimales?) | La validación exige solo "costo positivo"; un JSON externo podría traer decimales |
| G13 | **Criterios de rendimiento** (tiempo máximo, tamaño máximo de mapa) | En la sustentación se ejecuta sobre un mapa desconocido; Minimax puede explotar con muchas unidades |
| G14 | **Formato y canal de entrega** de documentos, idioma, fechas | No aparecen en el enunciado; confirmar con el profesor |
| G15 | **Tamaño del equipo** | No se menciona número de integrantes (solo "equipo") |

### 18.2 Ambigüedades o inconsistencias menores en el enunciado

- El catálogo `tipos_terreno` es **abierto**: los nombres del ejemplo (camino, pasto, bosque, pantano, muro) no son una lista cerrada, y la tabla de reglas habla de camino / regular / difícil / obstáculo. **No codifiques nombres de terreno**; lee el catálogo.
- La validación habla de bandos `a` y `b` en **minúscula**, pero el JSON de ejemplo usa `"A"` y `"B"` en mayúscula (en `bases`, `bando`, `turno`). Conviene aceptar ambas formas o confirmar la convención.
- Las coordenadas aparecen como objeto `{"fila": f, "columna": c}` en el JSON y como arreglo `[f, c]` en el ejemplo de resultado. Son contextos distintos (entrada vs salida), pero conviene fijar tu convención interna y respetarla.
- El ejemplo de resultado incluye el punto `[5,3]` que no cabe en el mapa de 4×4 del ejemplo de escenario: es un ejemplo ilustrativo de formato, no un caso coherente entre sí.
- El campo `muro` en el ejemplo no trae `costo`; solo `"transitable": false`. Tu parser debe tolerar la ausencia de costo en terrenos no transitables.

### 18.3 Requisitos implícitos que el enunciado no nombra pero que la sustentación va a exigir

- **Pruebas automáticas** (unitarias o de integración) sobre todo en validadores, generación de sucesores, cálculo de costos y algoritmos. El enunciado pide "casos mínimos de prueba" y "validación", lo que en la práctica se sostiene mejor con pruebas ejecutables.
- **Determinismo y semillas**: si usas aleatoriedad en algún punto (desempates, escenarios generados), fija semilla para que los experimentos sean reproducibles (RE-04).
- **Metodología experimental explícita**: qué escenarios, cuántas repeticiones para el tiempo, cómo se presentan los resultados (tablas/gráficas), cómo se interpretan. Es un 10 % del puntaje grupal.
- **Análisis de complejidad** con variables definidas (factor de ramificación b, profundidad de la solución d, profundidad máxima m, tamaño de frontera) para cada algoritmo, tanto en los docstrings como en el informe.
- **Etiquetado de versión** (por ejemplo un tag de Git) para cumplir "la misma versión presentada" (RE-02).
- **Contribuciones repartidas**: como el Git debe evidenciar aportes por integrante y la sustentación es individual sobre *cualquier* parte, conviene que todos toquen todos los módulos relevantes (revisiones cruzadas).
- **Informe de limitaciones** honesto (parte del documento técnico).

### 18.4 Observación sobre admisibilidad (para tu documento técnico)

Como los costos vienen del JSON y el profesor puede cambiarlos, la admisibilidad de una heurística depende de **cómo se relaciona con el costo mínimo por paso del mapa cargado**. Manhattan "pura" (1 por paso) es admisible si ningún paso cuesta menos de 1; si un escenario externo trajera costos menores, dejaría de serlo. Una forma segura de diseñarla es escalar por el **costo transitable mínimo leído del escenario**. Esto debe poder explicarse en la sustentación.

### 18.5 Temas del curso que NO exige el proyecto

- Greedy / Best First **no** aparece como requisito del proyecto (sí está en la Unidad 2). No es obligatorio, aunque puede servir como comparación.
- No hay requisito de aprendizaje, simulación estocástica ni sistemas multiagente (Unidades 4–6).

---

## 19. Preguntas sugeridas para el profesor

1. ¿Los movimientos son en 4 direcciones o en 8?
2. ¿El costo se cobra al entrar a la celda destino? ¿La celda inicial cuesta algo?
3. ¿Cuáles son los nombres canónicos de algoritmos y heurísticas que debe aceptar el campo `prueba` (BFS, DFS, UCS, A\*, BEAM…) y qué campos usar para `k`, heurística y profundidad?
4. ¿Se espera que la comparación `a`/`b` sea sensible a mayúsculas?
5. ¿Hay tamaño máximo de mapa o límite de tiempo de respuesta en la sustentación?
6. ¿Cuántos integrantes por equipo, y cuáles son la fecha y el formato de entrega y de sustentación?
7. ¿Se permite que dos unidades ocupen la misma celda?
8. ¿Los costos podrían ser decimales?

---

## 20. Lista de chequeo final de entrega

**Modelado y reglas**
- [ ] Estado compuesto definido y justificado (caso 6 demostrado).
- [ ] Reglas deterministas para bloqueos / sin ruta / pérdida del portador documentadas.
- [ ] Decisiones abiertas (G1–G15) tomadas y escritas en el documento técnico.

**Algoritmos**
- [ ] BFS, DFS, UCS implementados con las 6 métricas.
- [ ] A\* con ≥ 2 heurísticas, cada una con los 5 puntos de justificación.
- [ ] Beam Search probado con k = 1, 2, 4, 8.
- [ ] Minimax y alfa-beta con profundidad configurable y las 7 métricas.
- [ ] Mismo resultado Minimax vs. alfa-beta bajo las mismas condiciones.
- [ ] Análisis de orden de acciones y de profundidad.

**JSON y robustez**
- [ ] Carga atómica con las 9 validaciones y mensajes de error claros.
- [ ] Probado con dimensiones, costos, bases, obstáculos y unidades distintas.
- [ ] Ningún costo ni posición codificado en los algoritmos.
- [ ] Opción de verificación con los 6 chequeos.

**Interfaz**
- [ ] Muestra cuadrícula, terrenos, obstáculos, bases, recurso, unidades, bando, portador, turno y camino.

**Documentación y entrega**
- [ ] Docstrings con Purpose / Preconditions / Postconditions / Complexity / AI usage / AI intervention / Student validation.
- [ ] Documento técnico completo (incluye limitaciones y reporte de IA).
- [ ] Manual de usuario, instrucciones de instalación y ejecución.
- [ ] Escenarios JSON y los 10 casos con resultados esperados vs. obtenidos.
- [ ] Repositorio con README (nombres) y aportes visibles por integrante; versión etiquetada y coincidente con lo presentado.
- [ ] Uso de IA declarado (herramienta y propósito) y cada integrante puede explicar todo.

**Preparación de la sustentación**
- [ ] Cada integrante practicó: predecir antes de ejecutar, cambiar costos/profundidad/orden, y hacer una modificación pequeña.

---

## Apéndice A — Ejemplo oficial de escenario JSON [E]

```json
{
  "version": "1.0",
  "mapa": { "filas": 4, "columnas": 4 },
  "tipos_terreno": {
    "camino":  {"costo": 1, "transitable": true},
    "pasto":   {"costo": 2, "transitable": true},
    "bosque":  {"costo": 4, "transitable": true},
    "pantano": {"costo": 7, "transitable": true},
    "muro":    {"transitable": false}
  },
  "terreno": [
    ["camino", "camino", "pasto",  "pasto"],
    ["camino", "muro",   "bosque", "pasto"],
    ["camino", "camino", "pantano","pasto"],
    ["pasto",  "pasto",  "camino", "camino"]
  ],
  "bases": { "A": {"fila": 0, "columna": 0}, "B": {"fila": 3, "columna": 3} },
  "recurso": {"fila": 2, "columna": 2},
  "unidades": [
    {"id": "A1", "bando": "A", "tipo": "estandar", "fila": 0, "columna": 1},
    {"id": "A2", "bando": "A", "tipo": "estandar", "fila": 1, "columna": 0},
    {"id": "B1", "bando": "B", "tipo": "estandar", "fila": 3, "columna": 2},
    {"id": "B2", "bando": "B", "tipo": "estandar", "fila": 2, "columna": 3}
  ],
  "turno": "A",
  "juego": { "portador_recurso": null, "profundidad_maxima_minimax": 4 },
  "prueba": {
    "modo": "busqueda",
    "unidad_inicio": "A1",
    "objetivo": {"fila": 3, "columna": 2}
  }
}
```

## Apéndice B — Ejemplo oficial de resultado de búsqueda [E]

```json
{
  "algoritmo": "A_ESTRELLA",
  "exito": true,
  "camino": [[3,2], [3,3], [4,3], [5,3]],
  "costo": 9,
  "estados_generados": 42,
  "estados_expandidos": 21,
  "maximo_frontera": 13
}
```

*(Es un ejemplo de formato; no es coherente con el mapa 4×4 del Apéndice A.)*

## Apéndice C — Convenciones de búsqueda del curso [C]

- **Costo uniforme:** prioridad = g(n) (costo acumulado desde el estado inicial). Regla de expansión: extraer el nodo de menor g(n), expandir sucesores, calcular nuevos costos acumulados y **actualizar si aparece un camino más barato**. **Desempate: se expande primero el nodo que entró primero a la frontera.** En las trazas, la frontera se muestra ordenada y se anota qué nodo se expande y de cuál viene.
- **Heurística:** h(n) estima el costo restante; A\* ordena por f(n) = g(n) + h(n).
- **Generados vs. expandidos:** generado = entró a la búsqueda; expandido = se analizaron sus sucesores.

## Apéndice D — Glosario mínimo

| Término | Significado en este proyecto |
|---|---|
| Estado | Descripción completa de una situación del juego (no solo una posición) |
| Frontera | Conjunto de estados generados aún no expandidos |
| g(n) | Costo acumulado desde el estado inicial |
| h(n) | Estimación del costo restante hasta la meta |
| Admisible | Heurística que nunca sobreestima el costo real restante |
| MAX / MIN | Roles en el árbol Minimax; no son agentes distintos |
| Utilidad | Valor numérico de un estado desde la perspectiva de un bando |
| Poda alfa-beta | Descarte de ramas que no pueden cambiar la decisión de Minimax |
| Beam Search | Búsqueda que conserva solo las k mejores alternativas por nivel |
