from __future__ import annotations

STRINGS = {
    "es": {
        "search": "Buscar nodo (Enter para ir)…",
        "edges": "Aristas",
        "labels": "Etiquetas de nodos principales",
        "by_comm": "Colorear por comunidad (en vez de área)",
        "spin": "Rotación automática",
        "speed": "Velocidad",
        "reverse": "Girar al revés",
        "fit": "Encuadrar",
        "clear": "Quitar filtros",
        "fullscreen": "Pantalla completa (F)",
        "export_png": "Exportar PNG",
        "areas_title": "Áreas · puedes elegir varias",
        "comms_title": "Comunidades (5 o más nodos) · clic suma o quita",
        "hint": "Arrastra: rotar · Shift o clic derecho: mover · Rueda: zoom · Clic: seleccionar",
        "nodes": "nodos",
        "edges_n": "aristas",
        "communities": "comunidades",
        "connections": "conexiones",
        "node": "nodo",
        "community": "Comunidad",
        "external": "Externo",
        "others": "Otros",
        "root": "(raíz)",
    },
    "en": {
        "search": "Search node (Enter to jump)…",
        "edges": "Edges",
        "labels": "Labels for main nodes",
        "by_comm": "Color by community (instead of area)",
        "spin": "Auto-rotate",
        "speed": "Speed",
        "reverse": "Rotate backwards",
        "fit": "Fit view",
        "clear": "Clear filters",
        "fullscreen": "Fullscreen (F)",
        "export_png": "Export PNG",
        "areas_title": "Areas · pick as many as you like",
        "comms_title": "Communities (5+ nodes) · click to add or remove",
        "hint": "Drag: rotate · Shift or right-click: pan · Wheel: zoom · Click: select",
        "nodes": "nodes",
        "edges_n": "edges",
        "communities": "communities",
        "connections": "connections",
        "node": "node",
        "community": "Community",
        "external": "External",
        "others": "Other",
        "root": "(root)",
    },
}

DEFAULT_LANG = "es"


def strings_for(lang: str) -> dict[str, str]:
    if lang not in STRINGS:
        raise ValueError(f"idioma no soportado: {lang!r} (disponibles: {', '.join(sorted(STRINGS))})")
    return STRINGS[lang]
