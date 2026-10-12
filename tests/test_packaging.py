import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def requirement_lines(text):
    return sorted(line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#"))


class PackagingTest(unittest.TestCase):
    def test_requirements_match_pyproject_dependencies(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        declared = re.search(r"dependencies\s*=\s*\[(.*?)\]", pyproject, re.S).group(1)
        from_pyproject = sorted(item.strip().strip('"') for item in declared.split(",") if item.strip())
        from_requirements = requirement_lines((ROOT / "requirements.txt").read_text(encoding="utf-8"))
        self.assertEqual(from_pyproject, from_requirements)

    def test_python_files_do_not_import_anything_but_numpy_and_the_standard_library(self):
        allowed = {"numpy", "graph3d"}
        stdlib = {"__future__", "argparse", "colorsys", "dataclasses", "importlib", "json", "os", "pathlib", "struct", "sys", "zlib"}
        for path in (ROOT / "src" / "graph3d").glob("*.py"):
            for module in re.findall(r"^(?:from|import)\s+([A-Za-z_][\w]*)", path.read_text(encoding="utf-8"), re.M):
                self.assertIn(module, allowed | stdlib, f"{path.name} importa {module}")

    def test_template_loads_nothing_from_the_network(self):
        template = (ROOT / "src" / "graph3d" / "template.html").read_text(encoding="utf-8")
        self.assertNotRegex(template, r"(src|href)\s*=\s*[\"']https?://")
        self.assertNotIn("import(", template)


if __name__ == "__main__":
    unittest.main()
