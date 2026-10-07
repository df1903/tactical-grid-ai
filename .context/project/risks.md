# Risks

> Riesgos del proyecto. Revisar al cerrar cada fase.

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Minimax explota con mapa o profundidad grande | alta | alta | Profundidad configurable, alfa-beta, orden de sucesores, límite de tiempo |
| Heurística no admisible con costos externos | media | alta | Escalar por el costo transitable mínimo del JSON |
| Mapa externo rompe supuestos (costos fijos, tamaño) | media | alta | Cero constantes, pruebas con mapas variados |
| Un integrante no puede defender código ajeno | media | alta | Revisiones cruzadas, ensayo de sustentación |
| Documentación distinta del código (RD-01) | media | media | Revisar docstrings antes de etiquetar la versión |
| GUI consume tiempo, plazo 2026-10-21 | media | media | GUI mínima primero, avanzada opcional |
