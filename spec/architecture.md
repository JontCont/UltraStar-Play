# 架構研究基線

## 證據狀態

- 研究日期：2026-10-24。
- 研究對象：[UltraStar-Deluxe/Play](https://github.com/UltraStar-Deluxe/Play) 公開主分支與發布說明。
- 查閱時主分支 commit：`a4aaa0b31327062a92d12b5e4cab4d80777f2a3f`，日期 2026-10-21。
- 最新列出的發布版為 [v1.7.1-beta1](https://github.com/UltraStar-Deluxe/Play/releases/tag/v1.7.1-beta1)，發布於 2026-09-16。
- 下列原始碼連結固定在研究 commit，避免後續主分支變動混淆研究結果。
- 使用者已確認並匯入上述 commit。本機已核對來源、Git 歷史及部分建置 metadata；以下行為描述仍以研究為主，不代表已通過 Unity 建置或實機驗證。

## 本機匯入紀錄

- 匯入日期：2026-10-24，位置為目前 workspace 根目錄。
- 工作分支：`desktop-refresh`；`HEAD` 為上述完整 commit。
- 來源 remote：`upstream`，URL 為 `https://github.com/UltraStar-Deluxe/Play.git`。未設定發布 remote、未建立新提交或推送。
- 保留該 commit 的 2,696 筆祖先提交，不是 shallow clone。使用 `blob:none` 延後下載非當前版本所需的歷史檔案；查閱未快取的舊檔案時仍可能需要連網。
- 上游帶有 4,904 個追蹤檔案。checkout 後的程式碼與上游相同；唯一刻意修改的上游文件為主遊戲 AI 入口。
- 原有 8 份規劃與 AI 指引在匯入前後 SHA-256 相同；後續狀態更新另行編輯。
- 上游主遊戲 AI 指引已改為轉向 `.agents/`，原始內文保留為 [歷史參考](../.agents/references/upstream-main-game-guidelines.md)，不作為第二套生效規範。
- 目前只驗證 Git 物件連通性及工作樹，未還原依賴，也未驗證 Unity 執行。

## 上游主要邊界

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

- AI 製譜與即時演唱評分是不同流程。
- 2026 年整合使用 UVR、Parakeet、RMVPE 與 NeMo Forced Aligner 等工具。
- 模型與 FFmpeg 函式庫預設不隨建置下載；UI 翻新不得假定它們存在。
- 本機 `ProjectVersion.txt` 指定 Unity `6000.5.6f1`；匯入其他 tag 時必須重新核對。
- 本機 Nuke 建置專案目標為 `net8.0`，使用 `Nuke.Common` `9.0.4`。
- 已從 `NukeBuild/Build.cs` 核對 `RestoreMainGameDependencies`、`BuildMainGameWindows64`、`TestMainGame` target；尚未執行，不能視為成功命令。
- 上游測試 workflow 仍指定 Unity `6000.1.3f1`，與本機專案版本不一致。此為既有設定，未在匯入時修改；不可因此宣稱目前 CI 已驗證本版本。
- 根目錄 `build.ps1` 會建置 Nuke 專案，找不到 .NET 時還可能下載 SDK；不能將呼叫腳本的 `--help` 當作沒有副作用的環境探測。

來源：[依賴下載器](https://github.com/UltraStar-Deluxe/Play/blob/a4aaa0b31327062a92d12b5e4cab4d80777f2a3f/NukeBuild/MainGameDependencyDownloader.cs)、[Unity 版本](https://github.com/UltraStar-Deluxe/Play/blob/a4aaa0b31327062a92d12b5e4cab4d80777f2a3f/UltraStar%20Play/ProjectSettings/ProjectVersion.txt)。

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
