from pathlib import Path
import pytest
from youtube_sub.srt import split_segments, write_srt, segments_to_srt, _fmt_time
from youtube_sub.srt_parser import parse_srt, render_srt, read_srt, write_srt_parsed


# ---------- srt.py ----------

def test_split_segments_short_passthrough():
    segs = [{"start": 0.0, "end": 2.0, "text": "短文字"}]
    result = split_segments(segs, max_chars=20)
    assert result == segs


def test_split_segments_long_splits():
    segs = [{"start": 0.0, "end": 4.0, "text": "一二三四五六七八九十一二三四五六七八九十一二三"}]
    result = split_segments(segs, max_chars=10)
    assert len(result) > 1
    assert result[0]["start"] == pytest.approx(0.0)
    assert result[-1]["end"] == pytest.approx(4.0)
    for seg in result:
        assert len(seg["text"]) <= 10


def test_write_srt_creates_file(tmp_path):
    segs = [
        {"start": 0.0, "end": 1.5, "text": "Hello"},
        {"start": 1.5, "end": 3.0, "text": "World"},
    ]
    out = tmp_path / "test.srt"
    write_srt(segs, out)
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:01,500" in content
    assert "Hello" in content


def test_fmt_time_no_millisecond_overflow():
    # 接近整秒邊界，不應產出 ms=1000
    assert _fmt_time(0.9999) == "00:00:01,000"
    assert _fmt_time(1.9995) == "00:00:02,000"
    assert _fmt_time(0.0) == "00:00:00,000"
    assert _fmt_time(3661.5) == "01:01:01,500"


def test_segments_to_srt_format():
    segs = [{"start": 0.0, "end": 1.0, "text": "Hi"}]
    srt = segments_to_srt(segs)
    lines = srt.strip().split("\n")
    assert lines[0] == "1"
    assert "-->" in lines[1]
    assert lines[2] == "Hi"


# ---------- srt_parser.py ----------

SRT_CONTENT = """\
1
00:00:00,000 --> 00:00:01,500
Hello

2
00:00:01,500 --> 00:00:03,000
World
"""


def test_parse_srt():
    segs = parse_srt(SRT_CONTENT)
    assert len(segs) == 2
    assert segs[0]["index"] == 1
    assert segs[0]["timing"] == "00:00:00,000 --> 00:00:01,500"
    assert segs[0]["text"] == "Hello"
    assert segs[1]["text"] == "World"


def test_render_srt_roundtrip():
    segs = parse_srt(SRT_CONTENT)
    rendered = render_srt(segs)
    segs2 = parse_srt(rendered)
    assert len(segs2) == 2
    assert segs2[0]["text"] == "Hello"
    assert segs2[1]["text"] == "World"


def test_read_write_srt_parsed(tmp_path):
    srt_file = tmp_path / "test.srt"
    srt_file.write_text(SRT_CONTENT, encoding="utf-8")
    segs = read_srt(srt_file)
    segs[0]["text"] = "Bonjour"
    out = tmp_path / "out.srt"
    write_srt_parsed(segs, out)
    result = read_srt(out)
    assert result[0]["text"] == "Bonjour"
    assert result[1]["text"] == "World"
