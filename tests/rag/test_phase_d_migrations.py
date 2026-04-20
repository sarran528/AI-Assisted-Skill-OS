from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


VERSIONS_DIR = Path(__file__).resolve().parents[2] / "backend" / "alembic" / "versions"


class _FakeOp:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple, dict]] = []

    def __getattr__(self, name: str):
        def _capture(*args, **kwargs):
            self.calls.append((name, args, kwargs))

        return _capture


def _load_migration(file_name: str):
    path = VERSIONS_DIR / file_name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _call_names(fake_op: _FakeOp) -> list[str]:
    return [name for name, _args, _kwargs in fake_op.calls]


def test_018_upgrade_and_downgrade_operations(monkeypatch: pytest.MonkeyPatch) -> None:
    migration = _load_migration("018_add_rag_chunks_unique.py")
    fake_op = _FakeOp()
    monkeypatch.setattr(migration, "op", fake_op)

    migration.upgrade()
    migration.downgrade()

    names = _call_names(fake_op)
    assert "create_unique_constraint" in names
    assert "drop_constraint" in names


def test_019_upgrade_and_downgrade_operations(monkeypatch: pytest.MonkeyPatch) -> None:
    migration = _load_migration("019_create_doubt_log.py")
    fake_op = _FakeOp()
    monkeypatch.setattr(migration, "op", fake_op)

    migration.upgrade()
    migration.downgrade()

    names = _call_names(fake_op)
    assert "create_table" in names
    assert "create_index" in names
    assert "drop_index" in names
    assert "drop_table" in names


def test_020_upgrade_and_downgrade_operations(monkeypatch: pytest.MonkeyPatch) -> None:
    migration = _load_migration("020_create_tip_log.py")
    fake_op = _FakeOp()
    monkeypatch.setattr(migration, "op", fake_op)

    migration.upgrade()
    migration.downgrade()

    names = _call_names(fake_op)
    assert "create_table" in names
    assert "create_index" in names
    assert "drop_index" in names
    assert "drop_table" in names
