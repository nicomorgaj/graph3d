from __future__ import annotations

import numpy as np

from .loader import Graph


def group_communities(graph: Graph, node_area: list[int]) -> tuple[np.ndarray, list[str], list[int]]:
    """Devuelve (comunidad de cada nodo, nombre de cada comunidad, área de cada comunidad).

    Si el grafo no trae comunidades, cada área pasa a ser una comunidad.
    """
    keys: list[tuple] = []
    for node, area in zip(graph.nodes, node_area):
        community = node["community"]
        keys.append(("c", community) if community is not None else ("a", area))

    order: dict[tuple, int] = {}
    for key in keys:
        order.setdefault(key, len(order))

    node_comm = np.array([order[k] for k in keys], dtype=np.int64)
    count = len(order)
    names = [""] * count
    areas_of = np.zeros((count, max(node_area, default=0) + 1), dtype=np.int64)
    for i, node in enumerate(graph.nodes):
        c = node_comm[i]
        if not names[c] and node["community_name"]:
            names[c] = str(node["community_name"])
        areas_of[c, node_area[i]] += 1
    comm_area = [int(row.argmax()) for row in areas_of]

    degree = np.zeros(len(graph.nodes), dtype=np.int64)
    for source, target, _, _ in graph.edges:
        degree[source] += 1
        degree[target] += 1
    for c in range(count):
        if not names[c]:
            members = np.where(node_comm == c)[0]
            names[c] = graph.nodes[int(members[degree[members].argmax()])]["label"]
    return node_comm, names, comm_area


def _fr(npts, pairs, weights, init, k, iters, gravity, temp0, repulsion=None):
    pos = init.astype(np.float64).copy()
    if npts <= 1:
        return pos
    src = np.array([p[0] for p in pairs], dtype=np.int64) if pairs else np.zeros(0, dtype=np.int64)
    dst = np.array([p[1] for p in pairs], dtype=np.int64) if pairs else np.zeros(0, dtype=np.int64)
    w = np.array(weights, dtype=np.float64) if pairs else np.zeros(0)
    rep = np.ones(npts) if repulsion is None else repulsion
    temp = temp0
    chunk = 300
    for _ in range(iters):
        disp = np.zeros_like(pos)
        for a in range(0, npts, chunk):
            block = pos[a : a + chunk]
            delta = block[:, None, :] - pos[None, :, :]
            dist2 = np.einsum("ijk,ijk->ij", delta, delta) + 0.01
            force = (k * k) * rep[None, :] / dist2
            disp[a : a + chunk] += np.einsum("ij,ijk->ik", force, delta)
        if len(src):
            delta = pos[src] - pos[dst]
            dist = np.linalg.norm(delta, axis=1, keepdims=True) + 0.01
            pull = delta * dist * w[:, None] / k
            np.add.at(disp, src, -pull)
            np.add.at(disp, dst, pull)
        disp -= pos * gravity
        length = np.linalg.norm(disp, axis=1, keepdims=True) + 0.01
        pos += disp / length * np.minimum(length, temp)
        temp *= 0.96
    return pos


def _fibonacci_sphere(count: int) -> np.ndarray:
    points = []
    for i in range(count):
        y = 1 - 2 * (i + 0.5) / max(count, 1)
        r = max(0.0, 1 - y * y) ** 0.5
        theta = 2.399963 * i
        points.append((np.cos(theta) * r, y, np.sin(theta) * r))
    return np.array(points)


def compute_layout(
    n_nodes: int,
    edges: list[tuple[int, int, str, str]],
    node_comm: np.ndarray,
    comm_area: list[int],
    n_areas: int,
    seed: int = 7,
) -> tuple[np.ndarray, float]:
    """Posiciones 3D en dos niveles: esferas de comunidad y nodos dentro de cada esfera.

    Las comunidades se acercan según cuántas aristas las unen, cada área parte de una
    región propia y las comunidades aisladas se acercan al núcleo para no aplastar la vista.
    Devuelve (posiciones Nx3, radio de encuadre).
    """
    if n_nodes == 0:
        return np.zeros((0, 3)), 300.0

    rng = np.random.default_rng(seed)
    k_comm = int(node_comm.max()) + 1 if n_nodes else 0
    members = [np.where(node_comm == c)[0] for c in range(k_comm)]
    sizes = np.array([len(m) for m in members], dtype=np.float64)
    radius = 6.0 * sizes ** (1 / 3) + 4.0

    pair_weight: dict[tuple[int, int], int] = {}
    for s, t, _, _ in edges:
        a, b = int(node_comm[s]), int(node_comm[t])
        if a != b:
            key = (min(a, b), max(a, b))
            pair_weight[key] = pair_weight.get(key, 0) + 1
    pairs = list(pair_weight)
    weights = [min(1.0 + np.log1p(pair_weight[p]) * 0.6, 4.0) for p in pairs]

    anchors = _fibonacci_sphere(max(n_areas, 1)) * 120
    init = np.array([anchors[comm_area[c]] + rng.normal(scale=40, size=3) for c in range(k_comm)])
    centers = _fr(k_comm, pairs, weights, init, k=34.0, iters=220, gravity=0.015, temp0=60.0, repulsion=np.sqrt(sizes))

    centers -= centers.mean(axis=0)
    connected = np.zeros(k_comm, dtype=bool)
    for a, b in pairs:
        connected[a] = connected[b] = True
    norms = np.linalg.norm(centers, axis=1)
    reference = norms[connected] if connected.any() else norms
    core = float(np.percentile(reference, 85)) or 1.0
    cap = core * 0.85
    far = norms > cap
    centers[far] *= ((cap + (norms[far] - cap) * 0.04) / norms[far])[:, None]

    for _ in range(400):
        delta = centers[:, None, :] - centers[None, :, :]
        dist = np.linalg.norm(delta, axis=2) + 1e-6
        need = radius[:, None] + radius[None, :] + 5.0
        overlap = np.clip(need - dist, 0, None)
        np.fill_diagonal(overlap, 0)
        if overlap.max() < 0.5:
            break
        push = (delta / dist[:, :, None]) * (overlap[:, :, None] * 0.5)
        centers += push.sum(axis=1) * 0.5

    local_pairs: dict[int, list[tuple[int, int]]] = {c: [] for c in range(k_comm)}
    for s, t, _, _ in edges:
        if node_comm[s] == node_comm[t]:
            local_pairs[int(node_comm[s])].append((s, t))

    pos = np.zeros((n_nodes, 3))
    for c in range(k_comm):
        ms = members[c]
        if len(ms) == 1:
            pos[ms[0]] = centers[c]
            continue
        where = {int(v): i for i, v in enumerate(ms)}
        lp = [(where[s], where[t]) for s, t in local_pairs[c]]
        local = _fr(len(ms), lp, [1.0] * len(lp), rng.normal(size=(len(ms), 3)), k=1.0, iters=70, gravity=0.08, temp0=0.5)
        local -= local.mean(axis=0)
        peak = np.linalg.norm(local, axis=1).max() or 1.0
        pos[ms] = centers[c] + local / peak * radius[c]

    pos -= pos.mean(axis=0)
    reach = float(np.linalg.norm(pos, axis=1).max()) or 1.0
    pos *= 300.0 / reach
    return pos, 300.0
