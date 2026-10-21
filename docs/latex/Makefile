# Makefile para compilar los PDFs de TacticalGrid
# Uso: make (compila ambos), make informe, make manual, make clean

LATEXMK = latexmk -lualatex -shell-escape -interaction=nonstopmode -synctex=1
MAIN = Manual_Tecnico
MANUAL = Manual_de_Usuario
PDFDIR = ../pdf

all: $(MAIN).pdf $(MANUAL).pdf

$(MAIN).pdf: main.tex preambulo.tex portada.tex ucaldas.sty chapters/*.tex images/*.tikz images/screenshots/*
	$(LATEXMK) -jobname=$(MAIN) main.tex
	@mkdir -p $(PDFDIR) && cp $(MAIN).pdf $(PDFDIR)/

$(MANUAL).pdf: manual.tex preambulo.tex portada.tex ucaldas.sty manual_chapters/*.tex images/*.tikz images/screenshots/*
	$(LATEXMK) -jobname=$(MANUAL) manual.tex
	@mkdir -p $(PDFDIR) && cp $(MANUAL).pdf $(PDFDIR)/

# Compilar solo diagramas TikZ a PDF individuales (para verificar)
tikz: images/arquitectura.tikz images/ciclo_turno.tikz images/flujo_apply.tikz \
      images/clasificacion_algoritmos.tikz images/clases_escenario.tikz \
      images/gantt_timeline.tikz images/pie_nota.tikz \
      images/journey_progreso.tikz images/flujo_apply_intercept.tikz

# Compilar un solo diagrama TikZ a PDF (ej: make tikz-arquitectura)
tikz-%: images/%.tikz
	cd images && lualatex --shell-escape $*.tikz

# Verificar sintaxis LaTeX sin compilar completo
check:
	@echo "Verificando main.tex..."
	@latexmk -lualatex -shell-escape -interaction=nonstopmode -dry-run main.tex > /dev/null && echo "main.tex OK" || echo "main.tex ERROR"
	@echo "Verificando manual.tex..."
	@latexmk -lualatex -shell-escape -interaction=nonstopmode -dry-run manual.tex > /dev/null && echo "manual.tex OK" || echo "manual.tex ERROR"

# Limpiar archivos auxiliares
clean:
	latexmk -C
	rm -f *.aux *.log *.out *.toc *.lof *.lot *.bbl *.blg *.run.xml *.synctex.gz *.fls *.fdb_latexmk
	rm -rf _minted

clean-all: clean
	rm -f $(MAIN).pdf $(MANUAL).pdf $(PDFDIR)/$(MAIN).pdf $(PDFDIR)/$(MANUAL).pdf

# Ver PDFs
view-informe: $(MAIN).pdf
	@xdg-open $(MAIN).pdf 2>/dev/null || open $(MAIN).pdf 2>/dev/null || start $(MAIN).pdf 2>/dev/null || echo "Abra manualmente $(MAIN).pdf"

view-manual: $(MANUAL).pdf
	@xdg-open $(MANUAL).pdf 2>/dev/null || open $(MANUAL).pdf 2>/dev/null || start $(MANUAL).pdf 2>/dev/null || echo "Abra manualmente $(MANUAL).pdf"

.PHONY: all clean clean-all check view-informe view-manual tikz