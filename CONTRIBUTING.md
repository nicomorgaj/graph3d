# Contribuir

Todo corre dentro de un **venv**: ni la herramienta ni las pruebas usan el Python del sistema.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
make test            # unittest + pruebas del visor con node (si está instalado)
make demo            # regenera examples/sample-graph.json, docs/demo.html y docs/preview.png
```

Para usar otro venv: `make test VENV=/ruta/al/venv`.

## Antes de abrir un PR

- `make test` en verde. Si cambias el visor (`src/graph3d/template.html`), añade o ajusta una prueba en `tests/js/viewer.test.js`.
- Si cambias textos de la interfaz, ponlos en `src/graph3d/i18n.py` para **todos** los idiomas (hay una prueba que lo exige).
- Si cambias el diseño o los colores, ejecuta `make demo` y revisa `docs/preview.png`.
- Sin dependencias nuevas: la única es `numpy`, y el HTML generado no debe cargar nada externo.

## Estructura

| Ruta | Qué hace |
| --- | --- |
| `src/graph3d/loader.py` | Lee el grafo (node-link) y calcula las áreas |
| `src/graph3d/layout.py` | Comunidades y diseño 3D |
| `src/graph3d/render.py` | Arma el HTML a partir de `template.html` |
| `src/graph3d/preview.py` | PNG estático sin navegador |
| `src/graph3d/cli.py` | Línea de comandos |
| `tests/` | `unittest` y `tests/js/viewer.test.js` |
