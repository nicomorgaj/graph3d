"""Genera un grafo sintético y determinista para probar graph3d (sin datos de ningún proyecto real)."""
import json
import random
import sys
from pathlib import Path

rng = random.Random(2026)

MODULES = {
    "api": ["users", "orders", "payments", "catalog", "auth", "shipping", "reports"],
    "web": ["cart", "checkout", "profile", "search", "admin", "layout"],
    "worker": ["emails", "invoices", "imports", "cleanup"],
    "docs": ["guide", "adr", "runbooks"],
}
SUFFIX = {"api": ".py", "web": ".tsx", "worker": ".py", "docs": ".md"}
VERBS = ["create", "update", "delete", "list", "validate", "parse", "render", "sync", "load", "send"]
NOUNS = ["Item", "Order", "Token", "Report", "Cart", "Invoice", "Rule", "Event", "Job", "Form"]

nodes, links = [], []
community_of_module = {}
for area, modules in MODULES.items():
    for module in modules:
        community_of_module[(area, module)] = len(community_of_module)

by_community = {}
for (area, module), community in community_of_module.items():
    size = rng.randint(14, 40) if area != "docs" else rng.randint(5, 10)
    ids = []
    for i in range(size):
        label = f"{rng.choice(VERBS)}{rng.choice(NOUNS)}()" if i else f"{module}{SUFFIX[area]}"
        node_id = f"{area}_{module}_{i}"
        nodes.append({
            "id": node_id,
            "label": label,
            "community": community,
            "community_name": f"{area}/{module}",
            "source_file": f"{area}/{module}{SUFFIX[area]}",
            "source_location": f"L{rng.randint(1, 400)}",
            "file_type": "document" if area == "docs" else "code",
        })
        ids.append(node_id)
    by_community[community] = ids
    for i in range(1, size):
        links.append({"source": ids[0], "target": ids[i], "relation": "contains", "confidence": "EXTRACTED"})
        if i > 2 and rng.random() < 0.6:
            links.append({"source": ids[rng.randint(1, i - 1)], "target": ids[i], "relation": "calls", "confidence": "EXTRACTED"})

cross = [
    ("web_cart", "api_orders"), ("web_checkout", "api_payments"), ("web_search", "api_catalog"),
    ("web_profile", "api_users"), ("web_admin", "api_reports"), ("web_layout", "api_auth"),
    ("worker_emails", "api_users"), ("worker_invoices", "api_payments"), ("worker_imports", "api_catalog"),
    ("api_orders", "api_payments"), ("api_orders", "api_shipping"), ("api_auth", "api_users"),
    ("docs_guide", "api_orders"), ("docs_adr", "api_payments"), ("docs_runbooks", "worker_emails"),
]
for source_prefix, target_prefix in cross:
    sources = [n["id"] for n in nodes if n["id"].startswith(source_prefix + "_")]
    targets = [n["id"] for n in nodes if n["id"].startswith(target_prefix + "_")]
    for _ in range(rng.randint(3, 8)):
        links.append({
            "source": rng.choice(sources), "target": rng.choice(targets),
            "relation": rng.choice(["calls", "imports", "references"]),
            "confidence": rng.choice(["EXTRACTED", "EXTRACTED", "INFERRED"]),
        })

for name in ("react", "express", "postgres", "redis"):
    nodes.append({"id": f"ext_{name}", "label": name, "source_file": ""})
    for node in rng.sample([n for n in nodes if n["id"].startswith(("api_", "web_", "worker_"))], 12):
        links.append({"source": node["id"], "target": f"ext_{name}", "relation": "imports", "confidence": "EXTRACTED"})

out = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).with_name("sample-graph.json"))
out.write_text(json.dumps({"nodes": nodes, "links": links}, ensure_ascii=False), encoding="utf-8")
print(f"{len(nodes)} nodos, {len(links)} aristas -> {out}")
