# 任務清單

狀態：`pending` 尚未開始、`in_progress` 執行中、`blocked` 有明確阻礙、`done` 已驗證完成、`skipped` 經確認不適用。

先完成相依任務才可開始；選擇性任務若被排除，應記錄原因後標為 `skipped`。文件任務完成不代表遊戲已能執行。

| ID | 任務 | 狀態 | 前置任務 | 完成條件 |
|---|---|---|---|---|
| T00 | 建立規劃與共用 AI skills | done | - | 規格、計畫、任務、架構基線及 `.agents/` 指引齊備；完成文件檢查 |
| T01 | 確認上游版本與匯入方式 | done | T00 | 使用者確認 tag／完整 commit、匯入位置與版本管理安排 |
| T02 | 匯入上游原始碼 | done | T01 | 保留現有文件及上游授權；記錄來源、版本和匯入方式 |
| T03 | 準備可重現建置環境 | done | T02 | Unity 6.6 匯入、編譯、針對性 EditMode 與 Windows 建置已完成，命令及結果已記錄 |
| T03C | 升級 Companion 至 Unity 6.6／URP | done | T02 | 獨立 URP 資產與六個品質設定通過檢查；Editor 編譯、5 個 EditMode、1 個隔離渲染 PlayMode 與 Windows smoke build 通過；手機限制另列 |
| T03L | 新增共用繁體中文 | done | T03, T03C | 783 項完整翻譯；兩端選單、格式／字形與設定序列化測試通過，Windows 已建置並實際顯示繁體主畫面；Companion 重啟限制另列 |
| T03F | 修正中文設定頁缺字 | done | T03L | 10 個字型容量測試修前失敗、修後通過；主遊戲 30／Companion 24 項通過，Windows 設定與錄音頁及多次切換截圖驗證 |
| T03Z | 修正下載歌曲 ZIP 匯入 | done | T03 | 10 個 PlayMode 案例通過、Windows 重建成功；原生 UI 匯入官方 301 MB 包，217 個檔案逐一 SHA-256 相符並登記歌庫路徑；獨立 test runner 限制另列 |
| T03M | 提供獨立 MP3／MP4 直接網址下載工具 | done | - | Python 標準函式庫 CLI、中文使用文件及 README 入口完成，17 項本機測試通過；不處理 YouTube、轉檔或 Unity 整合 |
| T03Y | 加入獨立工具的 YouTube 支援 | done | T03M | 30 項測試通過，含真實本機 yt-dlp／FFmpeg 的三種模式；公開授權 YouTube 影片實際轉出 MP3 並以 ffprobe 驗證，未下載商業 MV |
| T03S | 修正繁中選歌預設為空清單 | done | T03L | 四語 PlayMode 4 項通過，Windows 重建成功；隔離繁中設定實際顯示本機歌曲卡片，清單為「所有歌曲」，離開再進入仍可見；既有選單測試逾時另列 |
| T03A | 本機製作三首中文譜面初稿 | done | - | 使用者提供歌詞並核准本機模型；三份 AI 初稿已加入私人歌庫，9 項工具檢查及 3 項實際遊戲解析檢查通過；不代表精修音高／同步或完整演唱驗收 |
| T04 | 驗證未翻新遊戲流程 | blocked | T03 | 核心 PlayMode 測試等待 SingScene 逾時；需排除並在 player 完成選歌、收音、演唱、結算 |
| T05 | 核對實際架構並更新 skills | pending | T04 | 確認 UI、音訊、評分、資料與連線邊界；研究假設與本機事實分開記錄 |
| T06 | 盤點畫面與相容需求 | pending | T04 | 列出頁面、既有操作、輸入裝置、資料、在地化與失敗情境 |
| T07 | 確認視覺與首版範圍 | pending | T06 | 使用者核准視覺草案、頁面順序、驗收硬體及手機是否納入 |
| T08 | 翻新共用樣式與控制項 | pending | T05, T07 | 先更新架構 skill；確認實際消費端，驗證主題、焦點、大小螢幕與回饋 |
| T09 | 翻新主畫面 | pending | T08 | 遵循核准設計；既有入口及輸入導覽仍可操作 |
| T10 | 翻新選歌流程 | pending | T09 | 保留現有選歌能力；驗證空歌庫、掃描狀態、錯誤歌曲及玩家選擇 |
| T11 | 翻新演唱畫面 | pending | T10 | 歌詞、音符與分數清晰；可重現輸入下評分及時間行為符合基線 |
| T12 | 翻新結算畫面 | pending | T11 | 成績呈現、保存、返回流程及重新啟動後資料均正確 |
| T13 | 翻新必要設定頁 | pending | T08 | 保留玩家、歌庫、收音與校正能力；驗證設定儲存和錯誤提示 |
| T14 | 驗證或擴充 Companion（選擇性） | pending | T03C, T10, T13 | 僅在 T07 納入時實作；先更新連線 skill，依確認用途驗證協定與斷線恢復 |
| T15 | 完成整體回歸 | pending | T12, T13, T14 | T14 完成或有理由地略過；針對性測試與 player 回歸通過，含離線、編輯器及相關資料相容 |
| T16 | 封裝 Windows 成品與交付文件 | pending | T15 | 成品在確認環境通過驗收；授權、啟動方法、限制及 skills 與交付一致 |

## 執行紀錄

### T03A

- 2026-10-24：使用者另行核准本機工具／模型下載，提供三份歌詞附件，要求替既有 MP3／MP4 產生 UltraStar TXT。這是一次性的私人歌庫處理，不是新增或宣稱遊戲內中文 AI 製譜功能已完成；沒有下載新商業影音、沒有上傳音訊／歌詞、沒有把私人譜面加入 repository。
- 在既有 ignored `.venv` 安裝 CPU Torch／TorchAudio 2.8.0、Transformers 4.57.1、librosa 0.11、OpenCC、pypinyin 及 torchcrepe；`pip check` 通過。使用 TorchAudio HDemucs 分離人聲、Chinese Wav2Vec2 CTC 音節機率對齊原歌詞、pYIN 偵測音高；周杰倫版本另用 full CREPE 核對音高。模型與分析程式僅留在本機 cache／session，不修改 Unity、評分或網路功能。
- 單字 ASR 在歌唱中常輸出同音異字，因此只在對齊時合併同音音節，不改使用者歌詞。〈聽見下雨的聲音〉的本機周杰倫 MV 重複了附件未再次列出的第二段主歌，已依影片把使用者原有文字重複排列；不是新增未提供的歌詞。第三首另記錄翹舌／鼻音對齊近似及人工核對的歌唱範圍。
- 三份成品為 **AI 初稿**：〈嘉賓〉537 音符（42 自由唱）、〈看著我的眼睛說〉452 音符（34 自由唱）、〈聽見下雨的聲音〉296 音符（88 自由唱）。第三首雖只有 1 個音符無可靠音高，但另有 87 個字時間對齊信心低，明確以不計分的自由唱保留，不以虛構音高或低信心定位冒充完成品；僅 208 音符計分，仍需較多人工校正。
- 每首資料夾新增中文歌手／歌名 TXT 及 `AI-chart-review.json`，逐項記錄低信心位置、音高變化、方法、來源 SHA-256 與限制。TXT 引用實際原媒體檔名；原影音、唯讀附件、其他歌曲及使用者設定未修改。
- 9 項本機工具測試通過，涵蓋字序、BPM 四分音符換算、無重疊、拒絕覆寫、缺音高自由唱、品質不足不發布、明確 review 模式不對低信心音符評分及過半不確定仍拒絕。初稿先通過原 gate 的兩首才發布；第三首因時間定位仍不足而採明確 partial-scoring review 模式，不宣稱原始自動品質檢查全部通過。
- 暫存 Editor fixture 以遊戲實際 `UltraStarSongParser` 讀取三份最終 TXT：**3 通過、0 失敗、0 略過**。驗證無 parser issues、中文名稱、媒體存在、537／452／296 音符、不同音高、正長度、不重疊與實際時間換算。命令為 `& $Unity -batchmode -projectPath '.\UltraStar Play' -runTests -testPlatform EditMode -testFilter LocalGeneratedChartValidation -testResults "$Evidence\three-chart-parser-results.xml" -logFile "$Evidence\three-chart-parser.log"`；暫存 fixture 驗證後已移至 session，沒有私人檔案路徑測試留在遊戲原始碼。
- 每首抽取 6 個對齊位置與本機 MV 字幕比較，已核對兩首張遠的段落，以及修正後周杰倫版本的主歌／副歌／重複段／結尾；這是段落抽查，不是逐字或聽歌驗收。原生 UI 自動檢查兩次因無法取得前景視窗而安全中止，未送輸入至其他視窗；測試 player 均已關閉，使用者正在執行的 player 未停止，設定檔 hash 不變。不得把解析測試說成已實際唱完或已看見三張歌曲卡片。
- 同日依使用者要求修正私人〈晴天〉譜面的大提琴間奏後尾段：先備份原 TXT，補回漏掉的 8 字，修復錯序、重疊及後續歌詞提早；只調整約 246.8–277.0 秒，前段逐位元組相同，原影音 SHA-256、BPM／GAP 與既有音高保持不變，缺句沿用前段副歌。以本機分離人聲及 23 個較可靠的對齊錨點校正原節奏，22 個誤差小於 100 ms，並抽查 6 處 MV 字幕；低信心單字不直接當作精確定位。6 項針對性檢查全部通過（原檔 5 項失敗），暫存 `LocalSunnyChartValidation` 經 Unity 6.6 實際 parser 驗證 1 通過、0 失敗；共 371 音符、尾段 50 音符，沒有時間倒退或重疊。暫存 fixture 移至 session，私人歌詞未加入 repository；未宣稱逐字人工聽歌或實唱驗收。

### T03S

- 2026-10-24：本機譜面原本引用不存在的 MP3 名稱，VIDEO 也不是實際影片檔；備份後只修 MP3／VIDEO 並補 COVER，三個引用均確認檔案存在。原繁中歌詞與全部音符、節拍、音高、GAP 不變；私人歌檔不納入 repository。
- 修正引用後，隔離成品仍空白；透過開發頁 Copy Log 取得當次記憶體紀錄，確認 `Found 1 songs`。根因為清單名稱排序令空的 `Favorites` 排在本地化「所有歌曲」之前，而預設、重設與 toggle-back 都依賴首項。已讓 `UltraStarAllSongsPlaylist` 固定首項，其餘仍按名稱排序，保留既有明確選取及 party-mode 分支。
- 新增 [四語清單測試](<../UltraStar Play/Assets/Tests/PlayModeTests/SongSelectLocalizedPlaylistTest.cs>) 與必需的 ProTrans 測試組件引用。修正前 **1 通過、3 失敗**，日文、簡中及繁中均實際讀到第一項 `Favorites`；修正後 **4 通過、0 失敗、0 略過**，涵蓋真實 chooser／dropdown、單首合成歌曲可見、手動選取、重設與 toggle-back。
- 最終命令：`& $Unity -batchmode -projectPath '.\UltraStar Play' -runTests -testPlatform PlayMode -testFilter 'SongSelectLocalizedPlaylistTest.*' -testResults "$Evidence\song-playlist-final-results.xml" -logFile "$Evidence\song-playlist-final.log"`：**4 通過**。
- 擴充合跑 `-testFilter 'SongSelectLocalizedPlaylistTest.*|SongSelectPlaylistTest'`：4 通過、1 失敗。既有 `SongSelectPlaylistTest.PlaylistShouldWork` 在第 73 行等待歌曲選單項目逾時；移除排序修正後單獨重跑仍於同處失敗（`song-playlist-existing-baseline-results.xml`），不是本次變更新增，未擴修既有選單問題。
- `& $Unity -batchmode -quit -projectPath '.\UltraStar Play' -buildTarget Win64 -executeMethod MainGameBuildTools.BuildWindows64 -logFile "$Evidence\song-playlist-windows-build.log"`：**Build Finished, Result: Success.**
- 用重建的正常 Windows 成品、靜音隔離繁中設定和使用者實際歌庫驗證：歌曲卡片及 cover 可見，篩選頁顯示「所有歌曲」，返回主畫面再進入仍可見。證據為 session 的 `song-load-selection-fixed.png`、`song-load-playlist-fixed.png`、`song-load-selection-revisited.png`。測試程序已正常關閉，使用者 Settings.json 前後 SHA-256 不變；沒有驗證實際演唱同步或評分。

### T03Y

- 2026-10-24：使用者另外要求支援 YouTube，與 T03M 最初選擇的直接網址模式分開追蹤。獨立工具加入 watch／短網址／shorts／live／embed 辨識與 `--format mp3|mp4|both`（預設 both），移除追蹤與播放清單參數，保留既有直接下載行為。
- 以 Python fact-grounded coding skill 核對現有程式與官方 yt-dlp／EJS 文件，新增 optional [依賴清單](../scripts/requirements-media.txt)，僅在 repository 的 `.venv` 安裝 yt-dlp 2026.10.21 及 EJS 0.8.0 等依賴。未改全域 Python 套件或 Pylance 選用的 Python 3.12；實際執行與測試為 `.venv` Python 3.11.9。
- 本機 FFmpeg／ffprobe 8.1.1 與既有 Scoop NVM 的 Node 24.19.0 已可用，沒有另裝或切換 Node、沒有修改永久環境變數。依賴缺漏、無效網址、下載／轉檔失敗及既有同名檔案均明確報錯。
- 使用獨立 staging，下載成功並確認輸出格式後才發布檔案，保留不覆寫與失敗清理；不載入使用者 yt-dlp 設定、plugins、瀏覽器 cookies，也不啟用遠端元件下載或 DRM／存取限制繞過。沒有整合 Unity、修改歌庫或產生譜面。
- `.\.venv\Scripts\python.exe -B -m unittest discover -s scripts -p "test_download*.py" -v`：**30 通過、0 失敗、0 略過**。保留原 17 案，新增三種輸出、網址路由、依賴／輸出錯誤、兩格式中第二筆失敗不發布第一筆，以及 ffprobe 驗證的真實本機 yt-dlp／FFmpeg 合併／轉檔。
- `.\.venv\Scripts\python.exe -B .\scripts\download_media.py --help` 成功。Pylance 兩份修改／新增 Python 檔語法檢查通過；diagnostics 無錯誤，只有 Windows 下非 Windows 分支與測試 callback 未使用參數的提示。
- 在線以 `--skip-download --dump-single-json` 解析 Blender 官方影片 `aqz-KE-bpKQ`，取得 61 種格式；核對官方 CC BY 3.0 授權後，以實際下載函式完成 MP3 下載／轉檔，產物 **19,229,136 bytes**，ffprobe 確認 mp3。署名：`(c) copyright 2008, Blender Foundation / www.bigbuckbunny.org`。測試影音僅放入自建暫存目錄並已自動清除，log 保存於 session 的 `youtube-cc-live-mp3.log`。
- 公開測試片 `BaW_jenozKc` 回報 unavailable；Blender 來源出現未知 iamf codec 警告，但 MP3 成功，沒有隱藏警告或繞過失敗來源。未下載使用者的商業 MV、未宣稱該支影片可下載；實際 YouTube MP4 下載未另跑，MP4 的轉檔／合併由本機合成影音驗證。中文使用文件及繁體 README 入口已同步。

### T03M

- 2026-10-24：使用者選擇支援 MP3／MP4 的 HTTP(S) 直接下載網址，以及同時下載兩種檔案；此工具獨立於 Unity，不以演唱驗收或建置為前置。
- 使用 Python fact-grounded coding skill，確認本機 Python 3.11.9；未安裝依賴、未修改遊戲或 Companion。新增 [下載工具](../scripts/download_media.py)、[測試](../scripts/test_download_media.py) 與 [中文文件](download-media.zh-TW.md)，繁體 README 提供入口。
- 支援多網址、重新導向、中文檔名及串流寫檔；不覆寫既有檔案，檢查媒體檔頭及已知長度，錯誤明確回報並以非零代碼結束，當筆失敗／取消時清理暫存檔。保留原始媒體位元組，不轉檔、不產生譜面，也不解析 YouTube 網頁或繞過存取限制。
- `python -B -m unittest discover -s scripts -p "test_download_media.py" -v`：17 通過、0 失敗。測試包含真正 CLI 子程序、兩種格式逐位元組比對、HTML／HTTP 錯誤、覆寫防護、逾時／取消及截斷清理；僅使用 loopback server 與自行產生的測試資料，沒有下載商業音樂或寫入使用者歌庫。
- `python -B .\scripts\download_media.py --help`：成功；Git whitespace 檢查通過。未以本次腳本測試宣稱媒體可播放或核心演唱驗收完成。

### T03F

- 2026-10-24：使用者回報設定與錄音頁部分中文字消失、看似排版跑掉。確認譯文仍完整，問題是共用 CJK fallback 的單張 1024x1024 動態 atlas 裝滿，而非版面寬度不足。
- 新增 `CjkFontAtlasTest`，以實際來源字型、取樣大小、padding、render mode、atlas 大小與 multi-atlas 設定建立暫存字型，載入繁體／簡體／日文所需且來源支援的字形。修正前 JP／KR／SC／TC 一般與粗體共 10 案全部失敗，每案有 745–964 個來源支援字形無法裝入。
- 對上述 10 個資產啟用多張 atlas 與建置時清除動態快取，未改 fallback 順序、字型尺寸、字型來源、UI 控制項寬度或音訊／評分邏輯；沒有用換字或縮字規避缺字。
- 修正後主遊戲 `CjkFontAtlasTest;TraditionalChineseTranslationTest;SettingsUtilsTest`：30 通過、0 失敗；Companion `CjkFontAtlasTest;TraditionalChineseTranslationTest;CompanionLanguageSettingsTest`：24 通過、0 失敗。每個容量案例確認全數字形裝入且真的使用超過一張 atlas；測試只修改暫存字型並釋放其材質／貼圖。
- Unity 建置清除動態資料時另外改寫了六個原先乾淨資產的既有 glyph／texture cache 與序列化欄位順序；已保留其原始資料，只留下每檔兩個設定值差異，避免夾帶大量無關的快取變更。成品仍為已驗證的清除快取後版本。
- 使用者同意正常關閉遊戲，另明確核准停止無視窗的 Unity 建置 PID 7652 及工作程序，才釋放主專案執行驗證。
- Windows 重建 `Build Finished, Result: Success.`。隔離設定啟動真正成品，進入遊戲設定、錄音設定與全域設定，並連續切換外觀／畫面／音效／網路攝影機／手機／模組頁後回到遊戲設定。
- 實際視窗截圖確認側欄「網路攝影機／手機應用程式／模組」與錄音頁「全域設定／音符／顏色／延遲／校正／音量門檻／取樣率／自動」完整可見；回訪頁面後仍正常。測試程序已關閉，沒有覆寫使用者設定。
- 原有部分 UI 硬編碼英文（如 Language／System Audio Backend Delay）未順手擴張修改；完整演唱與手機實機仍未驗證。專用 XML、log、視窗截圖保留於 session，不提交。

### T03L

- 2026-10-24：使用者核准新增遊戲繁體中文；先補架構 skill 與在地化責任邊界，再新增共享 `messages_zh_TW.properties` 與 Unity importer metadata，不覆寫簡體、不改預設語言。
- 英文預設目錄新增 `Chinese (Traditional) - 繁體中文` 選項；沿用既有 ProTrans 地區代碼探索、語言選單及 `CultureInfoName`。繁體 783 項與英文 key 完全一致、非空且無重複，placeholder、rich text、換行與 URL 均一致。
- 沿用既有 Noto Sans TC 動態 fallback，逐一驗證翻譯中使用的漢字在來源字型有字形；未下載新字型、修改 fallback 順序或寫入動態 atlas cache。
- 主遊戲 EditMode：20 通過、0 失敗（共用繁體測試 10、四語設定序列化 4、既有設定測試 6）。Companion EditMode：14 通過、0 失敗（同一共用測試 10、四語設定序列化 4）。原手動 TranslationTest 維持 Ignore。
- 初次 Companion 只發現 4 個專案內測試；兩個 manifest 加入 `testables: ["playsharedui"]` 後實際執行共用測試。主遊戲完整 Settings 的預設 party playlist 依賴執行中的歌庫，語言測試將此不相關欄位置空隔離，不改產品邏輯。
- 使用者明確允許停止原本占用主專案的 Unity 建置程序後，才執行桌機測試與重建。Windows build report 成功，建置清單列出繁體目錄，成品 `resources.assets` 也確認含繁體檔名與譯文。
- 以獨立 session 設定檔、靜音與本機測試連接埠啟動真正的 Windows EXE；視窗正常回應，主畫面「開始唱歌／隊伍與錦標賽／線上遊戲」繁體字形可見，離開後設定仍為 `zh-TW`。只擷取該遊戲視窗，結束自己啟動的程序，沒有覆寫使用者的設定檔。
- Companion 原有設定會保存語言字串，但啟動時未套用；重新啟動後需在語言選單重選。此既有問題未納入本次翻譯修改。沒有重建手機包或驗證觸控／配對；T04 演唱流程阻礙不因本次翻譯而解除。
- 可重現命令與結果見 [啟動指引](getting-started.md)；專用 XML、log 與視窗截圖保留於 session，不提交。

### T03C

- 2026-10-24：使用者明確選擇 Companion 一併升級 Unity 6.6 並遷移 URP。先更新架構與升級 skill，再修改；不擴張為 UI 翻新或協定重寫。
- 已盤點主場景、camera prefab、screen-space UI Toolkit panel、現有測試與建置入口。目前只安裝 Windows／WebGL 模組，Android／iOS 打包和實機驗證尚不可執行。
- 原有連線、收音、選歌 PlayMode 測試多數已標 Ignore（缺主遊戲）；不能將 ignored 測試記為通過。新增遷移專用測試，不改既有 Ignore。
- `.\build.ps1 RestoreCompanionAppDependencies` 成功：三個還原 target 均為 Succeeded，NuGet 建置零警告／錯誤；未安裝新 SDK。
- Editor 自動寫入 `6000.6.7f1`，URP `17.6.0`、Input System `1.20.1`、uGUI `2.6.0` 與 Test Framework `1.8.0` 等依賴由 Unity 解析；原 Git pins 不變。
- `CompanionAppBuildTools.ConfigureRenderPipeline` 使用 Unity API 建立自有 pipeline／forward renderer、加入 camera 的 URP data，六個品質等級均繼承 Graphics 預設。原色彩空間與 FPS 控制未更改，沒有修改收音或協定。
- 重複執行設定工具後，pipeline、renderer、camera prefab、Graphics／Quality 五個檔案 SHA-256 完全不變；最終只選取遷移測試的 EditMode 再跑仍為 5 通過、0 失敗。
- 修正兩份 Companion UXML 的逗號小數；5 個 pipeline／camera／UXML EditMode 測試通過。
- 隔離渲染 PlayMode：1 通過。初次因 batch-mode 不自動渲染 Game view 而觀察到 `currentPipeline == null`；改用官方 render request 實際繪製 camera 後通過，沒有延長等待或忽略錯誤。此測試不載入應用控制器、不讀寫 profile、不啟動連線／收音，僅檢查真實 UI 資產可掛接、layout 與 URP renderer。
- Windows smoke build 成功，無 C#／shader／UXML scalar 編譯錯誤；它不是手機版交付。還原共用插件後主遊戲格式／時間／主題回歸仍為 38 通過、1 個既有 Ignore、0 失敗。
- Companion 兩份 CI workflow 版本同步；未在遠端執行，沒有新增／切換 CI 平台。
- 已知非本次新引入問題：共用 `ApplicationUtils` 在 runtime initialization 讀取 Companion 不存在的 FFmpeg 支援副檔名檔，log 有既有 exception／fallback error。它發生於隔離測試開始前，不能因測試通過而宣稱整段啟動無錯；本次沒有壓制或擴張修改媒體處理。
- Android／iOS 打包、完整主場景、手機觸控／權限／收音、耗電與桌機配對仍未驗證，詳見 [啟動指引](getting-started.md)。

### T00

- 2026-10-24：建立桌機優先規格、計畫、任務及上游架構研究基線。
- 建立開發與架構 skills；根目錄 `AGENTS.md` 僅作為 `.agents/` 的發現入口。
- 文件檢查涵蓋必要檔案、skill frontmatter、相對連結與任務相依性。
- 尚未匯入原始碼、下載依賴、執行 Unity 或產生 EXE。

### T01

- 2026-10-24：使用者確認採用 commit `a4aaa0b31327062a92d12b5e4cab4d80777f2a3f`，匯入目前根目錄並保留上游歷史。
- 使用架構及開發 skills；透過 `git ls-remote` 核對當時 `master` 指向該 commit。
- 本步不改 UI、不安裝 Unity、不建立提交或推送。

### T02

- 2026-10-24：建立 `desktop-refresh` 分支，以 `upstream` remote 取得上游完整祖先歷史，checkout 使用者確認的 commit。
- 同日依使用者要求將分支更名為 `refactor/desktop-refresh`，並核對目前分支名稱；未建立提交或推送。
- 同日依使用者要求設定 `origin` 為 `https://github.com/JontCont/UltraStar-Play.git`，核對 fetch／push URL；保留官方 `upstream`，未推送或驗證遠端存取權限。
- 來源為 `https://github.com/UltraStar-Deluxe/Play.git`。無 `--depth` 截斷；使用 `blob:none` 部分複製，舊版檔案內容按需下載。
- 匯入 4,904 個上游追蹤檔案；`HEAD` 符合指定 commit、祖先提交數 2,696、`--is-shallow-repository` 為 `false`。
- checkout 前後比較原有 8 份文件的 SHA-256，確認匯入未覆寫任何一份；保留上游授權及程式碼。
- `git fsck --connectivity-only --no-dangling` 通過。後續 Git 工作樹檢查只允許上游 AI 指引入口變更及本專案規劃文件。
- 上游主遊戲 `AGENTS.md` 改為共用入口，原始內文移至 `.agents/references/` 作歷史參考；沒有修改遊戲程式或建置設定。
- 核對主遊戲 Unity 版本 `6000.5.6f1`、Nuke 建置專案目標 `net8.0` 及現有建置／測試 target。只讀取程式碼，未執行依賴還原、Unity 或建置腳本。
- T03 仍未開始；工具安裝狀態、授權、建置與實機結果尚未驗證。

### T03

- 2026-10-24：使用開發及架構 skills，開始環境盤點與主遊戲依賴還原。
- 已找到 `C:\Program Files\dotnet\dotnet.exe`，包含 SDK `8.0.426` 與 .NET runtime `8.0.32`。
- `.\build.ps1 RestoreMainGameDependencies`：成功，兩個還原 target 均為 `Succeeded`；Nuke 及 NuGet 專案建置為零警告、零錯誤。這不是 Unity 遊戲編譯結果。
- 腳本實際選用已安裝的 SDK `11.0.100-rc.2.26504.105`，Nuke 以 .NET 8 runtime 執行；未安裝、升級或切換系統工具。
- 已檢查 LeanTween、UniRx、CSharpSynthForUnity、UnityStandaloneFileBrowser 及兩處 NuGet 插件目錄非空，並檢查代表性 DLL 與 `VERSION.txt`。還原後 Git 工作樹未新增遊戲程式變更。
- 未下載 AI 模型或額外 FFmpeg 函式庫；Unity Package Manager 仍須在首次開啟 Editor 時解析套件。
- 在命令、常見系統／使用者安裝目錄、Hub 設定位置及 Windows 安裝登錄資料中未找到 Unity；不排除自訂安裝位置，尚未驗證授權。
- 阻礙：需準備 Unity Editor `6000.5.6f1` 與適用授權，才能執行 Unity 編譯、測試及 Windows player 建置。未自行安裝 Unity 或接受授權條款。
- 已建立 [開發版啟動指引](getting-started.md)，記錄 Hub 匯入目錄、主場景與待驗證命令。
- 後續更新：使用者安裝 Unity `6000.6.7f1` 並明確核准直接升級，不先執行 6.5；已核對執行檔版本。T03 恢復執行中。
- 已先建立 Unity 升級架構 skill，下一步執行首次匯入與相容性驗證。尚未宣稱 Unity 編譯、測試或 player 成功。
- 依使用者提醒核對渲染設定：主遊戲預設已指向 URP，各品質等級沒有覆寫；Companion 當時為 Built-In，後續另行核准並完成 T03C 的設定遷移。主遊戲材質、shader、粒子與背景特效的 URP 實際顯示仍需在後續畫面及 player 回歸中驗證。
- 已記錄官方 Built-In 支援至 Unity 6.7 LTS 完整生命週期的說明，避免把 deprecated 誤當立即移除；後續 Companion 升級需另行處理此風險。
- 6.6 首次編譯被 Editor-only Build Report Inspector `0.3.0-preview` 的 `BinaryFormatter` 診斷 `UAC0023` 阻擋；核對官方 registry 無新版且專案無程式引用後移除，未關閉診斷或修改 PackageCache。
- Editor 已將主遊戲版本遷移為 `6000.6.7f1`，並解析 URP `17.6.0`、Burst `2.0.0` 等對應依賴；保留必要的序列化資產與 XR 設定遷移。主遊戲 CI 版本同步，未宣稱遠端 CI 已執行。
- 在 28 份主遊戲／共用 UXML 中機械修正兩種逗號小數，排除 6.6 浮點解析錯誤，不更改版面設計或 Companion 自有版面。
- 最終匯入／編譯及 Windows64 建置成功。格式／時間／主題 EditMode：38 通過、1 個既有 Ignore、0 失敗；最後一次建置 log 未找到 UXML scalar conversion 或 shader error。
- 自動檢查第一次分別因舊版建置成功訊息及測試 root aggregate 狀態判讀過嚴而報錯；已核對實際 build report、產物及逐項測試結果，未重新命名或隱藏失敗測試。
- 精確命令與已知限制記錄於 [啟動指引](getting-started.md)。T03 已完成，完整演唱驗證由 T04 繼續追蹤。

### T03Z

- 2026-10-24：使用者回報官方歌曲包下載後無法安裝，錯誤為 `ZipFile.get_Count()` 不存在；已確認是編譯與 Windows 成品的同名 SharpZipLib API 衝突，不是 URL 或檔案權限。
- 已先更新架構 skill 與基線，再將歌曲 ZIP 匯入改用既有 BCL `ZipArchive`，不升級依賴、不修改 Unity 安裝／PackageCache，也不改 TAR 等其他消費端。
- 保留背景解壓、Windows 短路徑 staging、覆寫相同匯入檔但保留其他檔案，以及成功後才登記歌庫的順序；補齊父目錄、UTF-8、空資料夾、全部 entry 的進度與失敗清理，拒絕目的地外的 entry。
- `ArchiveExtractionTest`：10 個 PlayMode 案例全部通過、無略過，涵蓋中文／巢狀檔名、大小寫副檔名、進度、覆寫、路徑逸出及無效／遺失／不支援／空 ZIP；成功與失敗皆回到主執行緒。命令見 [啟動指引](getting-started.md)。
- `StandaloneWindows64` test runner 因既有其他 PlayMode 測試找不到 `VisualElementTestUtils` 而編譯失敗，未擴張修復無關測試，也未把此命令記為通過。
- 正常 Windows 建置的最終報告為 `Build Finished, Result: Success.`。以隔離設定啟動該 EXE，從歌庫下載 UI 經 loopback 匯入使用者已下載的官方 301,329,787-byte ZIP，沒有再次連外下載 300 MB。
- 實際解壓 217 個檔案，逐檔長度與 SHA-256 全部吻合；包含 85 個 `.txt`、37 個 MP3、13 個 OGG。完成後 UI 顯示新增資料夾，隔離設定的 `SongDirs` 已保存對應路徑；不是只由測試工具自行解壓。
- 證據保存在 session 的 `zip-import-playmode-results.xml`、`zip-import-windows-build.log`、`zip-import-native-results.json` 及 `zip-song-library-imported.png`。已正常關閉測試 player、停止 loopback helper，刪除精確的新建測試匯入目錄／ZIP 副本／隔離設定；原下載 ZIP 與使用者設定保留。
- 原生介面仍會提示自動新增資料夾與既有父歌庫重疊，這是原有歌庫註冊行為，不影響解壓成功，也未在本次順手改寫。完整演唱驗收不屬本次 ZIP 修復。

### T04

- 2026-10-24：執行現有 `CoreGameLoopTest` PlayMode 測試，使用測試設定、暫存歌曲與模擬麥克風，不以真實使用者歌庫作為測試資料。
- 初次及修正 UXML 後重試均失敗：`CoreGameLoopTest.cs:44` 等待 `SingScene` 超過 10 秒；目前僅確認載入選歌場景，不代表演唱與結算成功。
- 不加大 timeout、不忽略此測試，也不把失敗歸因為 URP 或 6.6；沒有 6.5 執行基線可供比較。
- 阻礙仍需排查選歌到演唱的輸入／啟動流程，並補上桌面 player 實際收音、影片同步、材質／特效、分數及成績儲存驗證。在此之前不開始 UI 翻新。

## 後續紀錄格式

每個開始執行的任務記錄：日期、範圍、使用的 skill、變更、驗證命令／人工步驟、實際結果，以及阻礙或核准事項。

`done` 必須有對應驗證；無法執行驗證時不得把預期結果寫成成功。
