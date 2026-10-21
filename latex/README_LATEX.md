# LaTeX Documentation for TacticalGrid

Este directorio contiene la versión LaTeX de la documentación del proyecto TacticalGrid,
generada a partir de los archivos Markdown en `../tactical-grid-ai/docs/`.

## Estructura

```
latex/
├── main.tex                    # Informe técnico (compilable)
├── manual.tex                  # Manual de usuario (compilable)
├── ucaldas.sty                 # Plantilla UCALDAS (paquete personalizado)
├── preambulo.tex               # Paquetes y configuraciones comunes
├── portada.tex                 # Portada común (logo UCALDAS, autores, fecha)
├── bibliography.bib            # Referencias bibliográficas
├── Makefile                    # Automatización de compilación (latexmk)
├── images/                     # Diagramas TikZ + logo UCALDAS
│   ├── logo_ucaldas.png        # Logo UCALDAS
│   ├── arquitectura.tikz       # Diagrama 1: Arquitectura
│   ├── ciclo_turno.tikz        # Diagrama 2: Ciclo de turno
│   ├── flujo_apply.tikz        # Diagrama 3: Flujo apply con interceptación
│   ├── clasificacion_algoritmos.tikz  # Diagrama 4: Clasificación algoritmos
│   ├── clases_escenario.tikz   # Diagrama 5: Clases del escenario JSON
│   ├── gantt_timeline.tikz     # Diagrama 6: Timeline (gantt)
│   ├── pie_nota.tikz           # Diagrama 7: Distribución de nota (pie)
│   ├── journey_progreso.tikz        # Diagrama 8: Progreso (journey)
│   ├── flujo_apply_intercept.tikz     # Flujo apply con interceptación
│   └── screenshots/             # Capturas PNG/JPG de GUI, CLI y JSON
├── chapters/                   # Capítulos del informe técnico (16 capítulos)
│   ├── 00_resumen.tex
│   ├── 01_introduccion.tex
│   ├── 02_modelado_estado.tex
│   ├── 03_reglas_juego.tex
│   ├── 04_costos.tex
│   ├── 05_arquitectura.tex
│   ├── 06_algoritmos_busqueda.tex
│   ├── 07_heuristicas.tex
│   ├── 08_busqueda_adversarial.tex
│   ├── 09_funcion_utilidad.tex
│   ├── 10_experimentacion.tex
│   ├── 10b_resultados.tex
│   ├── 11_verificacion_testing.tex
│   ├── 11b_casos_demostracion.tex
│   ├── 12_formato_json.tex
│   ├── 13_limitaciones.tex
│   ├── 14_uso_ia.tex
│   ├── 15_reproducibilidad.tex
│   └── 16_conclusiones.tex
├── manual_chapters/            # Capítulos del manual de usuario (8 capítulos)
│   ├── 01_requisitos.tex
│   ├── 02_inicio_rapido.tex
│   ├── 03_interfaz_grafica.tex
│   ├── 04_linea_comandos.tex
│   ├── 05_formato_json.tex
│   ├── 06_reproducir_experimentos.tex
│   ├── 07_tests_calidad.tex
│   └── 08_solucion_problemas.tex
└── README_LATEX.md             # Este archivo
```

## Compilación

### Requisitos
- TeX Live 2024+ (o MiKTeX en Windows)
- `latexmk` (incluido en TeX Live; requiere Perl en Windows)
- `lualatex` (para TikZ + pgfgantt + pgf-pie)
- Python 3.14 + `uv` (para generar diagramas si se regeneran)

### Compilar

```bash
cd latex

# Compilar ambos PDFs (LuaLaTeX)
make

# O compilar solo uno
make informe      # Manual_Tecnico.pdf
make manual       # Manual_de_Usuario.pdf

# Ver PDFs
make view-informe
make view-manual

# Limpiar
make clean
make clean-all    # también borra PDFs
```

### Verificar sin compilar
```bash
make check
```

## Diagrama TikZ

Los 8 diagramas Mermaid del HTML original se han convertido a TikZ nativo en `images/*.tikz`:

1. `arquitectura.tikz` - graph TD (7 nodos, flujo de datos)
2. `ciclo_turno.tikz` - stateDiagram-v2 (7 estados)
3. `flujo_apply.tikz` - flowchart TD (apply básico)
4. `clasificacion_algoritmos.tikz` - flowchart LR (4 subgrafos)
5. `clases_escenario.tikz` - classDiagram (11 clases)
5. `gantt_timeline.tikz` - gantt (6 fases, oct 2026)
6. `pie_nota.tikz` - pie chart (8 porciones)
7. `journey_progreso.tikz` - journey (8 fases, 33 hitos)
8. `flujo_apply_intercept.tikz` - flowchart TD (apply con interceptación)

Para compilar un diagrama individual:
```bash
cd latex/images
lualatex --shell-escape arquitectura.tikz
```

## Plantilla UCALDAS (`ucaldas.sty`)

Incluye:
- Colores institucionales (Azul #003366, Dorado #C8A84D)
- Configuración de página (márgenes UCALDAS)
- Encabezados/pies con `fancyhdr`
- Formato de capítulos/secciones con `titlesec`
- Configuración `minted` (estilo monokai, line numbers)
- TikZ libraries: automata, fit, matrix, pgfgantt, pgf-pie
- Hipervínculos con `hyperref` + `cleveref`
- Colores para tablas (LightBlue, LightGreen, etc.)

## Compilación

```bash
cd latex
make                    # compila Manual_Tecnico.pdf y Manual_de_Usuario.pdf
```

**Requisitos:** `latexmk`, `lualatex`, `python3` (para minted), `pygments` (`pip install pygments`).

En Windows con MiKTeX y Strawberry Perl:

```powershell
latexmk -lualatex -shell-escape -interaction=nonstopmode main.tex
latexmk -lualatex -shell-escape -interaction=nonstopmode manual.tex
```

Si VS Code estaba abierto antes de instalar Strawberry Perl, ciérralo y ábrelo de
nuevo para que herede el `PATH` actualizado.

## Diferencias con Markdown Original

| Aspecto | Markdown (`docs/`) | LaTeX (`latex/`) |
|---------|-------------------|------------------|
| Diagramas | Mermaid (JS) | TikZ nativo (PDF vectorial) |
| Código | Bloques markdown | `minted` (Pygments, syntax highlight) |
| Tablas | Markdown pipe | `longtable` + `booktabs` |
| Referencias | Manuales | `cleveref` automático |
| Bibliografía | Enlaces manuales | `biblatex` + `biber` (IEEE) |
| Compilación | Navegador | `latexmk` → PDF vectorial |

## Regenerar desde Markdown

Si actualizas los `.md` en `../tactical-grid-ai/docs/` y quieres regenerar el LaTeX:

1. Los `.md` son la **fuente de verdad**.
2. Los `.tex` en `chapters/` y `manual_chapters/` se editaron manualmente a partir de los `.md`.
3. Para sincronizar: edita los `.md` y luego actualiza los `.tex` correspondientes.

## Archivos Generados (No versionar)

```
*.aux, *.log, *.out, *.toc, *.lof, *.lot, *.bbl, *.blg, *.run.xml
*.synctex.gz, *.fls, *.fdb_latexmk

Los entregables `Manual_Tecnico.pdf` y `Manual_de_Usuario.pdf` se conservan junto a los fuentes.
```

Están en `.gitignore` (añadir al repo principal si no existe).

## Licencia

Documentación del proyecto TacticalGrid para UCALDAS 2026.
Código bajo licencia del repositorio principal.