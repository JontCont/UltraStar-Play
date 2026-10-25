# 歌詞搜尋、下載 MP3／MP4 與歌曲匯入

[ultrastar-song-import](../.agents/skills/ultrastar-song-import/SKILL.md) 以 **歌手、歌名、YouTube 網址** 為主要操作輸入：由 AI 使用 Playwright 找歌詞來源，再以 scripts 下載 MP3／MP4、分析中文歌詞並發布 UltraStar TXT 初稿。不修改 Unity 或評分，也不需啟動 Editor。

僅用於你擁有或已獲准下載、使用的內容。不讀瀏覽器 cookies，不支援登入驗證或繞過 DRM／付費／地區限制。直接下載只需 Python 3.10 以上；完整製譜使用既有 `.venv` Python 3.11.9。

## 一次準備

1. 在 skill 目錄複製 [.env.example](../.agents/skills/ultrastar-song-import/.env.example) 為 `.env`，設定已存在的 `ULTRASTAR_LIBRARY` 歌庫與 `ULTRASTAR_WORK_ROOT` 工作根目錄。兩者都放在 repository 外；`.env` 已被 Git 忽略。命令列設定優先於環境變數與 `.env`。
2. YouTube 下載需要 PATH 上的 FFmpeg／ffprobe 與 Node。Windows 的 Node 沿用 Scoop 管理的 NVM，不另裝獨立 runtime。
3. 只有環境缺少依賴時才安裝：

```powershell
# YouTube 下載（含本機 EJS，不允許 yt-dlp 臨時下載遠端元件）
.\.venv\Scripts\python.exe -m pip install -r .agents\skills\ultrastar-song-import\scripts\requirements-media.txt

# 完整製譜：人聲分離、中文對齊、音高分析
.\.venv\Scripts\python.exe -m pip install -r .agents\skills\ultrastar-song-import\scripts\requirements-ml.txt
```

模型首次使用可能下載至本機 cache，之後可重用；不會上傳影音或歌詞。

## Skill 操作：三個欄位

在對話中提供：

```text
歌手：……
歌名：……
YouTube：https://www.youtube.com/watch?v=……
```

skill 會使用 Playwright 搜尋並核對歌詞來源，**不是 Python script 自行呼叫 Playwright MCP**。只搜尋公開歌手／歌名，不上傳私人內容。已附歌詞時直接使用。

找得到歌詞不代表能自動重製全文。只有使用者提供、明確授權或公有領域的文字可保存為 `lyrics.txt`；一般受著作權保護的歌詞僅提供來源連結並請使用者供詞。官方網站本身不等於開放重製授權；登入、付費牆及驗證碼不會繞過。找不到可用歌詞或版本不符時停止，不能保證所有歌曲只靠三個欄位都完成。

可使用的歌詞以 UTF-8 放在 `<work>\lyrics.txt`，依 MV 的演唱順序排列，重複段也要列出。skill 另在工作目錄的 `lyrics-source.json` 記錄來源 URL、查閱日期、版本及使用依據，不把全文寫入 log／repository。普通歌詞、LRC 都不等於音高譜面。

## Scripts：YouTube 到歌庫

若 skill 已備妥工作目錄的 `lyrics.txt`，命令只需歌手、歌名、網址：

```powershell
.\.venv\Scripts\python.exe -B .\.agents\skills\ultrastar-song-import\scripts\song_import.py import `
  --artist "歌手" --title "歌名" --youtube "https://www.youtube.com/watch?v=實際影片ID"
```

也可指定已提供的歌詞檔與路徑：

```powershell
.\.venv\Scripts\python.exe -B .\.agents\skills\ultrastar-song-import\scripts\song_import.py import `
  --artist "歌手" --title "歌名" --youtube "https://youtu.be/實際影片ID" `
  --lyrics "D:\SongInput\lyrics.txt" --work "D:\SongWork\歌手-歌名" --library "D:\KaraokeSongs"
```

流程為：先驗證歌庫／目的地／歌詞 → 下載 MP3 與 MP4 → 記錄來源 → 分離人聲 → 中文對齊 → CREPE 音高 → render／check → 發布。下載檔名使用影片 ID，譜面的 `#MP3`／`#VIDEO` 自動引用實際檔名。

工作目錄保留 `lyrics.txt`、`media\<影片ID>.mp3`、`media\<影片ID>.mp4`、`download.json`、分析 cache、譜面及審查報告。歌庫的 `<歌手>-<歌名>` 收到譜面、MP3、MP4 與 `AI-chart-review.json`；原始歌詞 TXT 不複製到歌庫，以免被當作另一份譜面。

- 缺少有效歌詞、歌庫不存在或已有譜面時，在影音下載前報錯。
- 重試會驗證下載網址及 SHA-256，相符才重用媒體；換網址、改動下載檔案或更換歌詞需使用新工作目錄。
- 分析失敗不發布譜面，保留已完成工作。修正對齊選項後可加 `--force` 重算 ML；它不覆寫歌庫、不重新下載或忽略品質檢查。
- 完成品仍是 **AI 初稿**，需人工核對逐字同步、轉音及音高。品質不過會明確失敗，不以虛構音高湊出成功結果。
- 本機媒體流程保持可用：將 `--youtube` 換成 `--audio "D:\SongInput\song.mp3"`，並可加 `--video "D:\SongInput\song.mp4"`。`--audio` 與 `--youtube` 互斥。

### 只下載 YouTube MP3／MP4

```powershell
.\.venv\Scripts\python.exe -B .\.agents\skills\ultrastar-song-import\scripts\download_media.py `
  "https://www.youtube.com/watch?v=實際影片ID" -o "D:\SongInput"
```

- 支援單支 watch、youtu.be、shorts、live 或 embed 網址；去掉播放清單及追蹤參數，不下載整份清單。進行中的直播是否能取得，取決於來源，工具不保證即時錄製。
- yt-dlp 下載同一來源，FFmpeg 產生 H.264／AAC、yuv420p MP4，再從該影片音軌產生 MP3。已知解析度優先選至 1080p；不讀使用者 yt-dlp 設定或 plugins，不自動下載遠端 EJS。
- 兩檔均經 ffprobe 核對 codec、非空檔案與正長度後才發布，拒絕覆寫。第二筆發布失敗會回滾本次第一筆；不刪除既有或並行建立的檔案。
- 下載／轉檔失敗或取消會清理本次 staging；程序被強制終止或斷電仍可能留下暫存目錄。
- 這個下載命令本身不搜尋歌詞、不製譜、不修改遊戲設定。

## 直接 MP3／MP4 網址

將下方範例換成實際獲准下載的**檔案網址**：

```powershell
# 下載 MP3
python .\.agents\skills\ultrastar-song-import\scripts\download_media.py "https://example.org/audio.mp3" -o "D:\KaraokeSongs\My Song"

# 同時下載 MP3 與 MP4：提供兩個實際檔案網址
python .\.agents\skills\ultrastar-song-import\scripts\download_media.py "https://example.org/audio.mp3" "https://example.org/video.mp4" -o "D:\KaraokeSongs\My Song"

# 查看參數
python .\.agents\skills\ultrastar-song-import\scripts\download_media.py --help
```

`example.org` 僅示範語法，不提供上述歌曲檔案。網址請加雙引號，避免 PowerShell 將 `&` 等字元當成指令。

### 直接下載行為

- 一個直接網址對應一個檔案。支援 HTTP(S) 重新導向，以及沒有 `.mp3`／`.mp4` 副檔名、但實際回傳檔案的直接網址。
- 優先使用伺服器的 `Content-Disposition` 檔名，否則使用最終網址的檔名。清理不適合 Windows 的字元及路徑；副檔名依 MP3／MP4 檔頭決定。
- **直接網址不轉檔**：直接 MP4 不會自動產生 MP3，要兩種檔案需各有一個網址，原始位元組不變。
- 檢查檔頭以拒絕 HTML／登入頁及不支援的格式，但不完整解碼檔案，不能保證來源媒體可播放或其編碼適用遊戲。
- 串流寫入 `.part` 暫存檔，下載完成後才發布正式檔案。若伺服器提供 `Content-Length`，會核對下載長度。
- 不覆寫任何既有同名檔案；同名會明確報錯。請改用其他輸出資料夾，或自行確認後重新命名既有檔案。
- HTTP、網路、檔案或格式錯誤會顯示 `ERROR`，繼續處理下一個網址；只要一筆失敗，結束代碼即為 `1`，全部成功為 `0`。
- 網路讀取逾時為 30 秒，不是整個下載限時。按 `Ctrl+C` 取消時會清理當筆暫存檔，保留已完成檔案，結束代碼為 `130`。強制結束程序／斷電仍可能留下 `.part`。
- 直接下載模式不轉檔、不產生譜面、不下載歌詞，也不修改遊戲設定或加入歌庫。

## 下載後加入 UltraStar Play

1. 另備與音樂版本相符的 UltraStar `.txt` 譜面；普通歌詞／LRC 不能取代音高譜面。
2. 將譜面、音樂及選用影片放在同一首歌的資料夾。
3. 確認譜面中的 `#MP3:`，以及有影片時的 `#VIDEO:`，對應實際檔名；中文譜面使用 UTF-8。
4. 到 **設定 → 歌曲 → 新增歌曲資料夾** 選擇歌庫根目錄，啟用該路徑後離開設定頁重新掃描。已登記的資料夾內新增檔案後，可以重啟遊戲重新掃描。

取得 MP3／MP4 不代表已取得譜面、歌詞或分享授權；請確認來源的使用條件。

## 測試

從 repository 根目錄執行：

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s .agents\skills\ultrastar-song-import\scripts -p "test_*.py" -v
```

2026-10-25 執行結果：**110 項通過、0 失敗、0 略過**，包括直接下載回歸、URL 正規化、下載／轉檔失敗、非覆寫、來源 cache、歌詞前置檢查與品質 gate。實際 yt-dlp／FFmpeg／ffprobe 透過 loopback 合成影音驗證兩種輸出；完整匯入測試使用替身 ML，不代表真實歌曲的分析品質。

測試未下載真實 YouTube 歌曲、未寫入使用者歌庫，也未重跑 Unity 或驗收實唱。只有合成影音整合案例需要 YouTube 下載依賴；缺少時會明確略過。Playwright 已以公有領域作品的搜尋頁確認可操作，但尚未拿指定歌曲測試完整來源核對流程。詳見 [任務清單](tasks.md)。
