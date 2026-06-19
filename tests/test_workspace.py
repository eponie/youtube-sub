import json
from pathlib import Path
import pytest
from youtube_sub.workspace import WorkDir


def test_create_makes_dir_and_meta(tmp_path):
    wd = WorkDir.create(
        base_dir=tmp_path,
        url="https://youtu.be/abc123",
        video_id="abc123",
        title="Test Video Title!!",
        lang="ja",
        model="large-v3-turbo",
        to="zh-TW",
        translator="google",
    )
    assert wd.path.exists()
    assert (wd.path / "meta.json").exists()
    meta = json.loads((wd.path / "meta.json").read_text())
    assert meta["video_id"] == "abc123"
    assert meta["steps"] == {"download": "pending", "transcribe": "pending", "translate": "pending"}


def test_dir_name_format(tmp_path):
    wd = WorkDir.create(
        base_dir=tmp_path,
        url="https://youtu.be/abc123",
        video_id="abc123",
        title="Test Video Title!!",
        lang="ja", model="large-v3-turbo", to="zh-TW", translator="google",
    )
    # title[:20] = "Test Video Title!!" → re.sub(r'\W', '') = "TestVideoTitle"
    assert wd.path.name == "abc123_TestVideoTitle"


def test_safe_title_all_non_word(tmp_path):
    wd = WorkDir.create(
        base_dir=tmp_path,
        url="https://youtu.be/abc123",
        video_id="abc123",
        title="!!??##",
        lang="ja", model="large-v3-turbo", to="zh-TW", translator="google",
    )
    # 全部非 \W 字元，fallback 用 video_id
    assert wd.path.name == "abc123_abc123"


def test_load_roundtrip(tmp_path):
    wd = WorkDir.create(
        base_dir=tmp_path,
        url="https://youtu.be/abc123",
        video_id="abc123",
        title="My Video",
        lang="ja", model="large-v3-turbo", to="zh-TW", translator="google",
    )
    wd2 = WorkDir.load(wd.path)
    assert wd2.video_id == "abc123"
    assert wd2.lang == "ja"
    assert wd2.steps == {"download": "pending", "transcribe": "pending", "translate": "pending"}


def test_mark_done_updates_meta(tmp_path):
    wd = WorkDir.create(
        base_dir=tmp_path,
        url="https://youtu.be/abc123",
        video_id="abc123",
        title="My Video",
        lang="ja", model="large-v3-turbo", to="zh-TW", translator="google",
    )
    wd.mark_done("download")
    assert wd.steps["download"] == "done"
    meta = json.loads((wd.path / "meta.json").read_text())
    assert meta["steps"]["download"] == "done"


def test_scan_returns_incomplete_only(tmp_path):
    for vid, title in [("id1", "Video1"), ("id2", "Video2")]:
        WorkDir.create(
            base_dir=tmp_path,
            url=f"https://youtu.be/{vid}",
            video_id=vid,
            title=title,
            lang="ja", model="large-v3-turbo", to="zh-TW", translator="google",
        )
    wd1 = WorkDir.load(tmp_path / "id1_Video1")
    for step in ("download", "transcribe", "translate"):
        wd1.mark_done(step)

    incomplete = WorkDir.scan(tmp_path)
    assert len(incomplete) == 1
    assert incomplete[0].video_id == "id2"


def test_is_complete(tmp_path):
    wd = WorkDir.create(
        base_dir=tmp_path,
        url="https://youtu.be/x",
        video_id="x",
        title="X",
        lang="ja", model="large-v3-turbo", to="zh-TW", translator="google",
    )
    assert not wd.is_complete()
    for step in ("download", "transcribe", "translate"):
        wd.mark_done(step)
    assert wd.is_complete()
