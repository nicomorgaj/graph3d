from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .i18n import DEFAULT_LANG, strings_for
from .loader import Graph

TEMPLATE = Path(__file__).with_name("template.html")


def build_payload(
    graph: Graph,
    positions: np.ndarray,
    radius: float,
    areas: list[dict],
    node_area: list[int],
    node_comm: np.ndarray,
    comm_names: list[str],
    comm_area: list[int],
    title: str,
    lang: str = DEFAULT_LANG,
) -> dict:
    degree = np.zeros(len(graph.nodes), dtype=np.int64)
    for source, target, _, _ in graph.edges:
        degree[source] += 1
        degree[target] += 1

    sizes = np.bincount(node_comm, minlength=len(comm_names))
    return {
        "title": title,
        "lang": lang,
        "i18n": strings_for(lang),
        "R": radius,
        "areas": areas,
        "nodes": [
            {
                "l": node["label"],
                "c": int(node_comm[i]),
                "a": int(node_area[i]),
                "f": node["file"],
                "loc": node["location"],
                "t": node["type"],
                "d": int(degree[i]),
                "p": [round(float(x), 2) for x in positions[i]],
            }
            for i, node in enumerate(graph.nodes)
        ],
        "edges": [[s, t, relation, confidence] for s, t, relation, confidence in graph.edges],
        "communities": [
            {"name": comm_names[c], "size": int(sizes[c]), "a": comm_area[c]} for c in range(len(comm_names))
        ],
    }


def build_html(payload: dict) -> str:
    template = TEMPLATE.read_text(encoding="utf-8")
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    data = data.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    marker = "/*__DATA__*/null"
    if marker not in template:
        raise RuntimeError("la plantilla no contiene el marcador de datos")
    return template.replace(marker, data, 1)
