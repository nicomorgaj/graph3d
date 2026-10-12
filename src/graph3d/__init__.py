"""graph3d: visor 3D interactivo y autocontenido para grafos de código y conocimiento."""

__version__ = "0.1.0"

_LAZY = {
    "Graph": "loader",
    "build_areas": "loader",
    "load_graph": "loader",
    "compute_layout": "layout",
    "group_communities": "layout",
    "build_html": "render",
    "build_payload": "render",
}

__all__ = sorted(_LAZY)


def __getattr__(name):
    if name in _LAZY:
        from importlib import import_module

        return getattr(import_module(f".{_LAZY[name]}", __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
