from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from yklibpy.common.timex import Timex

from gistx.command_clone import CommandClone
from gistx.gistinfo import GistInfo


@pytest.fixture
def clone_cmd() -> CommandClone:
    store = MagicMock()
    store.get_from_config.return_value = "unit-test-user"
    return CommandClone(store)


def test_record_timestamp_jst_matches_spec_format(monkeypatch: pytest.MonkeyPatch) -> None:
    fixed = datetime(2026, 3, 9, 10, 0, 0, tzinfo=Timex.JST)

    class FakeDateTime:
        @staticmethod
        def now(tz: object) -> datetime:
            assert tz is Timex.JST
            return fixed

    monkeypatch.setattr("gistx.command_clone.datetime", FakeDateTime)

    assert CommandClone._record_timestamp_jst() == "2026-03-09 10:00:00"


def test_parse_gh_gist_list_line_public_and_secret(clone_cmd: CommandClone) -> None:
    pub = clone_cmd._parse_gh_gist_list_line("abc1234  My gist title  public")
    assert pub is not None
    assert pub.gist_id == "abc1234"
    assert pub.name == "My gist title"
    assert pub.public is True

    sec = clone_cmd._parse_gh_gist_list_line("def5678  secret  secret")
    assert sec is not None
    assert sec.gist_id == "def5678"
    assert sec.name == "secret"
    assert sec.public is False


def test_parse_gh_gist_list_line_skips_header(clone_cmd: CommandClone) -> None:
    assert clone_cmd._parse_gh_gist_list_line("ID  DESCRIPTION  VISIBILITY") is None


def test_parse_gh_gist_list_line_invalid_raises(clone_cmd: CommandClone) -> None:
    with pytest.raises(ValueError, match="gist ID"):
        clone_cmd._parse_gh_gist_list_line("not-a-gist-id  foo  public")
    with pytest.raises(ValueError, match="Visibility"):
        clone_cmd._parse_gh_gist_list_line("abc1234  title  internal")


def test_parse_gh_gist_list_output(clone_cmd: CommandClone) -> None:
    stdout = "abc1234  one  public\ndef5678  two  secret\n"
    assoc = clone_cmd._parse_gh_gist_list_output(stdout)
    assert set(assoc.keys()) == {"abc1234", "def5678"}
    assert assoc["abc1234"].public is True
    assert assoc["def5678"].public is False


def test_filter_gists(clone_cmd: CommandClone) -> None:
    assoc = {
        "a": GistInfo("a", "a", True),
        "b": GistInfo("b", "b", False),
    }
    assert [g.gist_id for g in clone_cmd._filter_gists(assoc, CommandClone.REPO_KIND_PUBLIC)] == ["a"]
    assert [g.gist_id for g in clone_cmd._filter_gists(assoc, CommandClone.REPO_KIND_PRIVATE)] == ["b"]
    assert [g.gist_id for g in clone_cmd._filter_gists(assoc, CommandClone.REPO_KIND_ALL)] == ["a", "b"]


def test_filter_gists_invalid_kind(clone_cmd: CommandClone) -> None:
    with pytest.raises(ValueError, match="Invalid repo_kind"):
        clone_cmd._filter_gists({}, "bogus")


def test_limit_gists(clone_cmd: CommandClone) -> None:
    gists = [GistInfo(str(i), str(i), True) for i in range(5)]
    assert len(clone_cmd._limit_gists(gists, None)) == 5
    assert len(clone_cmd._limit_gists(gists, 2)) == 2
    assert [g.gist_id for g in clone_cmd._limit_gists(gists, 2)] == ["0", "1"]


def test_build_clone_dir_name(clone_cmd: CommandClone) -> None:
    assert clone_cmd._build_clone_dir_name("abc123def") == "abc123def"
    assert clone_cmd._build_clone_dir_name("abc:test") == "abc_test"


def test_get_next_numeric_dir_value_and_latest_gists_path(
    clone_cmd: CommandClone, tmp_path: Path
) -> None:
    top = tmp_path / "workspaces"
    top.mkdir()
    assert clone_cmd._get_next_numeric_dir_value(top) == 1
    (top / "1").mkdir()
    (top / "3").mkdir()
    assert clone_cmd._get_next_numeric_dir_value(top) == 4
    (top / "3" / "gists.yaml").write_text("{}", encoding="utf-8")
    latest = clone_cmd._get_latest_gists_path(top)
    assert latest == top / "3" / "gists.yaml"


def test_should_refresh_list(clone_cmd: CommandClone, tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspaces_top = workspace / "workspaces"
    workspace.mkdir()
    workspaces_top.mkdir()
    workspaces_yaml_path = workspace / "workspaces.yaml"

    assert clone_cmd._should_refresh_list(workspaces_yaml_path, workspaces_top, force=True) is True

    workspaces_yaml_path.write_text("", encoding="utf-8")
    assert clone_cmd._should_refresh_list(workspaces_yaml_path, workspaces_top, force=False) is True

    workspaces_yaml_path.write_text("1:\n  - '2026-01-01 00:00:00'\n  - 2\n", encoding="utf-8")
    assert clone_cmd._should_refresh_list(workspaces_yaml_path, workspaces_top, force=False) is True

    (workspaces_top / "1").mkdir()
    (workspaces_top / "1" / "gists.yaml").write_text("{}", encoding="utf-8")
    assert clone_cmd._should_refresh_list(workspaces_yaml_path, workspaces_top, force=False) is False


def test_load_yaml_file_non_mapping_raises(clone_cmd: CommandClone, tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ValueError, match="YAML root must be a mapping"):
        clone_cmd._load_yaml_file(p)


def test_clone_gists_existing_target_counts_failure(
    clone_cmd: CommandClone, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clone_dir = tmp_path / "1"
    clone_dir.mkdir()
    pub = clone_dir / "public"
    pub.mkdir()
    g = GistInfo("abc1234567890ab", "n", True)
    target = pub / clone_cmd._build_clone_dir_name(g.gist_id)
    target.mkdir()

    def fail_subprocess(*_a: object, **_k: object) -> object:  # pragma: no cover
        raise AssertionError("gh should not run when target exists")

    monkeypatch.setattr("gistx.command_clone.subprocess.run", fail_subprocess)

    ok, fail = clone_cmd._clone_gists([g], clone_dir)
    assert ok == 0
    assert fail == 1


def test_clone_gists_subprocess_success(
    clone_cmd: CommandClone, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clone_dir = tmp_path / "1"
    clone_dir.mkdir()

    class Result:
        returncode = 0
        stdout = b""
        stderr = b""

    monkeypatch.setattr("gistx.command_clone.subprocess.run", lambda *_a, **_k: Result())

    g = GistInfo("abc1234567890ab", "n", True)
    ok, fail = clone_cmd._clone_gists([g], clone_dir)
    assert ok == 1
    assert fail == 0

