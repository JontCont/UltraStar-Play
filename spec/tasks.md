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

### T04

- 2026-10-24：執行現有 `CoreGameLoopTest` PlayMode 測試，使用測試設定、暫存歌曲與模擬麥克風，不以真實使用者歌庫作為測試資料。
- 初次及修正 UXML 後重試均失敗：`CoreGameLoopTest.cs:44` 等待 `SingScene` 超過 10 秒；目前僅確認載入選歌場景，不代表演唱與結算成功。
- 不加大 timeout、不忽略此測試，也不把失敗歸因為 URP 或 6.6；沒有 6.5 執行基線可供比較。
- 阻礙仍需排查選歌到演唱的輸入／啟動流程，並補上桌面 player 實際收音、影片同步、材質／特效、分數及成績儲存驗證。在此之前不開始 UI 翻新。

## 後續紀錄格式

每個開始執行的任務記錄：日期、範圍、使用的 skill、變更、驗證命令／人工步驟、實際結果，以及阻礙或核准事項。

`done` 必須有對應驗證；無法執行驗證時不得把預期結果寫成成功。
