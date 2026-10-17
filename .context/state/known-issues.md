# Known Issues

> Bugs conocidos. **No los redescubras ni los arregles sin que se pida.** Quitar la entrada al resolverse.

| Issue | Síntoma | Workaround | ¿Arreglar ahora? |
|---|---|---|---|
| Utilidad con pesos 10/3/1/0.5 | Minimax prefiere un recurso soltado bajo una unidad propia (U = 0) a llevarlo a más de 3 pasos de la base; profundidades pares aplanan valores (caso 10) | Ajustar los pesos en la sección `utilidad` del JSON | No, hasta que el equipo decida (ver decisions.md 2026-10-17) |
