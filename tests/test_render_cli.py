import json
import re
import shutil
import subprocess
import os
import unittest
from pathlib import Path
from unittest import mock

from graph3d.cli import main
from graph3d.i18n import STRINGS
from graph3d.layout import compute_layout, group_communities
from graph3d.loader import build_areas, load_graph
from graph3d.render import build_html, build_payload

from .helpers import TempDir, make_graph, write_graph

ROOT = Path(__file__).resolve().parent.parent


def payload_for(data, lang="es", title="Prueba"):
    with TempDir() as tmp:
        graph = load_graph(write_graph(tmp, data))
    areas, node_area = build_areas(graph, lang=lang)
    node_comm, names, comm_area = group_communities(graph, node_area)
    positions, radius = compute_layout(len(graph.nodes), graph.edges, node_comm, comm_area, len(areas))
    return build_payload(graph, positions, radius, areas, node_area, node_comm, names, comm_area, title=title, lang=lang)


class RenderTest(unittest.TestCase):
    def test_embeds_the_data_and_the_title(self):
        html = build_html(payload_for(make_graph()))
        self.assertNotIn("/*__DATA__*/null", html)
        data = json.loads(re.search(r"const DATA = (\{.*?\});\nconst T = DATA", html, re.S).group(1))
        self.assertEqual(data["title"], "Prueba")
        self.assertEqual(len(data["nodes"]), 60)
        self.assertEqual(data["lang"], "es")

    def test_labels_cannot_break_out_of_the_script_tag(self):
        data = make_graph()
        data["nodes"][0]["label"] = "</script><img src=x onerror=alert(1)>"
        html = build_html(payload_for(data))
        self.assertEqual(html.count("</script>"), 1)
        self.assertNotIn("</script><img", html)

    def test_both_languages_have_the_same_keys(self):
        self.assertEqual(set(STRINGS["es"]), set(STRINGS["en"]))

    def test_every_template_key_exists_in_the_dictionaries(self):
        template = (ROOT / "src" / "graph3d" / "template.html").read_text(encoding="utf-8")
        used = set(re.findall(r'data-i18n(?:-ph)?="(\w+)"', template)) | set(re.findall(r"\bT\.(\w+)", template))
        self.assertTrue(used)
        self.assertEqual(used - set(STRINGS["es"]), set())

    def test_node_payload_has_degree_and_position(self):
        payload = payload_for(make_graph())
        node = payload["nodes"][0]
        self.assertEqual(len(node["p"]), 3)
        self.assertGreater(node["d"], 0)


class CliTest(unittest.TestCase):
    def test_writes_html_and_png(self):
        with TempDir() as tmp:
            source = write_graph(tmp)
            out, png = tmp / "salida.html", tmp / "vista.png"
            code = main([str(source), "-o", str(out), "--png", str(png), "--title", "Mi repo", "--lang", "en"])
            self.assertEqual(code, 0)
            self.assertIn("Mi repo", out.read_text(encoding="utf-8"))
            self.assertEqual(png.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_default_output_name(self):
        with TempDir() as tmp:
            source = write_graph(tmp, name="mi-grafo.json")
            self.assertEqual(main([str(source)]), 0)
            self.assertTrue((tmp / "mi-grafo-3d.html").exists())

    def test_areas_config(self):
        with TempDir() as tmp:
            source = write_graph(tmp)
            config = tmp / "areas.json"
            config.write_text(json.dumps({"areas": [{"name": "Servidor", "match": "api/", "hue": 10}]}), encoding="utf-8")
            out = tmp / "o.html"
            self.assertEqual(main([str(source), "-o", str(out), "--areas-config", str(config)]), 0)
            self.assertIn("Servidor", out.read_text(encoding="utf-8"))

    def test_refuses_to_run_outside_a_virtualenv(self):
        with TempDir() as tmp:
            source = write_graph(tmp)
            with mock.patch("graph3d.cli.in_virtualenv", return_value=False), mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("GRAPH3D_ALLOW_SYSTEM", None)
                self.assertEqual(main([str(source), "-o", str(tmp / "o.html")]), 3)
                self.assertFalse((tmp / "o.html").exists())
                os.environ["GRAPH3D_ALLOW_SYSTEM"] = "1"
                self.assertEqual(main([str(source), "-o", str(tmp / "o.html")]), 0)

    def test_reports_errors_with_exit_code_2(self):
        with TempDir() as tmp:
            self.assertEqual(main([str(tmp / "no-existe.json")]), 2)
            empty = write_graph(tmp, {"nodes": [], "links": []}, name="vacio.json")
            self.assertEqual(main([str(empty)]), 2)
            broken = tmp / "roto.json"
            broken.write_text("{", encoding="utf-8")
            self.assertEqual(main([str(broken)]), 2)


@unittest.skipUnless(shutil.which("node"), "node no está instalado")
class ViewerInBrowserLikeEnvironmentTest(unittest.TestCase):
    def test_viewer_script_passes_its_js_tests(self):
        with TempDir() as tmp:
            source = write_graph(tmp)
            out = tmp / "visor.html"
            self.assertEqual(main([str(source), "-o", str(out)]), 0)
            result = subprocess.run(
                ["node", str(ROOT / "tests" / "js" / "viewer.test.js"), str(out)],
                capture_output=True, text=True, timeout=120,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("pruebas del visor OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
