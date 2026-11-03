"""Our 'awslint': checks the repository follows the framework conventions.

Rules
  1. Python file names are snake_case.
  2. File names are not vague (utils, misc, common, temp).
  3. Every public class has a docstring or sits in a file with a module docstring.
  4. Every package folder has an __init__.py.
  5. Construct files live in constructs/<aws_service>/ or constructs/serverless_backend/.

Usage: python tools/check_conventions.py [path-to-src-package]
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")
VAGUE_NAMES = {"utils", "misc", "common", "temp", "stuff"}
CONSTRUCT_FOLDERS = re.compile(r"^(aws_[a-z0-9]+|serverless_backend)$")


def check_package(package_dir: Path) -> list[str]:
    problems: list[str] = []
    for folder in [package_dir, *[p for p in package_dir.rglob("*") if p.is_dir()]]:
        if folder.name == "__pycache__":
            continue
        if not (folder / "__init__.py").exists():
            problems.append(f"{folder}: missing __init__.py")
    constructs_dir = package_dir / "constructs"
    if constructs_dir.exists():
        for sub in constructs_dir.iterdir():
            if (
                sub.is_dir()
                and sub.name != "__pycache__"
                and not CONSTRUCT_FOLDERS.match(sub.name)
            ):
                problems.append(f"{sub}: construct folders must be named aws_<service>")
    for path in package_dir.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        stem = path.stem
        if not SNAKE_CASE.match(stem):
            problems.append(f"{path}: file name must be snake_case")
        if stem in VAGUE_NAMES:
            problems.append(f"{path}: file name '{stem}' is too vague")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        has_module_doc = ast.get_docstring(tree) is not None
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                if ast.get_docstring(node) is None and not has_module_doc:
                    problems.append(f"{path}: class {node.name} needs a docstring")
    return problems


def main(argv: list[str]) -> int:
    package_dir = Path(argv[1]) if len(argv) > 1 else Path("src/sigmoid_cdk")
    problems = check_package(package_dir)
    for problem in problems:
        print(f"CONVENTION: {problem}")
    print(f"{len(problems)} problem(s) found")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
