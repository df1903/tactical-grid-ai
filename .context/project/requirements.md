# Requirements

> Requisitos globales del proyecto. El detalle de una feature va en su `sdd-NNN-<slug>/spec.md`.

## Funcionales
- Cargar escenarios JSON del formato del enunciado, sin modificar código, con validación atómica y errores claros (RF-34, RF-35, RF-36).
- Modelar un estado compuesto con sucesores, acciones válidas, meta y costo (RF-10 a RF-13).
- Implementar BFS, DFS y UCS con 6 métricas: éxito, longitud, generados, expandidos, máximo de frontera, tiempo (RF-14 a RF-19).
- Implementar A* con al menos 2 heurísticas justificadas y Beam Search con k = 1, 2, 4, 8 (RF-20 a RF-24).
- Implementar Minimax y alfa-beta con profundidad configurable, utilidad propia y 7 métricas (RF-25 a RF-33).
- Soportar los modos de prueba `busqueda`, `partida` y `adversarial`.
- Opción de verificación con los 6 chequeos (RF-42).
- GUI mínima: cuadrícula, terrenos, obstáculos, bases, recurso, unidades, bando, portador, turno y camino (RF-40).
- Entregar los 10 casos mínimos de demostración con resultado esperado vs. obtenido.
- Entregables: repo Git con README (nombres), instrucciones de instalación y ejecución, escenarios, manual de usuario, documento técnico con reporte de IA (sección 14 del enunciado).

## No funcionales
- Separación entre lógica, escenario, algoritmos e interfaz (RNF-05).
- Costos y posiciones nunca codificados; cualquier JSON válido se carga sin cambiar código (RNF-03, RNF-04).
- Reproducibilidad: estado inicial declarado y semillas fijas (RE-03, RE-04).
- Documentación de métodos consistente con la implementación (RD-01).
- Calidad: pruebas automáticas, `ruff` y `mypy --strict` en verde.
- Rendimiento: meta de tiempo de Minimax `<pendiente>`.
- Aportes de cada integrante visibles en Git (RE-01); versión entregada etiquetada (RE-02).

## Fuera de alcance
- Nada más allá de lo que pide el enunciado (decisión del usuario).
- Combate complejo, gráficos o animaciones elaboradas.
- Greedy / Best-First, aprendizaje por refuerzo, simulación estocástica y sistemas multiagente.
- GUI avanzada: opcional; si no alcanza el tiempo, el proyecto queda completo con la GUI mínima.
- Agente revisor de código y DoD: posterior a la configuración, no parte de este paso.
