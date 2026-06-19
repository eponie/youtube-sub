from unittest.mock import MagicMock, patch
import pytest
from youtube_sub.translator import GoogleBackend, _plan_batches, make_translator


def test_plan_batches_single_batch():
    texts = ["Hello", "World", "Foo"]
    batches = _plan_batches(texts)
    assert len(batches) == 1
    assert batches[0] == [0, 1, 2]


def test_plan_batches_splits_on_char_limit():
    # 建立超過 1500 字的批次
    long_text = "あ" * 800
    texts = [long_text, long_text, "短文"]
    batches = _plan_batches(texts)
    # 兩個 800 字加上分隔符會超過 1500，應該分成兩批
    assert len(batches) == 2


def test_plan_batches_oversized_single_item():
    huge = "あ" * 2000
    normal = "hello"
    texts = [normal, huge, normal]
    batches = _plan_batches(texts)
    # huge 應該獨立一批
    giant_batch = [b for b in batches if len(b) == 1 and b[0] == 1]
    assert len(giant_batch) == 1


def test_google_backend_calls_translator(monkeypatch):
    mock_gt = MagicMock()
    mock_gt.return_value.translate.return_value = "翻譯A\n@@@\n翻譯B"

    with patch("youtube_sub.translator.GoogleTranslator", mock_gt):
        backend = GoogleBackend(source="ja", target="zh-TW")
        result = backend._translate_batch(["テキストA", "テキストB"], mock_gt.return_value)

    assert result == ["翻譯A", "翻譯B"]


def test_google_backend_fallback_on_sep_mismatch(monkeypatch):
    mock_gt = MagicMock()
    # 回傳的分隔符數量不符，應 fallback 逐筆翻譯
    mock_gt.translate.side_effect = ["翻譯A只有一個", "翻譯A", "翻譯B"]

    backend = GoogleBackend(source="ja", target="zh-TW")
    result = backend._translate_batch(["テキストA", "テキストB"], mock_gt)

    assert result == ["翻譯A", "翻譯B"]


def test_make_translator_google():
    with patch("youtube_sub.translator.GoogleTranslator"):
        t = make_translator("google", source="ja", target="zh-TW")
    assert isinstance(t, GoogleBackend)


def test_make_translator_invalid():
    with pytest.raises(ValueError, match="Unknown translator"):
        make_translator("unknown", source="ja", target="zh-TW")
