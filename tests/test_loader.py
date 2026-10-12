import json
import unittest

from graph3d.loader import build_areas, load_graph

from .helpers import TempDir, make_graph, write_graph


class LoadGraphTest(unittest.TestCase):
    def test_reads_nodes_and_links(self):
        with TempDir() as tmp:
            graph = load_graph(write_graph(tmp))
        self.assertEqual(len(graph.nodes), 60)
        self.assertGreaterEqual(len(graph.edges), 60)
        self.assertEqual(graph.nodes[0]["label"], "Node 0")

    def test_accepts_edges_key_and_alternative_field_names(self):
        data = {
            "nodes": [{"id": 1, "name": "A", "path": "x/a.py", "group": 2}, {"id": 2, "name": "B"}],
            "edges": [{"source": 1, "target": 2, "type": "uses"}],
        }
        with TempDir() as tmp:
            graph = load_graph(write_graph(tmp, data))
        self.assertEqual(graph.nodes[0]["label"], "A")
        self.assertEqual(graph.nodes[0]["file"], "x/a.py")
        self.assertEqual(graph.nodes[0]["community"], 2)
        self.assertEqual(graph.edges, [(0, 1, "uses", "")])

    def test_falls_back_to_id_as_label(self):
        with TempDir() as tmp:
            graph = load_graph(write_graph(tmp, {"nodes": [{"id": "solo"}], "links": []}))
        self.assertEqual(graph.nodes[0]["label"], "solo")

    def test_ignores_dangling_and_self_edges(self):
        data = {
            "nodes": [{"id": "a"}, {"id": "b"}],
            "links": [{"source": "a", "target": "zzz"}, {"source": "a", "target": "a"}, {"source": "a", "target": "b"}],
        }
        with TempDir() as tmp:
            graph = load_graph(write_graph(tmp, data))
        self.assertEqual(len(graph.edges), 1)

    def test_rejects_invalid_inputs(self):
        with TempDir() as tmp:
            with self.assertRaises(ValueError):
                load_graph(write_graph(tmp, {"links": []}))
            with self.assertRaises(ValueError):
                load_graph(write_graph(tmp, {"nodes": [{"label": "sin id"}]}))
            broken = tmp / "roto.json"
            broken.write_text("{no es json", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                load_graph(broken)


class BuildAreasTest(unittest.TestCase):
    def graph(self, **kwargs):
        with TempDir() as tmp:
            return load_graph(write_graph(tmp, make_graph(**kwargs)))

    def test_areas_come_from_the_top_level_folder(self):
        areas, assignment = build_areas(self.graph())
        names = [a["name"] for a in areas]
        self.assertEqual(sorted(names), sorted(["api", "web", "docs", "Externo"]))
        self.assertEqual(len(assignment), 60)

    def test_nodes_without_file_go_to_the_gray_external_area(self):
        areas, assignment = build_areas(self.graph())
        external = next(i for i, a in enumerate(areas) if a["name"] == "Externo")
        self.assertTrue(areas[external].get("gray"))
        self.assertEqual(assignment[5], external)

    def test_max_areas_folds_the_rest_into_others(self):
        areas, _ = build_areas(self.graph(), max_areas=3)
        names = [a["name"] for a in areas]
        self.assertIn("Otros", names)
        self.assertLessEqual(len([n for n in names if n not in ("Otros", "Externo")]), 2)

    def test_depth_two_splits_by_subfolder(self):
        data = make_graph(files=["src/api/a.py", "src/web/b.ts"])
        with TempDir() as tmp:
            graph = load_graph(write_graph(tmp, data))
        names = [a["name"] for a in build_areas(graph, depth=2)[0]]
        self.assertEqual(sorted(names), ["src/api", "src/web"])

    def test_english_labels(self):
        areas, _ = build_areas(self.graph(), lang="en")
        self.assertIn("External", [a["name"] for a in areas])

    def test_config_controls_names_hues_and_matching(self):
        config = {"areas": [{"name": "Servidor", "match": ["api/"], "hue": 10}, {"name": "Cliente", "match": "web/", "hue": 200}]}
        areas, assignment = build_areas(self.graph(), config=config)
        by_name = {a["name"]: a for a in areas}
        self.assertEqual(by_name["Servidor"]["hue"], 10)
        self.assertEqual(by_name["Cliente"]["hue"], 200)
        self.assertEqual(assignment[0], 0)
        self.assertEqual(assignment[2], 1)
        self.assertEqual(areas[assignment[4]]["name"], "Externo")

    def test_config_extension_rule(self):
        config = {"areas": [{"name": "Markdown", "match": "*.md"}]}
        areas, assignment = build_areas(self.graph(), config=config)
        self.assertEqual(areas[assignment[4]]["name"], "Markdown")

    def test_unknown_language_is_rejected(self):
        with self.assertRaises(ValueError):
            build_areas(self.graph(), lang="xx")


if __name__ == "__main__":
    unittest.main()
