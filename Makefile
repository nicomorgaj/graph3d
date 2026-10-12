# Todo corre dentro de un venv. Por defecto .venv; para usar otro: make test VENV=/ruta/al/venv
VENV ?= .venv
PY   := $(VENV)/bin/python

.PHONY: venv test demo clean

$(PY):
	python3 -m venv $(VENV)
	$(PY) -m pip install -r requirements.txt

venv: $(PY)

test: $(PY)
	PYTHONPATH=src $(PY) -m unittest discover -s tests -t . -v

demo: $(PY)
	$(PY) examples/make_sample.py examples/sample-graph.json
	PYTHONPATH=src $(PY) -m graph3d examples/sample-graph.json -o docs/demo.html --title "graph3d · demo" --png docs/preview.png

clean:
	rm -rf build dist src/*.egg-info
