from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__
from .i18n import DEFAULT_LANG, STRINGS
from .loader import build_areas, load_graph


ENV_ALLOW_SYSTEM = "GRAPH3D_ALLOW_SYSTEM"


def in_virtualenv() -> bool:
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix) or bool(os.environ.get("VIRTUAL_ENV"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="graph3d",
        description="Genera un visor 3D interactivo (un solo HTML, sin dependencias) a partir de un grafo node-link.",
    )
    parser.add_argument("input", type=Path, help="grafo en JSON (nodes + links/edges), p. ej. graphify-out/graph.json")
    parser.add_argument("-o", "--output", type=Path, help="HTML de salida (por defecto <entrada>-3d.html)")
    parser.add_argument("--title", help="título del visor (por defecto, el nombre del archivo)")
    parser.add_argument("--lang", choices=sorted(STRINGS), default=DEFAULT_LANG, help="idioma de la interfaz")
    parser.add_argument("--areas-config", type=Path, help="JSON con las áreas a mano: {\"areas\": [{\"name\", \"match\", \"hue\"}]}")
    parser.add_argument("--depth", type=int, default=1, help="niveles de carpeta que definen un área (por defecto 1)")
    parser.add_argument("--max-areas", type=int, default=8, help="máximo de áreas; el resto va a «otros» (por defecto 8)")
    parser.add_argument("--seed", type=int, default=7, help="semilla del diseño (misma semilla, mismo dibujo)")
    parser.add_argument("--png", type=Path, help="además, escribe una vista previa estática en PNG")
    parser.add_argument("--version", action="version", version=f"graph3d {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not in_virtualenv() and not os.environ.get(ENV_ALLOW_SYSTEM):
        print(
            "error: graph3d solo corre dentro de un venv.\n"
            "  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt\n"
            "  .venv/bin/python -m graph3d <grafo.json>   (o usa bin/graph3d, que busca el venv solo)\n"
            f"  Para saltarte esta comprobación: {ENV_ALLOW_SYSTEM}=1",
            file=sys.stderr,
        )
        return 3
    from .layout import compute_layout, group_communities
    from .preview import render_png
    from .render import build_html, build_payload

    if not args.input.exists():
        print(f"error: no existe {args.input}", file=sys.stderr)
        return 2

    try:
        graph = load_graph(args.input)
    except (ValueError, json.JSONDecodeError) as error:
        print(f"error: {args.input} no es un grafo válido: {error}", file=sys.stderr)
        return 2
    if not graph.nodes:
        print("error: el grafo no tiene nodos", file=sys.stderr)
        return 2

    config = None
    if args.areas_config:
        config = json.loads(args.areas_config.read_text(encoding="utf-8"))

    areas, node_area = build_areas(graph, depth=args.depth, max_areas=args.max_areas, config=config, lang=args.lang)
    node_comm, comm_names, comm_area = group_communities(graph, node_area)
    positions, radius = compute_layout(len(graph.nodes), graph.edges, node_comm, comm_area, len(areas), seed=args.seed)
    payload = build_payload(
        graph, positions, radius, areas, node_area, node_comm, comm_names, comm_area,
        title=args.title or args.input.stem, lang=args.lang,
    )

    output = args.output or args.input.with_name(f"{args.input.stem}-3d.html")
    output.write_text(build_html(payload), encoding="utf-8")
    print(f"{len(graph.nodes)} nodos, {len(graph.edges)} aristas, {len(comm_names)} comunidades, {len(areas)} áreas -> {output}")
    if args.png:
        render_png(payload, args.png)
        print(f"vista previa -> {args.png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
