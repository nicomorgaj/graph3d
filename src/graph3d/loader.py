from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .i18n import DEFAULT_LANG, strings_for



@dataclass
class Graph:
    nodes: list[dict]
    edges: list[tuple[int, int, str, str]]
    meta: dict = field(default_factory=dict)


def _first(mapping: dict, keys: tuple[str, ...], default=""):
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return value
    return default


def load_graph(path: str | Path) -> Graph:
    """Lee un grafo node-link (el formato de graphify, NetworkX y D3).

    Cada nodo necesita ``id``. Se aprovechan, si existen: ``label``/``name``,
    ``community``/``group``/``cluster``, ``community_name``, ``source_file``/``file``/``path``,
    ``source_location`` y ``file_type``. Las aristas pueden venir en ``links`` o ``edges``.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if "nodes" not in raw:
        raise ValueError("el JSON no tiene la clave 'nodes'")
    links = raw.get("links")
    if links is None:
        links = raw.get("edges", [])

    nodes: list[dict] = []
    index: dict[object, int] = {}
    for position, node in enumerate(raw["nodes"]):
        if "id" not in node:
            raise ValueError(f"el nodo {position} no tiene 'id'")
        index[node["id"]] = position
        community = _first(node, ("community", "group", "cluster"), None)
        nodes.append(
            {
                "id": node["id"],
                "label": str(_first(node, ("label", "name", "title"), node["id"])),
                "community": community,
                "community_name": _first(node, ("community_name", "community_label"), ""),
                "file": str(_first(node, ("source_file", "file", "path"), "")),
                "location": str(_first(node, ("source_location", "location", "line"), "")),
                "type": str(_first(node, ("file_type", "type", "kind"), "")),
            }
        )

    edges: list[tuple[int, int, str, str]] = []
    for link in links:
        source, target = link.get("source"), link.get("target")
        if source in index and target in index and index[source] != index[target]:
            relation = str(_first(link, ("relation", "label", "type"), ""))
            confidence = str(_first(link, ("confidence",), ""))
            edges.append((index[source], index[target], relation, confidence))

    return Graph(nodes=nodes, edges=edges, meta={"source": str(path)})


def _golden_hues(count: int, start: float = 24.0) -> list[float]:
    return [(start + i * 137.508) % 360 for i in range(count)]


def build_areas(
    graph: Graph,
    depth: int = 1,
    max_areas: int = 8,
    config: dict | None = None,
    lang: str = DEFAULT_LANG,
) -> tuple[list[dict], list[int]]:
    """Agrupa los nodos en áreas (el color principal del visor).

    Sin configuración, el área es la carpeta de primer nivel (``depth``) del archivo de
    origen. Con ``config`` (``{"areas": [{"name", "match", "hue"}]}``) se controla a mano:
    ``match`` es un prefijo de ruta, o una lista de prefijos.
    """
    text = strings_for(lang)
    external, others, root = text["external"], text["others"], text["root"]
    if config and config.get("areas"):
        return _areas_from_config(graph, config["areas"], external)

    keys: list[str] = []
    for node in graph.nodes:
        parts = [p for p in node["file"].replace("\\", "/").split("/") if p]
        if not node["file"]:
            keys.append(external)
        elif len(parts) <= depth:
            keys.append(root)
        else:
            keys.append("/".join(parts[:depth]))

    counts: dict[str, int] = {}
    for key in keys:
        counts[key] = counts.get(key, 0) + 1

    named = sorted((k for k in counts if k != external), key=lambda k: -counts[k])
    keep = named[: max(1, max_areas - 1)]
    overflow = [k for k in named if k not in keep]

    areas: list[dict] = []
    hues = _golden_hues(len(keep))
    for key, hue in zip(keep, hues):
        areas.append({"name": key, "hue": round(hue, 1)})
    area_index = {a["name"]: i for i, a in enumerate(areas)}
    if overflow:
        areas.append({"name": others, "hue": 0, "gray": True})
        area_index.update({k: len(areas) - 1 for k in overflow})
    if external in counts:
        areas.append({"name": external, "hue": 215, "gray": True})
        area_index[external] = len(areas) - 1

    return areas, [area_index[k] for k in keys]


def _areas_from_config(graph: Graph, specs: list[dict], external: str) -> tuple[list[dict], list[int]]:
    areas = [
        {
            "name": spec["name"],
            "hue": spec.get("hue", h),
            **({"gray": True} if spec.get("gray") else {}),
        }
        for spec, h in zip(specs, _golden_hues(len(specs)))
    ]
    fallback = len(areas)
    areas.append({"name": external, "hue": 215, "gray": True})

    def match_of(spec: dict) -> list[str]:
        value = spec.get("match", [])
        return [value] if isinstance(value, str) else list(value)

    assignment: list[int] = []
    for node in graph.nodes:
        file = node["file"].replace("\\", "/")
        chosen = fallback
        for i, spec in enumerate(specs):
            if any(_matches(file, rule) for rule in match_of(spec)):
                chosen = i
                break
        assignment.append(chosen)
    if fallback not in assignment:
        areas.pop()
    return areas, assignment


def _matches(file: str, rule: str) -> bool:
    if rule.startswith("*."):
        return file.endswith(rule[1:])
    return file.startswith(rule) or (rule and file == rule.rstrip("/"))

