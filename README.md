# youtube-sub

YouTube 影片一鍵下載音訊 → 語音轉字幕 → 字幕翻譯。

最常用情境：日文影片 → 日文 SRT → 繁體中文 SRT。

---

## Requirements

- Apple Silicon Mac (M series)
- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- ffmpeg: `brew install ffmpeg`

## Install

```bash
git clone https://github.com/eponie/youtube-sub
cd youtube-sub && bash install.sh
```

First run: download the Whisper model (~1.5GB, cached at `~/.cache/huggingface/hub/`):

```bash
youtube-sub warmup
```

---

## 快速開始

```bash
# 設定固定工作目錄（加到 ~/.zshrc 就不用每次指定）
export YOUTUBE_SUB_WORK_DIR=~/Movies/subtitles

# 日文影片 → 日文字幕 → 繁體中文字幕（預設值）
youtube-sub run "https://www.youtube.com/watch?v=VIDEO_ID"

# 英文影片 → 英文字幕（不翻譯）
youtube-sub run "https://..." --lang en --to en

# 臨時指定不同的工作目錄
youtube-sub run "https://..." --work-dir ~/Desktop

# 指定翻譯引擎為 Claude
youtube-sub run "https://..." --translator claude
```

> **貼上 URL 的技巧：** 若 zsh 把 URL 裡的 `?` 變成 `\?`，程式會自動修正，不用手動處理。

輸出的 SRT 檔案在自動建立的工作目錄下，例如：

```
~/Movies/
  dQw4w9WgXcY_NeverGonnaGiveYouUp/
    meta.json
    NeverGonnaGiveYouUp.ja.srt
    NeverGonnaGiveYouUp.zh-TW.srt
```

---

## 指令說明

### `run` — 完整流程

```
youtube-sub run <URL> [--lang ja] [--model large-v3-turbo] [--to zh-TW] [--translator google]
```

下載音訊、轉字幕、翻譯，一次完成。

| 選項 | 預設值 | 說明 |
|------|--------|------|
| `--lang` / `-l` | `ja` | 影片語言（Whisper 語言代碼） |
| `--model` / `-m` | `large-v3-turbo` | Whisper 模型 |
| `--to` / `-t` | `zh-TW` | 目標翻譯語言 |
| `--translator` | `google` | 翻譯引擎：`google` 或 `claude` |

### `download` — 只下載

```
youtube-sub download <URL> [--lang ja] [--model large-v3-turbo] [--to zh-TW] [--translator google]
```

建立工作目錄並下載音訊，不轉字幕。方便先下載、之後再跑轉錄。

### `transcribe` — 語音轉字幕

```
youtube-sub transcribe <工作目錄> [--lang ja] [--model large-v3-turbo]
```

對已下載的工作目錄執行 Whisper 轉錄。轉錄完成後音訊檔自動刪除。

### `translate` — 翻譯字幕

```
youtube-sub translate <工作目錄> [--to zh-TW] [--translator google]
```

讀取工作目錄的 `.<lang>.srt`，翻譯後輸出 `.<to>.srt`。

### `resume` — 繼續未完成的工作

```
youtube-sub resume
```

掃描**當前目錄**下所有含 `meta.json` 的子目錄，找出未完成的工作繼續執行。不接受任何參數，全部從各自的 `meta.json` 讀取設定。

### `warmup` — 預下載模型

```
youtube-sub warmup [--model large-v3-turbo]
```

預先下載 Whisper 模型到 HuggingFace cache，避免第一次轉錄時等待。

### `langs` — 查看語言代碼

```
youtube-sub langs
```

列出 `--lang` 和 `--to` 支援的語言代碼對照表。

> **注意：** `--lang` 使用 Whisper 代碼（如 `zh`），`--to` 使用 Google Translate 代碼（如 `zh-TW`），兩者不同。

---

## 工作目錄

**位置：執行指令時的當前目錄。** 每支影片自動建立一個子目錄：

```
<video_id>_<標題前20字（去除特殊符號）>/
  meta.json                   ← pipeline 設定與步驟狀態
  audio.m4a                   ← 暫存，轉錄完自動刪除
  <標題>.ja.srt               ← 轉錄產出
  <標題>.zh-TW.srt            ← 翻譯產出
```

`meta.json` 範例：

```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "video_id": "dQw4w9WgXcY",
  "title": "Rick Astley - Never Gonna Give You Up",
  "lang": "ja",
  "model": "large-v3-turbo",
  "to": "zh-TW",
  "translator": "google",
  "steps": {
    "download": "done",
    "transcribe": "done",
    "translate": "pending"
  }
}
```

每個 step 狀態為 `pending` 或 `done`，支援中斷後用 `resume` 繼續。

---

## 模組架構

```
youtube_sub/
  main.py          CLI 入口，所有 typer 指令
  downloader.py    yt-dlp 封裝：下載音訊、取得影片資訊
  transcriber.py   mlx-whisper 封裝：語音轉文字
  translator.py    翻譯後端：GoogleBackend + ClaudeBackend
  srt.py           字幕切割（按字數 + jieba 斷詞）、寫出 SRT
  srt_parser.py    讀取/修改/寫回既有 SRT 檔案
  workspace.py     WorkDir：管理工作目錄與 meta.json 狀態
```

---

## Whisper 模型選擇

| 模型 | 速度 | 精準度 | 大小 |
|------|------|--------|------|
| `tiny` | 最快 | 較低 | ~75MB |
| `small` | 快 | 中等 | ~250MB |
| `large-v3-turbo` | 中（預設） | 高 | ~1.5GB |
| `large-v3` | 慢 | 最高 | ~3GB |

模型 cache 位置：`~/.cache/huggingface/hub/`

---

## 環境需求

- Apple Silicon（M 系列 Mac）
- Python 3.12+
- `uv`（虛擬環境管理）
- ffmpeg（`brew install ffmpeg`）
- 使用 Claude 翻譯需設定 `ANTHROPIC_API_KEY`
