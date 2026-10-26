# 架構研究基線

## 證據狀態

- 研究日期：2026-10-24。
- 研究對象：[UltraStar-Deluxe/Play](https://github.com/UltraStar-Deluxe/Play) 公開主分支與發布說明。
- 查閱時主分支 commit：`a4aaa0b31327062a92d12b5e4cab4d80777f2a3f`，日期 2026-10-21。
- 最新列出的發布版為 [v1.7.1-beta1](https://github.com/UltraStar-Deluxe/Play/releases/tag/v1.7.1-beta1)，發布於 2026-09-16。
- 下列原始碼連結固定在研究 commit，避免後續主分支變動混淆研究結果。
- 使用者已確認並匯入上述 commit。本機後續通過 Unity 6.6 編譯、針對性 EditMode 與 Windows 建置；以下行為描述仍以研究為主，不等於實機演唱已驗證。

## 本機匯入紀錄

- 匯入日期：2026-10-24，位置為目前 workspace 根目錄。
- 工作分支：`refactor/desktop-refresh`；匯入起點為上述完整 commit，後續專案提交保留此祖先。
- 專案 remote：`origin`，URL 為 `https://github.com/JontCont/UltraStar-Play.git`；依使用者要求設定為 fetch／push 目的地，尚未驗證遠端存取權限。
- 官方來源 remote 保留為 `upstream`，URL 為 `https://github.com/UltraStar-Deluxe/Play.git`。未建立新提交或推送。
- 保留該 commit 的 2,696 筆祖先提交，不是 shallow clone。使用 `blob:none` 延後下載非當前版本所需的歷史檔案；查閱未快取的舊檔案時仍可能需要連網。
- 上游帶有 4,904 個追蹤檔案。初次 checkout 時程式碼與上游相同；當時唯一刻意修改的上游文件為主遊戲 AI 入口。後續引擎相容性變更另見下節。
- 原有 8 份規劃與 AI 指引在匯入前後 SHA-256 相同；後續狀態更新另行編輯。
- 上游主遊戲 AI 指引已改為轉向 `.agents/`，原始內文保留為 [歷史參考](../.agents/references/upstream-main-game-guidelines.md)，不作為第二套生效規範。
- 匯入時驗證了 Git 物件連通性及工作樹；後續 Nuke 依賴、Unity 匯入／編譯及 Windows 建置已通過，互動演唱仍未驗證。

## 上游主要邊界

### 已核准的 Companion 遷移

- 2026-10-24：使用者另行確認 Companion 也升級至 Unity `6000.6.7f1`，並由 Built-In 遷移 URP；不是只列入未來計畫。
- 修改前查證：Companion 沒有 URP 套件、Graphics 預設與六個品質等級均未指定 SRP。主場景使用無 target texture 的 UI Toolkit panel，`CommonSceneObjects` 只有一個正交 camera；沒有發現自有材質、shader 或 C# 渲染 callback。
- 核准方案：由 Unity API 建立 Companion 自有輕量 forward renderer／URP asset，設定 Graphics 預設並驗證每個品質等級；不直接套用桌機渲染資產、不新增後處理、陰影、depth／opaque texture 成本，保留原色彩空間、UI、FPS、收音與協定。
- 使用現有 Nuke target 還原缺少的 Companion 依賴；該 target 也會重建主遊戲／共用 NuGet 插件，需關閉兩個 Editor。
- 已由 Unity API 產生專屬 [pipeline](<../UltraStar Play Companion/Assets/RenderPipeline/CompanionRenderPipeline.asset>)、[renderer](<../UltraStar Play Companion/Assets/RenderPipeline/CompanionRenderer.asset>)、global settings／volume profile，並保存 camera 的 URP data。六個品質等級均繼承此預設 pipeline；desktop 資產未被借用。
- Editor 匯入／編譯、5 個渲染設定／UXML EditMode、1 個隔離渲染 PlayMode 與 Windows smoke build 通過。隔離測試只掛載真實 camera／panel／UXML，不載入完整主場景控制器、不操作使用者設定或連線。
- 目前沒有 Android／iOS 建置模組，手機打包、觸控、授權收音、耗電及主遊戲配對不可用 Editor 結果代替。共用 ApplicationUtils 啟動時仍有缺 FFmpeg 副檔名資料檔的既有錯誤，未在渲染遷移中順手修改。

| 元件 | 已觀察到的責任 | 翻新原則 |
|---|---|---|
| `UltraStar Play` | Unity 主遊戲；選歌、演唱、設定及編輯器 | 優先保留引擎，按場景修改呈現 |
| `UltraStar Play Companion` | 獨立 Unity 手機專案；連線與手機收音等功能 | 非單機必要依賴；改動需確認相容性 |
| `Packages/playshared` | 兩專案共用的資料、歌曲格式、音高與通訊程式 | 變更前確認全部呼叫端 |
| `Packages/playsharedui` | 共用 UI 元件與樣式 | 檢查主遊戲及 Companion 的實際使用範圍 |
| `NukeBuild` | 依賴還原與建置工作 | 用選定 checkout 的命令，不自行重建工具鏈 |

以上路徑均相對於本機 repository 根目錄；已匯入，但模組行為與相依關係仍須後續追查及測試。

## UI 層

- 使用 Unity UI Toolkit：UXML 定義結構、USS 定義樣式，C# 處理互動。
- 主畫面、選歌與演唱場景有各自的 UI 資產；共用 UI 有大小螢幕樣式。
- 具備主題機制，不能只改單一顏色而忽略其他主題、焦點或在地化。
- 2026 年整合說明記錄自訂元件遷移到 `[UxmlElement]` 與 `[UxmlAttribute]`。
- 這不是瀏覽器 DOM；不能直接當成 HTML/CSS 網站部署。

來源：[主畫面 UXML](https://github.com/UltraStar-Deluxe/Play/blob/a4aaa0b31327062a92d12b5e4cab4d80777f2a3f/UltraStar%20Play/Assets/Scenes/Main/MainSceneUi.uxml)、[共用 UI](https://github.com/UltraStar-Deluxe/Play/tree/a4aaa0b31327062a92d12b5e4cab4d80777f2a3f/UltraStar%20Play/Packages/playsharedui)、[整合說明](https://github.com/UltraStar-Deluxe/Play/pull/585)。

## 演唱與評分

### 離線譜面初稿與正式演唱的界線

- 2026-10-24 使用者核准一次性私人歌庫製譜，提供歌詞並允許下載 CPU 模型；分析在既有隔離 Python 環境進行，不新增 Unity 製譜功能、不改評分規則、不上傳媒體或收錄歌詞。
- HDemucs 人聲分離、中文 CTC 音節對齊及 pYIN／CREPE 音高只能產生待校正初稿。保留原字序，版本重複段只能重新排列使用者已提供的文字；未測得可靠音高，或明確 review 模式中時間對齊不足的音符，以現有格式的自由唱標示，不假裝它們是可靠評分音符。
- 三份私人初稿已通過 9 項工具檢查與 3 項實際 Unity parser 檢查；第三首只有約七成音符計分。段落字幕抽查不能取代逐字同步／音高、轉音、實唱與評分驗收；原生 UI 檢查因前景視窗限制中止，未宣稱 runtime 唱歌通過。詳見任務 T03A。
- 2026-10-25：[歌曲匯入 skill](../.agents/skills/ultrastar-song-import/SKILL.md) 接受歌手、歌名及單支 YouTube 網址，由 AI 使用 Playwright 查找歌詞來源、核對版本及使用依據；只將已提供、授權或公有領域的文字存成工作目錄的歌詞，不抓未授權全文。Python CLI 本身不搜尋歌詞，讀取歌詞後下載 MP3／MP4、產生初稿並發布到 `.env` 指定的本機歌庫。原始歌詞 TXT 留在工作目錄，避免被遊戲當成另一份譜面。
- 下載為獨立依賴，直接媒體下載仍僅用標準函式庫；YouTube 使用 yt-dlp／既有 Node／FFmpeg，不讀 cookies、設定或 plugins，不繞過存取限制。來源 hash、兩檔驗證後才發布、不覆寫、缺詞及品質失敗先停止，均有工具測試；110 項本機測試通過，包括真實 yt-dlp／FFmpeg 的 loopback 合成影音。沒有下載真實 YouTube 歌曲，也未驗收指定歌曲的瀏覽器搜詞或實唱；不更動 Unity。

### 歌曲掃描與播放清單預設值

- 2026-10-24：使用者歌庫設定正確，但選歌頁空白。先修正本機譜面與實際 MP3／MP4 的檔名不符並補 cover，保留備份及所有音符／歌詞；該私人譜面不加入 repository。
- 隔離原生成品仍重現空白，而記憶體 log 明確顯示 `Found 1 songs`，確認不是完全未掃描。`SongSelectionPlaylistChooserControl.UpdateItems` 把含翻譯名稱的「所有歌曲」與其他清單一起按字母排序，空的 `Favorites` 便成為繁中預設；`Reset` 與 toggle-back 也依賴首項。
- 已修復：以 `UltraStarAllSongsPlaylist` 型別固定首項，再按名稱排序其餘清單。保留明確選取的清單與 party-mode 歌池，不更改掃描、譜面解析或評分規則。四語 PlayMode 回歸修前 1 通過／3 失敗、修後 4 通過，Windows 重建成功；隔離繁中成品確認歌曲卡片及 cover 可見，清單為「所有歌曲」，回訪仍正常。既有歌曲選單測試第 73 行逾時在修前與修後均可重現，未擴修；完整演唱仍未驗收。

### 歌曲 ZIP 匯入

- 2026-10-24：使用者回報下載官方 CC 歌曲包後出現 `Method not found: long ICSharpCode.SharpZipLib.Zip.ZipFile.get_Count()`。約 301 MB 的 ZIP 已存在本機，問題在解壓而非歌曲 URL 或下載權限。
- 查證主遊戲編譯引用 SharpZipLib 0.85／Sherpa 1.4，而 Windows 成品實際包含 Unity Mono 的 4.84；相同 assembly 名稱造成 API 不相容。修復只讓 ZIP 匯入改用既有 `System.IO.Compression.ZipArchive`，不新增依賴、不改 Unity 安裝或 PackageCache。
- 保留 `DownloadSongArchiveUiControl` 的錯誤顯示與成功後新增歌庫路徑、背景解壓和 Windows 短路徑 staging；補齊缺省父資料夾、完整進度與失敗清理，禁止 ZIP entry 寫出目的地。
- TAR、Android StreamingAssets 和建置壓縮仍維持現有程式，不因 ZIP 修復而宣稱已驗證；驗收包含合成案例、實際下載包與 Windows 成品，不只 Editor。
- 驗證已完成：10 個隔離 PlayMode 案例通過，正常 Windows 建置成功。以隔離設定及僅限 loopback 的暫存 HTTP helper，讓成品從原下載 UI 匯入既有官方 ZIP（301,329,787 bytes／258 entries）；217 個解壓檔案的長度及 SHA-256 全部符合原 ZIP，包含 85 個 `.txt`、50 個音訊檔案，成功回報後登記歌庫路徑。未覆寫使用者設定；測試副本與 helper 已清理，原 ZIP 保留。
- `StandaloneWindows64` 測試 runner 被既有 PlayMode 測試的 `VisualElementTestUtils` 編譯錯誤阻擋，未宣稱該 runner 通過；上述成品證據來自正常建置的原生遊戲，不是以 Editor 結果推論。完整演唱仍由 T04 追蹤。

### 繁體中文在地化

- 2026-10-24 使用者核准新增遊戲繁體中文，與先前 README 翻譯不同；保留英文、簡體中文、日文與其他語言，不改預設語言。
- 主遊戲與 Companion 共用 `playshared/Runtime/Resources/Translations`，ProTrans 以 `messages_zh_TW.properties` 對應 `zh-TW`。`LanguageChooserControl` 自動探索資源，語言名稱由英文預設檔的 `language_zh_tw` 提供。
- 沿用既有 `CultureInfoName` 設定與切換流程，不改評分、歌曲語言或 Companion 通訊。
- 現有 `UltraStarPlayTextSettings` 已包含 Noto Sans TC 動態字型 fallback；先驗證繁體字形覆蓋，不新增字型依賴或改全域字型順序。
- 新增整份繁體翻譯並檢查 key、placeholder、換行、rich text 與 URL 一致；以共用測試涵蓋兩個 Unity 專案，另外驗證設定序列化與 Windows 建置。現有手動 TranslationTest 不解除 Ignore。
- 已實作 783 個繁體項目與獨立共用測試 assembly，兩個 manifest 的 `testables` 明確啟用 `playsharedui` 測試。主遊戲 20 項與 Companion 14 項 EditMode 通過，包含選單、格式、字型與設定序列化；Windows 成品已打包繁體資源，隔離設定啟動的主畫面已實際顯示繁體。
- 後續使用者截圖發現設定頁缺字；來源字型覆蓋測試不等於 atlas 容量測試。JP、KR、SC、TC fallback 及其粗體原本限制為單張 1024x1024 動態 atlas；10 個暫存 FontAsset 容量案例重現失敗後，已啟用多張 atlas 與建置時清除動態快取，未更改字型順序或靠縮字隱藏。
- 缺字修復後主遊戲 30 項／Companion 24 項 EditMode 通過，Windows 重建成功；實際成品的設定與錄音頁中文字完整，多次切換其他設定頁再回訪也正常。這取代先前僅主畫面可見的有限視覺證據，不代表演唱或手機已驗證。
- Companion 原有啟動流程沒有套用已保存的 `CultureInfoName`，本次不順便修改其生命週期；重新啟動需重選語言。未宣稱手機打包、配對或演唱流程已驗證。

概念流程：

```text
本機麥克風取樣 / Companion 音高事件
  -> 音高與歌曲時間對應
  -> 依難度、校正與既有規則處理
  -> 比對譜面目標音符
  -> 音符及句子表現評估
  -> 計分與畫面更新
```

- 即時音高分析列出 Dywa、Camd。
- 標準評分上限為 10,000；音符部分為 9,000，句子獎勵最多 1,000；Golden Notes 採雙倍權重。
- 以上是程式設計基線，不代表已驗證所有模式或 Mods 均受相同限制。
- 介面翻新不得改變取樣、延遲、音高容錯、Joker 規則或評分事件順序。
- 確切時間換算、難度容錯及資料保存路徑須待匯入後追查與測試，不在此猜測。

來源：[PlayerMicPitchTracker](https://github.com/UltraStar-Deluxe/Play/blob/a4aaa0b31327062a92d12b5e4cab4d80777f2a3f/UltraStar%20Play/Assets/Scenes/Sing/Players/NoteRecording/PlayerMicPitchTracker.cs)、[PlayerPerformanceAssessmentControl](https://github.com/UltraStar-Deluxe/Play/blob/a4aaa0b31327062a92d12b5e4cab4d80777f2a3f/UltraStar%20Play/Assets/Scenes/Sing/Players/Score/PlayerPerformanceAssessmentControl.cs)、[PlayerScoreControl](https://github.com/UltraStar-Deluxe/Play/blob/a4aaa0b31327062a92d12b5e4cab4d80777f2a3f/UltraStar%20Play/Assets/Scenes/Sing/Players/Score/PlayerScoreControl.cs)。

## 歌曲與本機資料

- UltraStar TXT 記錄歌曲資訊、歌詞、音符音高與時間，音樂／圖片／影片為其他媒體檔案。
- 不是只有音樂檔就能得到可靠評分，仍需要正確譜面。
- 應沿用 parser、writer 與既有掃描機制，不因 UI 更新修改格式或編碼語義。
- 玩家、設定、成績的實際 schema、路徑、備份及遷移需求目前尚未核對。
- 舊 Wiki 可能與當前 parser 不一致，格式支援以選定版本的實作及測試為準。

來源：[歌曲 parser](https://github.com/UltraStar-Deluxe/Play/blob/a4aaa0b31327062a92d12b5e4cab4d80777f2a3f/UltraStar%20Play/Packages/playshared/Runtime/Songs/UltraStarSongFormat/UltraStarSongParser/UltraStarSongParser.cs)。

## Companion 與連線

- 主遊戲已有 HTTP endpoint 機制；它不是現成完整 Web 用戶端。
- 已查閱的手機收音流程在手機端分析後傳送拍點、音符及頻率事件。
- 不應因此宣稱現成支援手機人聲串流、低延遲擴音，或任何自訂手機網站。
- 若要改連線，先確認 discovery、傳輸方式、協定版本、時間同步與斷線處理，再建立或更新專用 skill。
- 本次不要求新增連線服務；本機唱歌不能被手機或伺服器可用性綁住。

來源：[HTTP server](https://github.com/UltraStar-Deluxe/Play/blob/a4aaa0b31327062a92d12b5e4cab4d80777f2a3f/UltraStar%20Play/Assets/Common/CompanionClientConnections/SimpleHttpServerForUnity/UltraStarPlayHttpServer.cs)、[手機收音事件傳送](https://github.com/UltraStar-Deluxe/Play/blob/a4aaa0b31327062a92d12b5e4cab4d80777f2a3f/UltraStar%20Play%20Companion/Assets/Common/Network/ClientSideMicDataSender.cs)。

## AI 工具與建置

### Windows 區網測試安裝檔

- 2026-10-26：使用者要求兩台 Windows 分別執行主遊戲及 Companion，並核准安裝 Inno Setup 編譯工具。這是測試封裝，不代表 T16 正式發行或 T04 演唱驗收完成。
- 封裝邊界：沿用 Unity Windows64 player；已以 `tools/windows-installer/Build-Installers.ps1` 呼叫 Inno Setup 6，建立各自獨立 AppId 的每使用者安裝檔，不要求管理員、不自動修改防火牆、不打包私人歌曲、設定、模型或 Unity 備份符號。兩端仍沿用既有 persistent data，不因安裝位置不同而另建 profile。
- Companion 增加與主遊戲相同的 Windows64 建置入口；安裝封裝補入共用媒體副檔名目錄及授權文字，不改網路或媒體處理邏輯。
- 原始碼確認：LiteNetLib discovery／連線使用 UDP，主遊戲預設 `34567`；Companion 可留空主機位址自動探索，或指定主遊戲的 IP。主遊戲 HTTP 預設 TCP `6789`，實際 port 由連線回覆提供；HTTP 權限仍沿用既有設定。
- 已驗證：兩份安裝檔編譯、隔離安裝，513／213 個來源 runtime 檔案逐一 SHA-256 相符，另驗證授權及 Companion 媒體目錄；安裝後雙端可回應、loopback 實際協定版本 7 握手／權限／MicProfile 交換與 HTTP hello 成功。重新安裝／解除安裝保留未知 marker，既有設定 hash 不變；測試程序與安裝目錄已清理。
- 兩端均觀察到 TextMeshPro 預設字型的啟動空參照錯誤，未阻止上述配對；不宣稱 log 無錯。兩台電腦的探索、防火牆、路由、控制及麥克風仍待實機測試，不能以 loopback 結果代替；步驟及命令見 [啟動指引](getting-started.md)。

- AI 製譜與即時演唱評分是不同流程。
- 2026 年整合使用 UVR、Parakeet、RMVPE 與 NeMo Forced Aligner 等工具。
- 模型與 FFmpeg 函式庫預設不隨建置下載；UI 翻新不得假定它們存在。
- 上游匯入時兩專案指定 Unity `6000.5.6f1`；本機主遊戲與 Companion 現均由 Editor 遷移到 `6000.6.7f1`。
- 本機 Nuke 建置專案目標為 `net8.0`，使用 `Nuke.Common` `9.0.4`。
- 已從 `NukeBuild/Build.cs` 核對 `RestoreMainGameDependencies`、`BuildMainGameWindows64`、`TestMainGame` target。
- 2026-10-24 已執行 `.\build.ps1 RestoreMainGameDependencies`，NuGet 與主遊戲外部插件還原成功；未啟用 AI 模型或額外 FFmpeg 函式庫下載。Unity 測試及 Windows 建置經直接 Editor 命令執行，未呼叫 Nuke 對應 target，詳細命令與結果見 [啟動指引](getting-started.md)。
- 上游兩專案 workflow 原先指定 `6000.1.3f1`；核准後兩專案的 build/test workflow 均同步到 `6000.6.7f1`。尚未執行遠端 CI，也未驗證手機平台。
- 根目錄 `build.ps1` 會建置 Nuke 專案，找不到 .NET 時還可能下載 SDK；不能將呼叫腳本的 `--help` 當作沒有副作用的環境探測。

來源：[依賴下載器](https://github.com/UltraStar-Deluxe/Play/blob/a4aaa0b31327062a92d12b5e4cab4d80777f2a3f/NukeBuild/MainGameDependencyDownloader.cs)、[Unity 版本](https://github.com/UltraStar-Deluxe/Play/blob/a4aaa0b31327062a92d12b5e4cab4d80777f2a3f/UltraStar%20Play/ProjectSettings/ProjectVersion.txt)。

## 已核准的 Unity 6.6 遷移

- 2026-10-24 使用者確認直接採用已安裝的 `6000.6.7f1`，不先安裝或執行 6.5。
- 已核對執行檔 `C:\Program Files\Unity\Hub\Editor\6000.6.7f1\Editor\Unity.exe` 的 ProductVersion 為 `6000.6.7f1_b22767f04f04`。
- 遷移前主遊戲仍指定 `6000.5.6f1`，沒有 Library 匯入快取，也沒有執行中的 Unity Editor。
- 此主遊戲階段只處理必要相容性，不混入 UI 翻新或評分變更；Companion 後續另行核准，證據與責任範圍分列於 Companion 段落。
- 由 Editor 進行序列化／API 遷移，先確認匯入與編譯，再執行可行的既有測試及 Windows 建置。
- 由於沒有 6.5 執行基線，任何錯誤都須區分「觀察到」與「證明由升級造成」，不得混為一談。
- 已通過匯入／編譯、針對性 EditMode 與 Windows 建置，但核心 PlayMode 仍失敗，不能視為完整相容性驗收。程序見 [Unity 升級 skill](../.agents/skills/ultrastar-play-unity-upgrade/SKILL.md)。
- 首次 6.6 匯入完成套件解析，但編譯被 `com.unity.build-report-inspector` `0.3.0-preview` 的 `BinaryFormatter` 用法阻擋（`UAC0023`）。官方 registry 沒有更新版本，專案 C#／asmdef 沒有引用此工具。
- 相容性處理：移除這個僅 Editor 使用的預覽版報告檢視工具，不關閉編譯診斷、不修改 PackageCache，也不更動遊戲資料序列化。這會移除工具提供的報告檢視選單；Unity 的 BuildReport API 與建置 log 仍保留。
- 移除後匯入及編譯成功；現有格式／時間／主題 EditMode 測試為 38 通過、1 個既有 Ignore、0 失敗，Windows64 建置也成功產生 EXE。
- 核心演唱 PlayMode 測試等待進入 SingScene 逾時；目前尚無證據能將其直接歸因為 6.6。另在匯入 log 觀察到 UXML 浮點屬性使用逗號小數（`0,135`、`0,1`）的解析錯誤，已統一主遊戲與共用版面為 invariant 小數格式後重試。
- 修正 28 份 UXML 後，最終 EditMode 仍為 38 通過、1 個既有 Ignore，Windows 建置成功且沒有該類 UXML 或 shader error；核心 PlayMode 重試仍停在等待 SingScene，繼續由 T04 追蹤。
- Unity 產生的字型／URP／sprite atlas 等序列化遷移保留；測試造成的 NetworkManager 日誌層級改動已還原為原值，不混入連線行為修改。

### 渲染管線與 Built-In 淘汰風險

- 使用者要求將 Built-In Render Pipeline 淘汰納入升級考量。官方文件標示從 Unity 6.5 起 deprecated，並承諾支援（含修正與維護）至 **Unity 6.7 LTS 完整生命週期**；不應解讀成在 6.7 發布時立即移除。
- 已核對主遊戲 [GraphicsSettings](<../UltraStar Play/ProjectSettings/GraphicsSettings.asset>) 的 `m_CustomRenderPipeline` GUID 為 `5b2dd8830449c234ba547ed27b4b214d`，對應 [URP asset metadata](<../UltraStar Play/Assets/RenderPipeline/UniversalRenderPipelineAsset.asset.meta>) 及 [URP asset](<../UltraStar Play/Assets/RenderPipeline/UniversalRenderPipelineAsset.asset>)。
- 主遊戲 [QualitySettings](<../UltraStar Play/ProjectSettings/QualitySettings.asset>) 各品質等級均未覆寫 render pipeline，因此使用 Graphics 的預設 URP；`fileID: 0` 在此代表沒有品質覆寫，不代表強制選用 Built-In。
- 遷移前未在主遊戲、共用套件及 Companion 的 C# 發現 runtime pipeline 切換。這次只新增 Editor 設定工具，不新增 runtime 切換；不是對外部 DLL 或所有動態行為的保證。
- Companion 原先的 [GraphicsSettings](<../UltraStar Play Companion/ProjectSettings/GraphicsSettings.asset>) 與 [QualitySettings](<../UltraStar Play Companion/ProjectSettings/QualitySettings.asset>) 未指定 SRP；後續獨立核准並完成 URP 設定遷移，Editor 也已升為 6.6，見本文件 Companion 遷移段落。
- 桌機主遊戲不需為淘汰通知重新做一次 Built-In → URP 遷移，但仍須驗證第三方材質、shader、粒子與背景特效在 URP 下的實際顯示，不能以設定正確取代畫面驗證。
- 不再將 Built-In 視為新開發方向；Companion 遷移後仍需手機端的渲染／效能與配對實測。

來源：[Unity 6.5 Built-In Render Pipeline 文件](https://docs.unity.com/en-us/engine/6000.5/manual/render-pipelines/built-in-render-pipeline)。

## 授權

主專案採 MIT，但第三方程式、模型、Unity、音效、美術與歌曲不必然採相同授權。匯入及交付時必須保留聲明並核對實際隨附內容。

來源：[LICENSE](https://github.com/UltraStar-Deluxe/Play/blob/a4aaa0b31327062a92d12b5e4cab4d80777f2a3f/LICENSE)、[第三方授權概覽](https://github.com/UltraStar-Deluxe/Play/blob/a4aaa0b31327062a92d12b5e4cab4d80777f2a3f/UltraStar%20Play/Assets/StreamingAssets/InfoAndLegalTexts/License-Overview.txt)。

## 本機驗證後要補齊

1. 匯入 revision、目錄與宣告的 Unity 版本已核對；仍須確認工具安裝、授權，以及實際可執行的建置／測試命令。
2. 場景與控制器關係、共用 UI 消費端及主題套用方式。
3. 麥克風校正、時間換算、難度及評分的可重現測試。
4. 本機資料 schema、儲存路徑與相容／備份策略。
5. Companion 必要性、支援版本與連線測試。
6. 設計核准後的實作決策，以及必要的新架構 skills。
