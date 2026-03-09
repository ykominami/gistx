from __future__ import annotations

from pathlib import Path

from gistx.command_fix import (
    collect_existing_gistlist_counts,
    reconcile_fetch_entries,
    remove_empty_directories,
)


def test_remove_empty_directories_removes_empty_descendants_only(tmp_path: Path) -> None:
    gistlist_top = tmp_path / "gistlist"
    empty_dir = gistlist_top / "1" / "gistrepo" / "1" / "public" / "emptydir"
    keep_dir = gistlist_top / "1" / "gistrepo" / "1" / "public" / "keepdir"
    empty_dir.mkdir(parents=True)
    keep_dir.mkdir(parents=True)
    (keep_dir / "dummy.txt").write_text("ok", encoding="utf-8")

    removed = remove_empty_directories(gistlist_top)

    assert removed == 1
    assert not empty_dir.exists()
    assert keep_dir.exists()
    assert gistlist_top.exists()


def test_collect_existing_gistlist_counts_returns_sorted_numeric_dirs(tmp_path: Path) -> None:
    gistlist_top = tmp_path / "gistlist"
    gistlist_top.mkdir()
    (gistlist_top / "3").mkdir()
    (gistlist_top / "1").mkdir()
    (gistlist_top / "not-a-count").mkdir()
    (gistlist_top / "2.txt").write_text("ignore me", encoding="utf-8")

    counts = collect_existing_gistlist_counts(gistlist_top)

    assert counts == [1, 3]


def test_reconcile_fetch_entries_drops_extra_keys_and_backfills_missing(
    monkeypatch,
) -> None:
    timestamp = "2026-03-09 12:34:56"
    monkeypatch.setattr("gistx.command_fix.Timex.get_now", lambda: timestamp)
    fetch_assoc: dict[str, object] = {
        "1": ["2026-03-09 10:00:00", 2],
        "2": ["2026-03-09 10:05:00", 2],
        "3": ["2026-03-09 10:10:00", 2],
    }

    reconciled = reconcile_fetch_entries(fetch_assoc, [1, 3, 5])

    assert reconciled == {
        "1": ["2026-03-09 10:00:00", 2],
        "3": ["2026-03-09 10:10:00", 2],
        "5": [timestamp, 0],
    }


def test_reconcile_fetch_entries_returns_empty_for_no_numeric_dirs() -> None:
    fetch_assoc: dict[str, object] = {
        "1": ["2026-03-09 09:00:00", 4],
        "2": ["2026-03-09 09:30:00", 5],
    }

    reconciled = reconcile_fetch_entries(fetch_assoc, [])

    assert reconciled == {}
