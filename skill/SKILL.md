---
name: youtube-sub
description: 下載 YouTube 影片、用 Whisper 轉字幕、翻譯成目標語言。當使用者貼上 YouTube URL 並想要字幕、翻譯、或影片文字時觸發。也適用於「幫我下載字幕」、「翻譯這部影片」、「轉成中文字幕」等請求。Args: [url] [--lang ja] [--to zh-TW] [--translator google|claude]
---

# youtube-sub

執行完整 pipeline：下載影片 + 音訊 → Whisper 轉字幕 → 翻譯。

## 專案資訊

- 路徑：`/Users/enid/Documents/vibe/youtube-sub`
- 執行方式：`cd /Users/enid/Documents/vibe/youtube-sub && uv run youtube-sub <指令> [選項]`
- 輸出目錄：優先使用 `$YOUTUBE_SUB_WORK_DIR`，未設定則用當前目錄

## 參數

| 選項 | 預設 | 說明 |
|------|------|------|
| `--lang` | `ja` | 影片語言（Whisper 代碼，如 ja/zh/en/ko） |
| `--to` | `zh-TW` | 翻譯目標語言（如 zh-TW/en/ja） |
| `--translator` | `google` | `google`（免費）或 `claude`（用當前 session 翻譯，不需 API key） |
| `--work-dir` | 環境變數 | 覆蓋輸出目錄 |

## 執行流程

### 步驟 1：解析參數

從 args 或使用者訊息中取得 YouTube URL，清除 backslash：`url.replace('\\', '')`

從 URL 取出 video_id（`?v=` 後面的值，或 youtu.be/ 後面的值）。

### 步驟 2：判斷翻譯模式

#### `--translator google`（預設）

一行搞定：

```bash
cd /Users/enid/Documents/vibe/youtube-sub && uv run youtube-sub run "<url>" --lang <lang> --to <to> --translator google
```

加上 `--work-dir <path>` 若有指定。完成後告知產出檔案位置。

---

#### `--translator claude`（in-session 翻譯，不需 API key）

分三段執行：

**2a. 下載影片 + 音訊**

```bash
cd /Users/enid/Documents/vibe/youtube-sub && uv run youtube-sub download "<url>" --lang <lang> --to <to>
```

**2b. 轉錄音訊 → SRT**

```bash
# 從 $YOUTUBE_SUB_WORK_DIR 或 ~/Documents/vibe/youtube-sub 找工作目錄
BASE_DIR="${YOUTUBE_SUB_WORK_DIR:-/Users/enid/Documents/vibe/youtube-sub}"
WORK_DIR=$(ls -d "$BASE_DIR"/<video_id>_* 2>/dev/null | head -1)

cd /Users/enid/Documents/vibe/youtube-sub && uv run youtube-sub transcribe "$WORK_DIR" --lang <lang>
```

**2c. In-session 翻譯（每 200 段一批，/compact 後繼續）**

> 每次只翻譯 200 段，翻完寫檔、更新進度，然後停下來等使用者 /compact 再繼續。
> 這樣可以避免 context 爆炸，每批都從乾淨的狀態開始。

**第一步：確認進度**

```bash
cat "$WORK_DIR/meta.json"
```

讀取 `translate_progress` 欄位（不存在則視為 0）。設 `start = translate_progress`。
stem = 工作目錄名去掉 `<video_id>_` 前綴。

**第二步：讀取來源 SRT 並取出本批段落**

用 Read 工具讀取 `$WORK_DIR/<stem>.<lang>.srt`，解析所有段落（每個 block：index、時間軸、文字）。

取出第 `start+1` 到 `start+200` 段（若剩餘不足 200 段就取到結尾）。
設 `end = start + 本批實際段數`，`total = 總段數`。

**第三步：翻譯本批**

- **只翻譯文字行，時間軸一字不動**
- 目標語言 `<to>`（預設 zh-TW = 台灣繁體中文），字幕口語化、保留語感
- 計算批次編號：`batch_num = start // 200 + 1`，格式化為三位數（如 `001`）

**第四步：寫出分批檔案**

用 Write 工具寫出 `$WORK_DIR/<stem>.<to>.part<NNN>.srt`（`NNN` = 批次編號三位數）。
- 內容為本批翻譯結果，完整 SRT 格式
- index 沿用原始段落編號（第 `start+1` 段的 index 不變）
- 若檔案已存在（前次中斷），先用 Read 讀取任意 1 行，再用 Write 覆蓋

**第五步：更新 meta.json 進度**

用 Edit 工具更新 `meta.json`，將 `translate_progress` 設為 `end`。
（若欄位不存在，加在 `steps` 物件外層）

**第六步：判斷是否全部完成**

- **還有剩餘**（`end < total`）：
  回報：
  ```
  第 <batch_num> 批完成（段落 <start+1>–<end>，共 <end>/<total> 段）
  請執行 /compact，完成後再呼叫 youtube-sub 繼續翻譯下一批。
  ```
  **到此停止，等使用者 /compact 後重新呼叫。**

- **全部完成**（`end >= total`）：
  組合所有分批檔案並清理：
  ```bash
  cat "$WORK_DIR"/<stem>.<to>.part*.srt > "$WORK_DIR"/<stem>.<to>.srt
  rm "$WORK_DIR"/<stem>.<to>.part*.srt
  ```
  更新 `meta.json`：`steps.translate = "done"`，移除 `translate_progress` 欄位。
  回報完成，列出產出檔案。

**Resume 偵測**：若使用者說「繼續翻譯」或重新呼叫 skill，直接從第一步讀取進度繼續，不需重新下載或轉錄。

**SRT 格式範例**（保持不變）：
```
1
00:00:01,000 --> 00:00:03,500
こんにちは

2
00:00:03,800 --> 00:00:05,200
ありがとうございます
```

翻譯後：
```
1
00:00:01,000 --> 00:00:03,500
你好

2
00:00:03,800 --> 00:00:05,200
謝謝
```

## 完成後回報

告知：
- 工作目錄名稱
- 產出檔案：影片 .mp4、原文 .srt、翻譯 .srt
- 若有錯誤說明原因

## 注意事項

- URL 有 `\?` 或 `\=` 時自動去除 backslash
- Whisper 轉錄需要時間（~1.5GB 模型從磁碟載入約 30 秒）
- 查看語言代碼：`cd /Users/enid/Documents/vibe/youtube-sub && uv run youtube-sub langs`
