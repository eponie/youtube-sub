# youtube-sub

下載 YouTube 影片、取得字幕、翻譯成目標語言。

**字幕來源優先順序：** YouTube 手動字幕 → YouTube 自動字幕 → Whisper 語音轉錄。有 YouTube 字幕時不會跑 Whisper。

最常用情境：日文影片 → 日文 SRT → 繁體中文 SRT。

---

## 環境需求

- Apple Silicon Mac（M 系列）
- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- ffmpeg：`brew install ffmpeg`
- 使用 Claude 翻譯需設定 `ANTHROPIC_API_KEY`

## 安裝

```bash
git clone https://github.com/eponie/youtube-sub
cd youtube-sub && bash install.sh
```

預下載 Whisper 模型（~1.5GB，只在影片沒有 YouTube 字幕時才需要）：

```bash
youtube-sub warmup
```

---

## 快速開始

### CLI

```bash
# 設定固定輸出目錄（加到 ~/.zshrc）
export YOUTUBE_SUB_WORK_DIR=~/Movies/subtitles

# 日文影片 → 繁體中文（預設值）
youtube-sub run "https://www.youtube.com/watch?v=VIDEO_ID"

# 英文影片 → 繁體中文
youtube-sub run "https://..." --lang en

# 不翻譯
youtube-sub run "https://..." --lang en --to en

# 使用 Claude 翻譯
youtube-sub run "https://..." --translator claude
```

> **提示：** zsh 貼上 URL 時若把 `?` 變成 `\?`，程式會自動修正。

輸出檔案在每支影片自動建立的子目錄下：

```
~/Movies/subtitles/
  dQw4w9WgXcY_NeverGonnaGiveYouUp/
    meta.json
    NeverGonnaGiveYouUp.en.srt          ← YouTube 手動字幕
    NeverGonnaGiveYouUp.en.auto.srt     ← YouTube 自動字幕
    NeverGonnaGiveYouUp.zh-TW.srt       ← 翻譯結果
```

### Claude Code Skill

執行 `install.sh` 後，在 [Claude Code](https://claude.ai/code) 貼上 YouTube URL 即可：

```
youtube-sub https://www.youtube.com/watch?v=VIDEO_ID
youtube-sub https://www.youtube.com/watch?v=VIDEO_ID 英文轉繁體中文
youtube-sub https://www.youtube.com/watch?v=VIDEO_ID --lang en --to zh-TW --translator claude
```

Claude 會執行完整流程並回報產出檔案位置。

---

## 指令說明

### `run` — 完整流程

```
youtube-sub run <URL> [--lang ja] [--model large-v3-turbo] [--to zh-TW] [--translator google]
```

下載、取字幕（YouTube 優先，沒有才跑 Whisper）、翻譯，一次完成。

| 選項 | 預設值 | 說明 |
|------|--------|------|
| `--lang` / `-l` | `ja` | 影片語言（Whisper 語言代碼） |
| `--model` / `-m` | `large-v3-turbo` | Whisper 模型（有 YouTube 字幕時不使用） |
| `--to` / `-t` | `zh-TW` | 目標翻譯語言 |
| `--translator` | `google` | `google`、`claude` 或 `gemini` |

### `download` — 只下載

```
youtube-sub download <URL> [--lang ja] [--to zh-TW]
```

建立工作目錄、下載音訊，並抓取 YouTube 字幕（若有）。不執行轉錄。

### `transcribe` — Whisper 語音轉字幕

```
youtube-sub transcribe <工作目錄> [--lang ja] [--model large-v3-turbo]
```

對已下載的音訊執行 Whisper 轉錄，完成後自動刪除音訊檔。

### `translate` — 翻譯字幕

```
youtube-sub translate <工作目錄> [--to zh-TW] [--translator google]
```

讀取工作目錄的 `.<lang>.srt`，翻譯後輸出 `.<to>.srt`。

### `resume` — 繼續未完成的工作

```
youtube-sub resume
```

掃描當前目錄下所有含 `meta.json` 的子目錄，找出未完成的工作繼續執行。

### `warmup` — 預下載 Whisper 模型

```
youtube-sub warmup [--model large-v3-turbo]
```

### `langs` — 查看語言代碼

```
youtube-sub langs
```

> **注意：** `--lang` 使用 Whisper 代碼（如 `zh`），`--to` 使用 Google Translate 代碼（如 `zh-TW`），兩者不同。

---

## 工作目錄

每支影片自動建立一個子目錄：

```
<video_id>_<標題前20字>/
  meta.json                     ← pipeline 設定與步驟狀態
  audio.m4a                     ← 暫存，轉錄完自動刪除
  <標題>.<lang>.srt             ← YouTube 手動字幕或 Whisper 產出
  <標題>.<lang>.auto.srt        ← YouTube 自動字幕（若有）
  <標題>.<to>.srt               ← 翻譯結果
```

`meta.json` 記錄每個步驟狀態（`pending` / `done`），中斷後可用 `resume` 繼續。

---

## Whisper 模型

| 模型 | 速度 | 精準度 | 大小 |
|------|------|--------|------|
| `tiny` | 最快 | 較低 | ~75MB |
| `small` | 快 | 中等 | ~250MB |
| `large-v3-turbo` | 中（預設） | 高 | ~1.5GB |
| `large-v3` | 慢 | 最高 | ~3GB |

模型 cache 位置：`~/.cache/huggingface/hub/`

---

## 模組架構

```
youtube_sub/
  main.py          CLI 入口（typer 指令）
  downloader.py    yt-dlp 封裝：下載音訊、抓取 YouTube 字幕
  transcriber.py   mlx-whisper 封裝：語音轉文字
  translator.py    翻譯後端：Google、Claude、Gemini
  srt.py           字幕切割與 SRT 輸出
  srt_parser.py    讀取/修改既有 SRT 檔案
  workspace.py     WorkDir：工作目錄與 meta.json 管理
```

---
---

# youtube-sub (English)

Download YouTube videos, generate subtitles, and translate them.

**Subtitle source priority:** YouTube manual captions → YouTube auto-generated captions → Whisper transcription. Whisper only runs when no YouTube captions are available.

Most common use case: Japanese video → Japanese SRT → Traditional Chinese SRT.

---

## Requirements

- Apple Silicon Mac (M series)
- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- ffmpeg: `brew install ffmpeg`
- Claude translator: set `ANTHROPIC_API_KEY`

## Install

```bash
git clone https://github.com/eponie/youtube-sub
cd youtube-sub && bash install.sh
```

Pre-download the Whisper model (~1.5GB, only needed if videos don't have YouTube captions):

```bash
youtube-sub warmup
```

---

## Quick Start

### CLI

```bash
# Set a persistent output directory (add to ~/.zshrc)
export YOUTUBE_SUB_WORK_DIR=~/Movies/subtitles

# Japanese video → Traditional Chinese (defaults)
youtube-sub run "https://www.youtube.com/watch?v=VIDEO_ID"

# English video → Traditional Chinese
youtube-sub run "https://..." --lang en

# No translation
youtube-sub run "https://..." --lang en --to en

# Use Claude as translator
youtube-sub run "https://..." --translator claude
```

> **Tip:** If zsh escapes `?` to `\?` in pasted URLs, the tool handles it automatically.

Output files are created in a per-video subdirectory:

```
~/Movies/subtitles/
  dQw4w9WgXcY_NeverGonnaGiveYouUp/
    meta.json
    NeverGonnaGiveYouUp.en.srt          ← YouTube manual captions
    NeverGonnaGiveYouUp.en.auto.srt     ← YouTube auto-generated captions
    NeverGonnaGiveYouUp.zh-TW.srt       ← translated
```

### Claude Code Skill

After running `install.sh`, the skill is available in [Claude Code](https://claude.ai/code). Just paste a YouTube URL:

```
youtube-sub https://www.youtube.com/watch?v=VIDEO_ID
youtube-sub https://www.youtube.com/watch?v=VIDEO_ID --lang en --to zh-TW
youtube-sub https://www.youtube.com/watch?v=VIDEO_ID --lang en --to zh-TW --translator claude
```

Claude handles the full pipeline and reports output file locations when done.

---

## Commands

### `run` — full pipeline

```
youtube-sub run <URL> [--lang ja] [--model large-v3-turbo] [--to zh-TW] [--translator google]
```

Downloads audio, gets subtitles (YouTube captions first, Whisper as fallback), and translates.

| Option | Default | Description |
|--------|---------|-------------|
| `--lang` / `-l` | `ja` | Video language (Whisper code) |
| `--model` / `-m` | `large-v3-turbo` | Whisper model (skipped when YouTube captions exist) |
| `--to` / `-t` | `zh-TW` | Translation target language |
| `--translator` | `google` | `google`, `claude`, or `gemini` |

### `download` — download only

```
youtube-sub download <URL> [--lang ja] [--to zh-TW]
```

Creates the work directory, downloads audio, and fetches YouTube captions if available. Does not transcribe.

### `transcribe` — Whisper transcription

```
youtube-sub transcribe <work-dir> [--lang ja] [--model large-v3-turbo]
```

Runs Whisper on the downloaded audio. Audio file is deleted after transcription.

### `translate` — translate subtitles

```
youtube-sub translate <work-dir> [--to zh-TW] [--translator google]
```

Reads `.<lang>.srt` from the work directory and outputs `.<to>.srt`.

### `resume` — continue interrupted work

```
youtube-sub resume
```

Scans subdirectories in the current directory for unfinished jobs and continues them.

### `warmup` — pre-download Whisper model

```
youtube-sub warmup [--model large-v3-turbo]
```

### `langs` — list language codes

```
youtube-sub langs
```

> **Note:** `--lang` uses Whisper codes (e.g. `zh`), `--to` uses Google Translate codes (e.g. `zh-TW`).

---

## Work Directory

Each video gets its own subdirectory:

```
<video_id>_<title-slug>/
  meta.json                     ← pipeline config and step state
  audio.m4a                     ← temporary, deleted after transcription
  <title>.<lang>.srt            ← YouTube manual captions or Whisper output
  <title>.<lang>.auto.srt       ← YouTube auto-generated captions (if available)
  <title>.<to>.srt              ← translated output
```

`meta.json` tracks step state (`pending` / `done`), so interrupted jobs can be resumed with `resume`.

---

## Whisper Models

| Model | Speed | Accuracy | Size |
|-------|-------|----------|------|
| `tiny` | fastest | lower | ~75MB |
| `small` | fast | moderate | ~250MB |
| `large-v3-turbo` | medium (default) | high | ~1.5GB |
| `large-v3` | slow | highest | ~3GB |

Cache location: `~/.cache/huggingface/hub/`

---

## Architecture

```
youtube_sub/
  main.py          CLI entry point (typer commands)
  downloader.py    yt-dlp wrapper: audio download, YouTube caption fetch
  transcriber.py   mlx-whisper wrapper: speech-to-text
  translator.py    translation backends: Google, Claude, Gemini
  srt.py           subtitle segmentation and SRT output
  srt_parser.py    read/modify existing SRT files
  workspace.py     WorkDir: work directory and meta.json management
```
