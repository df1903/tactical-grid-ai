# Architecture

> Componentes del sistema y cómo se comunican. Estable: **solo cambia si cambia una decisión estructural**, no en cada feature.

## Componentes
- `domain` — estado compuesto, acciones, generación de sucesores, costos y reglas del juego.
- `scenario` — carga del JSON, validación atómica (9 validaciones mínimas) y traducción a objetos de `domain`.
- `algorithms` — búsqueda (BFS, DFS, UCS, A*, Beam) y decisión adversarial (Minimax, alfa-beta); heurísticas y función de utilidad. No conoce la GUI.
- `gui` — visualización y control; mínima obligatoria (RF-40), avanzada opcional.
- `experiments` — métricas, verificador de soluciones y casos mínimos reproducibles.

## Comunicación
- `scenario` → `domain`: devuelve un estado inicial y un catálogo de terrenos ya validados.
- `algorithms` → `domain`: consulta sucesores, costos y prueba de meta; nunca lee JSON ni conoce la interfaz.
- `experiments` → `algorithms`: ejecuta y mide (llamadas de Python; estructuras de resultado con campos equivalentes al Apéndice B del enunciado).
- `gui` → `scenario`, `algorithms`, `experiments`: solo orquesta y muestra; no contiene lógica de juego.
- Llamadas directas dentro de un solo proceso; sin red ni servicios.

## Datos
- Escenarios: `scenarios/*.json`; los escribe el equipo (o el profesor) y los lee `scenario`.
- Estado de partida: en memoria, inmutable, producido por `domain`.
- Resultados de experimentos: en memoria y expuestos en la GUI; exportación a archivo `<pendiente>`.
