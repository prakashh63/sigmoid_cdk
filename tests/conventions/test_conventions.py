from pathlib import Path

from tools.check_conventions import check_package

ROOT = Path(__file__).resolve().parents[2]


def test_source_follows_conventions() -> None:
    assert check_package(ROOT / "src" / "sigmoid_cdk") == []
