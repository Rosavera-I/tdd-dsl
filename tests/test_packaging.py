from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_project_metadata_declares_src_package_and_cli_script(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(pyproject["project"]["name"], "tdd-dsl")
        self.assertEqual(pyproject["tool"]["setuptools"]["packages"]["find"]["where"], ["src"])
        self.assertEqual(pyproject["project"]["scripts"]["tdd-dsl"], "tdd_dsl.cli:main")


if __name__ == "__main__":
    unittest.main()
