# 開啟桌機開發版

## 目前可用方式

主遊戲目前使用 **Unity 6.6（6000.6.7f1）及 URP 17.6.0**，已成功編譯並產生 Windows EXE。核心演唱測試仍失敗，因此這是供檢查原版行為的開發成品，不是已完成驗收的翻新版。

### 直接開 Windows 成品

開啟 [UltraStar Play.exe](<../Build/UltraStarPlay-v1.7.1-beta1-Windows64/UltraStar Play.exe>)。

請保留同目錄的 `UnityPlayer.dll`、資料夾及其他依賴，不要只搬 EXE。這個 Build 目錄不納入版本控制，重新 clone 後需要重新建置；目錄名稱保留上游版本號，不代表本專案已發行新版本。

### 用 Unity 開發

1. Unity Hub 登入並啟用適用授權；目前已找到 Editor：

   ```text
   C:\Program Files\Unity\Hub\Editor\6000.6.7f1\Editor\Unity.exe
   ```

2. 在 **Projects > Add / Add project from disk** 選取：

   ```text
   C:\company\personal\sing-it\UltraStar Play
   ```

   不是 repository 根目錄，也不是 `UltraStar Play Companion`。

3. 用 **6000.6.7f1** 開啟並等待匯入／編譯。主遊戲的 [ProjectVersion.txt](<../UltraStar Play/ProjectSettings/ProjectVersion.txt>) 已更新，不要用 6.5 回開遷移後專案。
4. 從 Project 視窗開啟 [MainScene.unity](<../UltraStar Play/Assets/Scenes/Main/MainScene.unity>)，按 **Play**。
5. 先用合法的測試歌曲與本機 USB 麥克風核對行為，Companion 不作為單機必要條件。

同一專案不要同時開啟互動 Editor 與 batch-mode 測試／建置。

### VS Code 的 Unity.Sdk／NU1503 訊息

建議使用獨立的 **Unity** profile。2026-10-24 已在 VS Code Insiders 的此 profile 安裝 Microsoft 官方 Unity extension，並自動加入 C# Dev Kit、C#、.NET Install Tool 三個依賴；沒有搬入其他 profile 的全端開發套件。[擴充套件建議](../.vscode/extensions.json) 只列官方 Unity extension，其依賴由 VS Code 處理。這與 Unity Package Manager 中的 `Visual Studio Editor` 套件不同，兩者都需要；本專案已使用相容版本，不要另裝舊的 `Visual Studio Code Editor` Unity 套件。

若看到 Memory Profiler 的「Project configuration could not be detected」、找不到 `Unity.Sdk` 或 `NU1503`，先看錯誤路徑。本次已查證 C# Dev Kit 自動建立的 workspace solution 誤收了 `Library\PackageCache` 裡的套件內部開發專案，還包含 Hot Reload 副本與 build 目錄的 Mod 範本；不是遊戲本身少安裝 .NET SDK。

- 根目錄的 [VS Code 工作區設定](../.vscode/settings.json) 已明確選擇主遊戲的 Unity-generated solution，不載入上述套件內部專案。
- 在 Command Palette 執行 **Developer: Reload Window**。若仍選到先前記住的 workspace solution，再執行 **.NET: Open Solution**，選 `UltraStar Play\UltraStar Play.slnx`。
- 開發 Companion 時改選 `UltraStar Play Companion\UltraStar Play Companion.slnx`；不要將整個 repository 的所有 `.csproj` 一起加入。
- 若 generated solution／project 尚不存在，在對應 Unity Editor 的 **Preferences > External Tools** 重新產生專案；不要自行編寫 Unity 的 generated `.csproj`。
- 保留 Memory Profiler，不修改 PackageCache、不停用 NuGet restore、不以 `NoWarn` 隱藏警告，也不為這些套件內部專案亂裝 `Unity.Sdk`。

2026-10-24 已在兩個正確的 generated solution 執行以下檢查；這是 IDE 專案還原，不代替 Unity 遊戲建置。工作區設定生效後的 VS Code health check 仍須在 reload 後確認。

```powershell
# 兩者均成功，沒有 Unity.Sdk / MSB4236 / NU1503 訊息
dotnet restore '.\UltraStar Play\UltraStar Play.slnx' --verbosity minimal
dotnet restore '.\UltraStar Play Companion\UltraStar Play Companion.slnx' --verbosity minimal
```

## 2026-10-24 驗證結果

| 檢查 | 結果 |
|---|---|
| 主遊戲 Nuke 依賴還原 | 通過；本機已有 .NET 8，不重裝 SDK |
| Unity 6.6 首次匯入／編譯 | 首次被舊 Build Report Inspector 阻擋；移除僅 Editor 預覽工具後通過 |
| 最終針對性 EditMode | 38 通過、1 個既有 Ignore、0 失敗 |
| Windows64 player 建置 | 通過，最終 build report 為 `Build Finished, Result: Success.` |
| UXML scalar／shader 錯誤掃描 | 最終 build log 未找到；不等於所有畫面已人工驗收 |
| 核心演唱 PlayMode | 失敗，等待 SingScene 逾時；修正 UXML 後重試仍失敗 |
| 真實麥克風、音樂／影片同步及 URP 視覺效果 | 待人工驗證 |
| Companion Editor／URP | 匯入與編譯通過；5 個 EditMode、1 個隔離渲染 PlayMode 與 Windows smoke build 通過 |
| 遠端 CI、Android／iOS、手機配對 | 未執行／未驗證 |

本次只做引擎相容性，不做視覺改版、不改評分規則。沒有建立 6.5 執行基線，不能將現有測試失敗直接認定為 6.6 回歸。

## 已處理的相容性

- 移除無新版的 Editor-only `com.unity.build-report-inspector` `0.3.0-preview`，其 `BinaryFormatter` 用法觸發 6.6 編譯錯誤 `UAC0023`。工具提供的報告檢視選單不再提供，但 Unity BuildReport API 及建置 log 仍在。
- Editor 自動升級主遊戲套件與必要的序列化資產；主遊戲已使用 URP，不是本次從 Built-In 轉換。
- 修正 28 份主遊戲／共用 UXML 的兩種逗號小數為 `0.135`、`0.1`，排除 UI Toolkit 浮點解析錯誤。
- 兩專案 build/test workflow 均同步 Editor 版本；沒有執行遠端 workflow。

## 可重現命令與本次證據

從 repository 根目錄執行，並先關閉此專案的其他 Editor。下列 `$Evidence` 為本次執行位置；換機時可改為自己的 log 目錄。輸出 log／XML 不提交。

```powershell
Set-Location 'C:\company\personal\sing-it'
$Unity = 'C:\Program Files\Unity\Hub\Editor\6000.6.7f1\Editor\Unity.exe'
$Project = 'C:\company\personal\sing-it\UltraStar Play'
$Evidence = 'C:\Users\jontc\.copilot\session-state\71bf52ed-36f6-43b1-8f8f-d4469e08b7a9\files'

# 已成功。只有依賴缺失或需要重建時才重新執行
.\build.ps1 RestoreMainGameDependencies

# 已成功，exit 0；Editor 遷移與編譯
& $Unity -batchmode -quit -accept-apiupdate -projectPath $Project -logFile "$Evidence\unity66-import-retry.log"

# 最終 38 通過、1 個既有 Ignore、0 失敗，exit 0
& $Unity -batchmode -projectPath $Project -runTests -testPlatform EditMode -testFilter 'UltraStarSongFormatTest;TimeUtilsTest;ThemeMetaUtilsTest' -testResults "$Evidence\unity66-final-editmode-results.xml" -logFile "$Evidence\unity66-final-editmode.log"

# 仍失敗，exit 2；等待進入 SingScene 超過 10 秒
& $Unity -batchmode -projectPath $Project -runTests -testPlatform PlayMode -testFilter CoreGameLoopTest -testResults "$Evidence\unity66-core-loop-retry-results.xml" -logFile "$Evidence\unity66-core-loop-retry.log"

# 最終成功，exit 0；報告及 EXE 都已核對
& $Unity -batchmode -quit -projectPath $Project -buildTarget Win64 -executeMethod MainGameBuildTools.BuildWindows64 -logFile "$Evidence\unity66-final-windows-build.log"
```

目前沒有下載 AI 模型或額外 FFmpeg 函式庫。這些不是打開主畫面的必要條件；AI 製譜未經驗證。

## Companion：Unity 6.6／URP

使用者另行核准後，Companion 也已升到 **6000.6.7f1／URP 17.6.0**，不是繼續停留 Built-In。

1. Unity Hub 另加 [UltraStar Play Companion](<../UltraStar Play Companion>) 專案，用同一個 Editor 開啟。
2. 開啟 [Companion MainScene](<../UltraStar Play Companion/Assets/Scenes/MainScene/MainScene.unity>)，此專案與桌機主遊戲分開開啟。
3. 渲染資產已保存於 [RenderPipeline](<../UltraStar Play Companion/Assets/RenderPipeline>)，六個品質等級繼承 Graphics 預設；不必每次開啟重做遷移。需要重建缺少的設定時，現有選單 **Build > Configure Companion URP** 可重新套用，正常開發勿拿桌機 pipeline 覆蓋手機設定。

這次沒有修改連線 DTO、麥克風取樣／音高傳送、FPS 控制、色彩空間或介面設計。Companion 使用獨立 forward renderer，沒有新增後處理、深度／opaque texture、HDR 或陰影渲染成本。

驗證與限制：

- 5 個 EditMode：六個品質等級的 pipeline、forward renderer、camera data、兩份修正小數的 UXML。
- 1 個 PlayMode：真實 camera／panel／主畫面 UXML 在 runtime 可掛接、有非零 layout，並用官方 render request 實際呼叫 URP renderer。測試不建立完整應用控制器、不讀寫 profile、不啟動 discovery／麥克風；不是連線測試或手機截圖驗收。
- Windows smoke build 通過，用來確認 player／shader 編譯；不是 Android APK／iOS 成品。
- 現有手機連線、收音與點歌測試有既存 Ignore，本次未解除，也沒有將它們算作通過。
- 沒有 Android／iOS 模組，因此手機打包、觸控、權限、實際收音、耗電與主遊戲配對仍待驗證。需要 Android 時，可在 Hub 為相同 Editor 加入 **Android Build Support、SDK & NDK Tools、OpenJDK**；iOS 最終建置還需要 macOS／Xcode。此次未自行安裝。
- 已觀察到非渲染問題：共用 `ApplicationUtils` 啟動時讀不到 Companion 的 FFmpeg 副檔名資料檔並記錄 exception／fallback error。這發生於隔離測試開始前；不能用測試通過宣稱整段啟動 log 無錯。本次未壓制或擴大修改既有媒體邏輯。

在上方 `$Unity`、`$Evidence` 變數設定後，可使用下列命令：

```powershell
$Companion = 'C:\company\personal\sing-it\UltraStar Play Companion'

# 本次成功；會連帶還原主遊戲／共用 NuGet，兩專案 Editor 均須關閉
.\build.ps1 RestoreCompanionAppDependencies

# 本次成功；只在首次遷移或需要重建設定時執行，不是每次啟動必跑
& $Unity -batchmode -quit -projectPath $Companion -executeMethod CompanionAppBuildTools.ConfigureRenderPipeline -logFile "$Evidence\companion66-configure-retry.log"

# 5 通過、0 失敗、0 Ignore
& $Unity -batchmode -projectPath $Companion -runTests -testPlatform EditMode -testFilter CompanionRenderPipelineTest -testResults "$Evidence\companion66-final-editmode-results.xml" -logFile "$Evidence\companion66-final-editmode.log"

# 1 通過、0 失敗、0 Ignore；batch-mode 以 render request 主動繪製
& $Unity -batchmode -projectPath $Companion -runTests -testPlatform PlayMode -testFilter CompanionRenderSmokeTest -testResults "$Evidence\companion66-playmode-retry-results.xml" -logFile "$Evidence\companion66-playmode-retry.log"

# 成功，僅作 Windows smoke build，不是手機版發行
& $Unity -batchmode -quit -projectPath $Companion -buildWindows64Player 'C:\company\personal\sing-it\Build\Companion-Unity66-Smoke\UltraStar Play Companion.exe' -logFile "$Evidence\companion66-windows-smoke-build.log"

# 還原共用依賴後桌機回歸：38 通過、1 個既有 Ignore、0 失敗
& $Unity -batchmode -projectPath $Project -runTests -testPlatform EditMode -testFilter 'UltraStarSongFormatTest;TimeUtilsTest;ThemeMetaUtilsTest' -testResults "$Evidence\companion66-main-regression-results.xml" -logFile "$Evidence\companion66-main-regression.log"
```

## 尚待排查

- `CoreGameLoopTest` 已完成測試設定、模擬麥克風與選歌場景載入，但未成功轉入演唱場景；不應增加等待時間或忽略測試來宣稱成功。
- 先核對選歌到演唱的輸入／啟動流程，再完成一首歌及成績保存的 player 實測。
- 仍有上游 obsolete API、樣式及舊序列化設定警告，尚未全面清理；若實際造成阻礙，依第一個可重現問題處理，不混入大規模重構。
- 若主畫面、歌庫或麥克風有錯誤，保留第一個 Console 錯誤或 player log，不刪除插件硬跑。

進度見 [任務清單](tasks.md) 的 T03、T03C、T04；完整演唱驗證通過前不開始 UI 翻新。
