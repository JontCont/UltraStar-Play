# 下載 MP3／MP4 與 YouTube 影片

[download_media.py](../scripts/download_media.py) 是獨立命令列工具，不修改遊戲，也不需啟動 Unity。使用 Python 3.10 以上；本機驗證版本為 3.11.9。

僅用於你擁有或已獲准下載的內容。直接 MP3／MP4 網址使用 Python 標準函式庫；YouTube 單一影片另使用 yt-dlp、FFmpeg 與 JavaScript runtime。不支援播放清單批次下載、登入驗證或繞過 DRM／付費／地區限制。

## YouTube：先準備環境

在 repository 根目錄開啟 PowerShell。建議使用隔離環境，避免改動系統 Python 套件；本工作區已建立 `.venv` 並安裝下列依賴，不必重複建立：

```powershell
# 第一次設定或重新 clone 時才需要執行
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\scripts\requirements-media.txt
```

此外需要：

- `ffmpeg`、`ffprobe` 都能從 PATH 執行；不是名為 ffmpeg 的 Python 套件。本機已安裝 FFmpeg／ffprobe 8.1.1，無須重裝。
- 支援的 JavaScript runtime：工具依序尋找 Deno、Node.js、Bun、QuickJS，實際支援版本依 [yt-dlp EJS 指引](https://github.com/yt-dlp/yt-dlp/wiki/EJS) 為準。
- 本機已驗證 Scoop 管理的 NVM for Windows／Node.js 24.19.0，沒有另裝 Node。Windows 若需要調整 Node 版本，使用既有 NVM 的 `nvm install <version>`、`nvm use <version>`，不要額外安裝 standalone Node 或改動永久環境變數。
- [requirements-media.txt](../scripts/requirements-media.txt) 的 `yt-dlp[default]` 包含 EJS 等依賴；本次驗證 yt-dlp 2026.10.21／yt-dlp-ejs 0.8.0。

## YouTube 使用方式

將網址換成你有權下載的 YouTube 影片。`VIDEO_ID` 僅為示意：

```powershell
# 同時輸出 MP3 音訊與 MP4 影片
.\.venv\Scripts\python.exe .\scripts\download_media.py "https://www.youtube.com/watch?v=VIDEO_ID" --format both -o "D:\KaraokeSongs\My Song"

# 只輸出 MP3
.\.venv\Scripts\python.exe .\scripts\download_media.py "https://www.youtube.com/watch?v=VIDEO_ID" --format mp3 -o "D:\KaraokeSongs\My Song"

# 只輸出 MP4
.\.venv\Scripts\python.exe .\scripts\download_media.py "https://youtu.be/VIDEO_ID" --format mp4 -o "D:\KaraokeSongs\My Song"
```

- `-o` 為必填；YouTube 的 `--format` 預設為 `both`。`watch`、`youtu.be`、`shorts`、`live`、`embed` 的單一影片網址會正規化，移除追蹤與播放清單參數，只處理該影片。
- 使用影片標題加影片 ID 作檔名，保留中文並清理不適合 Windows 的字元。
- MP3 下載音訊後透過 FFmpeg 轉成 MP3。MP4 優先選擇 H.264／AAC 的 MP4 串流並合併，不強制重新編碼；若來源沒有 H.264，可能保留其他 MP4 視訊編碼，遊戲相容性需另行確認。
- `both` 分別執行音訊與影片下載，可能重複傳輸音訊；兩者都產生且通過基本檔頭檢查後才發布輸出。下載／轉檔失敗會清理本次 staging，不將第一種格式當成整筆成功。
- 不覆寫既有檔案。同名會報錯；由於下載在獨立 staging 進行，可能下載完成後才發現目的地同名。
- 發布每個檔案時拒絕覆寫；兩個檔案的發布不是整組交易，磁碟錯誤或取消發生在發布階段時，可能保留已成功發布的一個檔案。
- 不讀取瀏覽器 cookies、不載入使用者 yt-dlp 設定／plugins，不啟用遠端 JS 元件下載或繞過存取限制。若影片被刪除、需登入、受限或 YouTube 拒絕請求，會保留 yt-dlp 的錯誤訊息，不保證每支影片都能下載。

### 常見錯誤

| 訊息 | 處理 |
|---|---|
| `YouTube support needs yt-dlp` | 使用 `.venv` 的 Python 執行；只在其他 Python 安裝套件並不會影響這個環境 |
| `needs FFmpeg and ffprobe` | 確認兩個執行檔都在目前終端的 PATH |
| `needs a JavaScript runtime` | 檢查 Deno／Node 等 runtime；Windows Node 依前述 NVM 方式管理 |
| `yt-dlp failed ...` | 閱讀上方原始錯誤。不能單憑此訊息判定被 YouTube 阻擋，也不要以 cookies／代理或 DRM 繞過作為預設處理 |

網站介面變動時，可在相同隔離環境更新並重試你有權下載的影片：

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade -r .\scripts\requirements-media.txt
```

## 直接 MP3／MP4 網址

原本的直接下載模式仍不需要第三方套件；將下方範例換成實際獲准下載的**檔案網址**：

```powershell
# 下載 MP3
python .\scripts\download_media.py "https://example.org/audio.mp3" -o "D:\KaraokeSongs\My Song"

# 同時下載 MP3 與 MP4：提供兩個實際檔案網址
python .\scripts\download_media.py "https://example.org/audio.mp3" "https://example.org/video.mp4" -o "D:\KaraokeSongs\My Song"

# 查看參數
python .\scripts\download_media.py --help
```

`example.org` 僅示範語法，不提供上述歌曲檔案。網址請加雙引號，避免 PowerShell 將 `&` 等字元當成指令。

若 `python` 指令無法執行，本機已驗證的直呼方式為：

```powershell
& 'C:\Users\jontc\AppData\Local\Programs\Python\Python311\python.exe' .\scripts\download_media.py --help
```

### 直接下載行為

- 一個直接網址對應一個檔案。支援 HTTP(S) 重新導向，以及沒有 `.mp3`／`.mp4` 副檔名、但實際回傳檔案的直接網址。
- 優先使用伺服器的 `Content-Disposition` 檔名，否則使用最終網址的檔名。清理不適合 Windows 的字元及路徑；副檔名依 MP3／MP4 檔頭決定。
- **直接網址不轉檔**：`--format` 只作用於 YouTube。直接 MP4 不會自動產生 MP3，要兩種檔案需各有一個網址，原始位元組不變。
- 檢查檔頭以拒絕 HTML／登入頁及不支援的格式，但不完整解碼檔案，不能保證來源媒體可播放或其編碼適用遊戲。
- 串流寫入 `.part` 暫存檔，下載完成後才發布正式檔案。若伺服器提供 `Content-Length`，會核對下載長度。
- 不覆寫任何既有同名檔案；同名會明確報錯。請改用其他輸出資料夾，或自行確認後重新命名既有檔案。
- HTTP、網路、檔案或格式錯誤會顯示 `ERROR`，繼續處理下一個網址；只要一筆失敗，結束代碼即為 `1`，全部成功為 `0`。
- 網路讀取逾時為 30 秒，不是整個下載限時。按 `Ctrl+C` 取消時會清理當筆暫存檔，保留已完成檔案，結束代碼為 `130`。強制結束程序／斷電仍可能留下 `.part`。
- 不會自動產生 UltraStar 譜面、下載歌詞、搜尋歌曲、修改遊戲設定或加入歌庫。

以上歌庫／譜面限制也適用 YouTube 模式。所有網址都應加雙引號，尤其是含 `&` 的 YouTube 網址。

## 下載後加入 UltraStar Play

1. 另備與音樂版本相符的 UltraStar `.txt` 譜面；普通歌詞／LRC 不能取代音高譜面。
2. 將譜面、音樂及選用影片放在同一首歌的資料夾。
3. 確認譜面中的 `#MP3:`，以及有影片時的 `#VIDEO:`，對應實際檔名；中文譜面使用 UTF-8。
4. 到 **設定 → 歌曲 → 新增歌曲資料夾** 選擇歌庫根目錄，啟用該路徑後離開設定頁重新掃描。已登記的資料夾內新增檔案後，可以重啟遊戲重新掃描。

取得 MP3／MP4 不代表已取得譜面、歌詞或分享授權；請確認來源的使用條件。

## 測試

從 repository 根目錄執行：

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s scripts -p "test_download*.py" -v
```

2026-10-24 原直接下載的 17 項測試保留；加入 YouTube 案例後共 **30 項通過、0 失敗、0 略過**，包含實際 yt-dlp／FFmpeg 整合，詳見 [任務清單](tasks.md) 的 T03Y。

直接下載回歸使用 loopback HTTP server 與自行產生的測試位元組。YouTube 整合測試則用 FFmpeg 產生一秒的測試圖／正弦波，從 loopback 提供，再以 yt-dlp 的離線資訊檔執行相同下載／轉檔／合併命令，透過 ffprobe 確認 MP3 編碼及 MP4 的 H.264／AAC。沒有依賴時，僅此 optional 整合測試會略過；不得將略過記成通過。

另外已在線解析公開 Blender 官方影片 `aqz-KE-bpKQ`，取得標題及 61 種格式；核對 [Blender 官方 CC BY 3.0 授權](https://peach.blender.org/about/) 後，再以相同 `download_youtube` 函式實際下載並轉出 19,229,136-byte MP3，ffprobe 確認 `codec_name=mp3`。測試輸出在自有暫存目錄完成並自動刪除，沒有放入使用者歌庫或 repository。測試來源署名：**(c) copyright 2008, Blender Foundation / www.bigbuckbunny.org，CC BY 3.0**。實際 YouTube MP4 下載未另外執行，MP4 合併與編碼檢查的證據來自前述本機合成影音。

原 downloader 測試影片 `BaW_jenozKc` 回報 unavailable；Blender 影片則有 `Unknown codec iamf.001.001.Opus` 警告，但可用音訊下載／轉 MP3 成功，警告未被隱藏。未下載使用者貼的周杰倫 MV，未驗證該影片可下載，也不代表已驗收音樂播放或完整演唱。
