import json
import random
import tempfile
from pathlib import Path


def make_graph(files=None, communities=True, extra_edges=True):
    """Grafo pequeño y determinista para las pruebas."""
    rng = random.Random(3)
    files = files or ["api/users.py", "api/orders.py", "web/app.tsx", "web/cart.tsx", "docs/guide.md", ""]
    nodes, links = [], []
    for i in range(60):
        node = {"id": f"n{i}", "label": f"Node {i}", "source_file": files[i % len(files)]}
        if communities:
            node["community"] = i % 6
        nodes.append(node)
    for i in range(60):
        links.append({"source": f"n{i}", "target": f"n{(i + 6) % 60}", "relation": "calls", "confidence": "EXTRACTED"})
        if extra_edges and rng.random() < 0.5:
            links.append({"source": f"n{i}", "target": f"n{rng.randrange(60)}", "relation": "imports"})
    return {"nodes": nodes, "links": links}


def write_graph(directory, data=None, name="graph.json"):
    path = Path(directory) / name
    path.write_text(json.dumps(data or make_graph()), encoding="utf-8")
    return path


class TempDir:
    def __enter__(self):
        self._dir = tempfile.TemporaryDirectory()
        return Path(self._dir.name)

    def __exit__(self, *exc):
        self._dir.cleanup()
