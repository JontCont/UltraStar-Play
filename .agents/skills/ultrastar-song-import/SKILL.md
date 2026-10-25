---
name: ultrastar-song-import
description: "Use when given a singer, song title and YouTube URL to find lyric sources with Playwright, download authorized MP3/MP4 media and import a draft chart, or when importing local media with supplied lyrics. 適用於歌詞搜尋、歌曲下載、歌詞轉譜與發布到本機歌庫。"
---

# 歌曲下載與匯入

## 輸入與邊界

- 操作輸入依序為 **歌手、歌名、YouTube 網址**。使用者已選擇由 skill 操作 Playwright 搜尋歌詞來源，再交給 scripts；不是要求 Python 自行操作 MCP。
- 若使用者已附歌詞，直接使用；否則依下節先搜尋來源。只有已提供、明確授權或公有領域的歌詞可存成全文，不憑歌手／歌名編造歌詞。
- 歌詞為 UTF-8 檔案，以 `--lyrics` 指定，或預先放在該首工作目錄的 `lyrics.txt`。找不到可合法取得的全文時，回報來源連結並請使用者提供歌詞，不能宣稱三個欄位在所有情況都必然完成。
- 僅處理使用者擁有或已獲授權下載、轉寫的內容。不讀取瀏覽器 cookies、不繞過 DRM、付費、登入或地區限制，不自動下載播放清單。
- 私人影音、歌詞、模型 cache 與譜面保留在 repository 外。不得把私人檔案納入版本控制。
- 工具獨立於 Unity；不修改遊戲評分、設定或 Companion。製譜限中文，輸出是待校正的 AI 初稿，不保證逐字同步或音高正確。

## 流程

1. 讀取同目錄 `.env` 的歌庫與工作根目錄。命令列優先於環境變數與 `.env`；不得回顯設定內容。設定格式見 [.env.example](./.env.example)。
2. 先驗證歌庫存在、目的地沒有既有譜面，完成下節的歌詞取得及版本核對，再執行影音下載。
3. [下載工具](./scripts/download_media.py) 處理單支 YouTube 網址，以 yt-dlp 下載至獨立暫存目錄，再以 FFmpeg 產生同一版本的 MP3 與 H.264/AAC MP4；兩檔都驗證成功才發布，不覆寫既有檔案。
4. [匯入工具](./scripts/song_import.py) 的 `import` 串接下載、記錄來源、人聲分離、中文對齊、音高分析、render／check 與發布。下載來源與 SHA-256 記在工作目錄；重試僅重用網址相同且 hash 相符的下載。
5. 使用者歌詞保存在工作目錄的 `lyrics.txt`；歌庫收到譜面、MP3、MP4 與 `AI-chart-review.json`。不要把普通歌詞 TXT 放到歌庫根層，避免被當作另一份譜面。
6. 品質檢查不過時停止，不發布假成功結果；保留工作輸出供修正及重跑。不得為通過檢查而捏造音高或放寬 gate。
7. 原本 `--audio`／`--video` 的本機流程與直接媒體網址下載保持可用。

## Playwright 歌詞來源搜尋

1. 載入可用的 Playwright／瀏覽器工具。以「歌手 歌名 歌詞」搜尋，優先核對官方藝人、唱片公司或明確標示授權的來源；不要將私人歌詞、媒體或設定上傳搜尋引擎。
2. 開啟實際結果，核對歌手、歌名、演唱者及版本，不只採信搜尋摘要。搜尋只用來定位來源，不代表允許複製歌詞全文；官方發布也不自動代表授權重製。
3. 全文使用需有可確認的公有領域／授權依據，或由使用者提供。遇到一般受著作權保護的歌詞，僅回報來源連結並索取使用者歌詞，不自動抓取全文；遇到登入、付費牆、驗證碼或 robots 限制即停止，不繞過限制。
4. 對可使用的歌詞，以 UTF-8 存成 repository 外工作目錄的 `lyrics.txt`，依實際 MV 排列重複段，去掉頁面導覽、廣告、歌名與作者等非演唱內容。不得新增未提供／未獲授權的句子。只調整使用者已有文字的重複順序時，說明調整原因。
5. 在工作目錄 `lyrics-source.json` 記錄來源 URL、查閱日期、歌手／歌名／版本與使用依據；不把歌詞全文寫入 log、報告或 repository。來源或版本不明確時詢問使用者，不選一份看似相近的歌詞繼續。
6. 再執行 `song_import.py import --artist ... --title ... --youtube ...`。瀏覽器搜尋由 skill 負責；Python CLI 僅讀 `lyrics.txt` 或 `--lyrics`，不內建歌詞網站爬蟲，也不自動轉用 ASR／字幕補詞。

## 執行與驗證

命令、依賴安裝及輸出說明以 [使用文件](../../../spec/download-media.zh-TW.md) 為準。先用現有 `.venv`，只有依賴清單變更或缺依賴時才安裝；Windows 的 Node 使用既有 Scoop NVM，不另裝 runtime。

從 repository 根目錄執行：

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s .agents\skills\ultrastar-song-import\scripts -p "test_*.py" -v
```

驗證需涵蓋直接下載回歸、YouTube URL 正規化、兩種輸出、不覆寫、失敗清理、重試及完整匯入的品質 gate。合成影音與替身 ML 的通過，不等於實際 YouTube 下載、真實歌曲製譜或遊戲實唱驗收；分別在 [任務清單](../../../spec/tasks.md) 記錄未驗證項目。
