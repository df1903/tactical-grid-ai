# Known Issues

> Bugs conocidos. **No los redescubras ni los arregles sin que se pida.** Quitar la entrada al resolverse.

| Issue | Síntoma | Workaround | ¿Arreglar ahora? |
|---|---|---|---|
| Batalla de placajes en mapas pequeños o abiertos | En `escenario_03x03` … `escenario_15x15` y a veces en `caso_01` el portador es placado justo al recoger y las partidas de IA contra IA llegan al límite de turnos (empate) | Usar mapas de 20×20 o más (`prueba_20x20`, `escenario_20x20`) o subir `juego.limite_turnos` | No: es una consecuencia de las reglas (decisions.md 2026-10-18) |
| Minimax puro a profundidad 6 en 15×15 | Tarda unos 10 s, por encima de la meta de 5 s | Usar alfa-beta (profundidad 7 en 2 s) o profundidad 5 con Minimax | No |
| Utilidad ignora el costo del terreno | Las rutas se miden en pasos, no en costo; el costo no decide quién gana porque cada turno es una sola acción | Documentado en el informe (sección 8); si se quiere, añadir un término de costo con peso configurable | No, hasta que el equipo decida |
| GUI: la persona bloqueada no pasa turno sola | Si el bando de la persona no tiene jugadas legales, la partida manual se queda esperando (la IA sí pasa sola) | «Aplicar jugada» juega por ella y desbloquea | No, hasta que se pida |
| Variante dinámica: la IA casi no roba | En las partidas medidas sobre el mapa del caso 7 hay 0–1 robos por partida; el robo, la penalización y la inmunidad solo se ejercitan en `tests/test_dynamic_rules.py` | Probar mapas más estrechos o subir `inmunidad_robo`/`penalizacion_placaje` en el JSON | No |
