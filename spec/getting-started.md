# 開啟桌機開發版

## 目前可用方式

主遊戲目前使用 **Unity 6.6（6000.6.7f1）及 URP 17.6.0**，已成功編譯並產生 Windows EXE。核心演唱測試仍失敗，因此這是供檢查原版行為的開發成品，不是已完成驗收的翻新版。

### 直接開 Windows 成品

開啟 [UltraStar Play.exe](<../Build/UltraStarPlay-v1.7.1-beta1-Windows64/UltraStar Play.exe>)。

請保留同目錄的 `UnityPlayer.dll`、資料夾及其他依賴，不要只搬 EXE。這個 Build 目錄不納入版本控制，重新 clone 後需要重新建置；目錄名稱保留上游版本號，不代表本專案已發行新版本。

### 用安裝檔測試兩台 Windows 連線

2026-10-26 已產生兩份 **Windows 64-bit 區網測試版**：

| 裝置 | 安裝檔 |
|---|---|
| A：執行主遊戲 | [UltraStarPlay-Windows64-Setup.exe](../Build/Installers/UltraStarPlay-Windows64-Setup.exe)，約 171 MiB |
| B：執行 Companion | [UltraStarPlayCompanion-Windows64-Setup.exe](../Build/Installers/UltraStarPlayCompanion-Windows64-Setup.exe)，約 73 MiB |

各自只需複製一個 Setup.exe，不需要搬 Unity 專案或另外安裝 Unity／.NET。[SHA256SUMS.txt](../Build/Installers/SHA256SUMS.txt) 可供傳輸後核對。成品在 ignored `Build` 目錄，不會隨 clone 取得。

安裝精靈使用英文；程式內仍可選繁體中文。安裝位置預設為目前使用者的 `%LOCALAPPDATA%\Programs\UltraStar Play LAN Test` 或 `UltraStar Play Companion LAN Test`，不要求管理員權限，提供開始功能表捷徑與解除安裝。這是未簽章的本機測試成品，可能出現 SmartScreen 提示；只執行你確認來源及校驗碼的檔案。

安裝檔不夾帶私人歌曲或設定、不自動修改防火牆，也不刪除既有歌庫。**執行後會沿用各程式既有的本機使用者資料**；LAN Test 名稱只區分安裝位置，不代表另建設定 profile。解除安裝保留使用者資料。

#### 連線步驟

1. A、B 接上同一個可信任的區域網路，可使用同一路由器下的 Wi-Fi 或網路線；不要使用隔離裝置的訪客網路。Windows 的私人網路設定只用在可信任網路。
2. A 安裝並開啟主遊戲。先關閉其他舊版主遊戲，避免重複占用連線埠。在 PowerShell 執行 `ipconfig`，記下實際連線網卡的 IPv4，例如 `192.168.1.10`；不要使用 VPN／虛擬網卡的位址。
3. B 安裝並開啟 Companion。預設會自動探索；若持續顯示連線中，按右上角齒輪、開啟 **Developer Mode／開發者模式**，將 **IP Address of Main Game** 設為 A 的 IPv4，**Connection Port** 保持 `34567`。只輸入 IP，不加 `http://` 或 port；另一台電腦不能使用 `127.0.0.1`。
4. Windows 防火牆若詢問，僅在可信任的**私人網路**允許這兩個程式，不要關閉整個防火牆或設定路由器對外轉送。主要通訊為 A 的 **UDP 34567**（探索／配對／訊息）與 **TCP 6789**（HTTP 功能）；若手動改過遊戲設定，須使用實際 port。Companion 使用動態 UDP 本機埠，宜採程式規則而非只在 B 開放 34567。
5. A 進入 **設定 → 手機應用程式**（Companion 應用程式），確認出現 B；B 的連線中畫面應切換為麥克風／歌曲／控制頁籤。如果要求權限已開啟，僅授予這台測試裝置所需的點歌或模擬輸入權限。
6. 如要測收音，在 B 的 Windows 麥克風隱私設定允許桌面應用程式存取，並在 Companion 選擇錄音裝置；再於 A 選擇該 Companion 麥克風。**配對成功不代表收音、延遲或演唱評分已驗收**；現有流程傳送音高事件，不代表會把 B 的人聲串流到 A 擴音。

只測 TCP 是否可達，可在 B 執行 `Test-NetConnection 192.168.1.10 -Port 6789`（改成 A 的 IP）。它**不能驗證 UDP 配對**。若 TCP 通但仍無法配對，核對 UDP 程式規則、兩端 34567 設定及有無第二個主遊戲；若已配對但點歌不可用，另查 HTTP、防火牆與 Companion 權限。

診斷記錄位於 `%USERPROFILE%\AppData\LocalLow\ultrastar\UltraStar Play\Logs` 及 `UltraStar Play Companion\Logs`。啟用開發者模式後也能複製記錄；不要只依 Unity `-logFile` 判斷，程式會將自訂記錄導向自己的每日 log。

#### 重建安裝檔

先關閉對應 Unity Editor。既有主遊戲 Windows player 可直接封裝；需要更新程式時先重建：

```powershell
$Unity = 'C:\Program Files\Unity\Hub\Editor\6000.6.7f1\Editor\Unity.exe'
& $Unity -batchmode -quit -projectPath '.\UltraStar Play' -buildTarget Win64 -executeMethod MainGameBuildTools.BuildWindows64 -logFile "$PWD\Build\main-windows.log"
& $Unity -batchmode -quit -projectPath '.\UltraStar Play Companion' -buildTarget Win64 -executeMethod CompanionAppBuildTools.BuildWindows64 -logFile "$PWD\Build\companion-windows.log"

# 只在缺少 Inno Setup 6 且核准安裝工具後執行：
winget install --id JRSoftware.InnoSetup -e --source winget --scope user

.\tools\windows-installer\Build-Installers.ps1 -Version '1.7.1-beta1-lan-test.20261026'
```

[封裝腳本](../tools/windows-installer/Build-Installers.ps1) 只打包現成 player，不會自動建置 Unity、還原依賴或安裝工具；可用 `-MainGameBuildPath`、`-CompanionBuildPath`、`-OutputDirectory`、`-IsccPath` 指定路徑。預設來源分別為主遊戲 `1.7.1-beta1` 與 Companion `1.3.4`，兩端已驗證使用相容的協定版本 7；安裝檔版本標籤不是修改上游應用程式版本。

封裝保留 Unity runtime 與授權文字，排除 `BackUpThisFolder_ButDontShipItWithYourGame`、PDB／MDB。Companion 安裝 payload 另外補入主遊戲的共用 FFmpeg 副檔名資料檔，避免啟動時缺少資料；不新增 FFmpeg 執行檔或變更媒體邏輯。

#### 本次驗證範圍

- `dotnet build '.\NukeBuild\NukeBuild.csproj' --no-restore --nologo`：通過，0 警告、0 錯誤；包含新增的 `BuildCompanionAppWindows64` target。
- 上述 `CompanionAppBuildTools.BuildWindows64`：Unity `Build Finished, Result: Success`，產生完整主場景 player，不使用舊的隔離渲染 smoke build。
- 上述封裝命令：兩份 Setup.exe 與 SHA-256 清單產生成功。未重新建置未修改的主遊戲，使用現有本機 Windows 成品。
- 兩份安裝檔均以 `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- /DIR=... /LOG=...` 在 session 測試目錄安裝；主遊戲 513、Companion 213 個來源 runtime 檔案逐一 SHA-256 相符，另外核對授權與新增副檔名資料檔，沒有備份／符號檔。
- 使用 `--settingsPath` 隔離設定啟動安裝後的兩個原生視窗，確認可回應；`127.0.0.1:34567` 完成實際 ConnectRequest／ConnectResponse、權限及 MicProfile 交換，主遊戲保存測試 client；HTTP `GET /api/rest/hello/installer-test` 回傳 `Hello installer-test`。
- 重新安裝與 `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /LOG=...` 解除安裝皆通過，保留自放 marker、移除專屬解除安裝登錄；既有兩端設定檔 hash 不變，測試 player 與安裝目錄已清理。
- 兩端啟動均觀察到 TextMeshPro 的 `TMP_Settings.get_defaultFontAsset` 空參照錯誤，來源 runtime 檔案與安裝後 hash 一致；未阻止本次配對，但不宣稱啟動 log 無錯，也未在封裝工作順手修正。
- **尚未驗證：兩台實體電腦的自動探索、防火牆／網路路由、遠端控制操作、跨機麥克風、完整演唱及乾淨 Windows 環境。** 本機 loopback 成功不等同這些項目通過，也不代表 T16 正式發行。

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

### 切換繁體中文

主遊戲先進入 **Options → Game → Language**，選擇 **Chinese (Traditional) - 繁體中文**。套用後介面切換為繁體，並沿用既有設定保存機制；簡體中文 **Chinese (Simplified)** 仍可選，不會強制改動原本的語言設定。

繁體翻譯資源與字型由主遊戲、Companion 共用，Companion 的語言選單也會列出繁體。現有 Companion 不會在啟動時套用保存的語言設定，重新啟動後需在選單重選；此既有行為不是本次新增翻譯所修改的範圍。

在 Unity Editor 載入更新的資源即可看到新選項；舊 EXE 不會因原始碼更新而改變，必須重新建置 Windows 成品。字型沿用既有 Noto Sans TC fallback，不需另裝系統字型。

2026-10-24 已重建本機 Windows 成品並以隔離設定啟動，主畫面繁體字形可見；不是只新增 README 或只驗證原始碼。主遊戲 20 項與 Companion 14 項 EditMode 通過，涵蓋 783 項 key／格式一致、兩種中文選項、四語設定序列化及現有字型的漢字覆蓋。尚未逐頁人工檢查所有長文字排版，也未因此重新驗證完整演唱。

同日後續已修正設定頁缺字：原有 CJK 字型限制為單張動態 atlas，顯示更多文字後容量不足；現在可自動增加 atlas 頁，不需變更字型或縮小文字。已再重建 Windows，實際檢查遊戲設定、錄音／全域設定，以及連續切換其他設定頁後回訪；側欄與錄音欄位中文字完整顯示。請結束舊版 EXE 後重新開啟同一路徑的新成品；正在執行的程序不會自動換用新字型資源。

缺字回歸命令均通過，另有 10 個字型容量案例證明修正前失敗、修正後實際跨多張 atlas 成功：

```powershell
# 30 passed，0 failed
& $Unity -batchmode -projectPath '.\UltraStar Play' -runTests -testPlatform EditMode -testFilter 'CjkFontAtlasTest;TraditionalChineseTranslationTest;SettingsUtilsTest' -testResults "$Evidence\cjk-atlas-main-results.xml" -logFile "$Evidence\cjk-atlas-main.log"
# 24 passed，0 failed
& $Unity -batchmode -projectPath '.\UltraStar Play Companion' -runTests -testPlatform EditMode -testFilter 'CjkFontAtlasTest;TraditionalChineseTranslationTest;CompanionLanguageSettingsTest' -testResults "$Evidence\cjk-atlas-companion-results.xml" -logFile "$Evidence\cjk-atlas-companion.log"
# Build Finished, Result: Success.
& $Unity -batchmode -quit -projectPath '.\UltraStar Play' -buildTarget Win64 -executeMethod MainGameBuildTools.BuildWindows64 -logFile "$Evidence\cjk-atlas-windows-build.log"
```

下列針對性命令均已通過（同一專案先關閉其他 Editor，`$Unity` 與 `$Evidence` 使用下方驗證區段定義）：

```powershell
# 20 passed，0 failed
& $Unity -batchmode -projectPath '.\UltraStar Play' -runTests -testPlatform EditMode -testFilter 'TraditionalChineseTranslationTest;SettingsUtilsTest' -testResults "$Evidence\zh-tw-main-final-editmode-results.xml" -logFile "$Evidence\zh-tw-main-final-editmode.log"
# 14 passed，0 failed
& $Unity -batchmode -projectPath '.\UltraStar Play Companion' -runTests -testPlatform EditMode -testFilter 'TraditionalChineseTranslationTest;CompanionLanguageSettingsTest' -testResults "$Evidence\zh-tw-companion-retry-editmode-results.xml" -logFile "$Evidence\zh-tw-companion-retry-editmode.log"
# Build Finished, Result: Success.
& $Unity -batchmode -quit -projectPath '.\UltraStar Play' -buildTarget Win64 -executeMethod MainGameBuildTools.BuildWindows64 -logFile "$Evidence\zh-tw-main-windows-build.log"
```

### 歌曲 ZIP 下載後無法匯入

若舊版下載官方歌曲包後出現 `Method not found: long ICSharpCode.SharpZipLib.Zip.ZipFile.get_Count()`，原因是 Windows 成品載入的 SharpZipLib 與編譯版本 API 不同，不是下載權限。歌曲 ZIP 匯入已改用 .NET 內建 `ZipArchive`，不需重裝 Unity 或另外安裝 ZIP 工具。

請關閉舊遊戲並重新開啟上方同一路徑的 Windows 成品，在 **設定 → 歌曲** 重新啟動歌曲包下載／匯入。程式沒有新增「匯入既有 ZIP」按鈕，從既有下載介面重試仍可能再次下載；原先下載失敗留下的 ZIP 沒有被本次修復刪除。

已在正常 Windows 成品的原下載 UI 匯入本機快取的官方 301 MB 包（測試透過 loopback，無須重新連外下載），217 個解壓檔案逐一比對長度與 SHA-256 全部正確，並確認成功後保存新增歌庫路徑；包含 85 個 `.txt` 與 50 個音訊檔。使用者設定未覆寫，測試副本已清理。這只驗證下載／解壓／登記歌庫，不代表完整演唱已通過。

```powershell
# 10 passed，0 failed，0 skipped
& $Unity -batchmode -projectPath '.\UltraStar Play' -runTests -testPlatform PlayMode -testFilter ArchiveExtractionTest -testResults "$Evidence\zip-import-playmode-results.xml" -logFile "$Evidence\zip-import-playmode.log"
# Build Finished, Result: Success.
& $Unity -batchmode -quit -projectPath '.\UltraStar Play' -buildTarget Win64 -executeMethod MainGameBuildTools.BuildWindows64 -logFile "$Evidence\zip-import-windows-build.log"
# 未通過：既有其他 PlayMode 測試的 VisualElementTestUtils 無法在此 target 編譯。
& $Unity -batchmode -projectPath '.\UltraStar Play' -runTests -testPlatform StandaloneWindows64 -buildTarget Win64 -testFilter ArchiveExtractionTest -testResults "$Evidence\zip-import-standalone-results.xml" -logFile "$Evidence\zip-import-standalone.log"
```

### 加歌後選歌頁空白

1. 在 **設定 → 歌曲** 登記並啟用根歌庫，譜面放在其子資料夾；新增檔案後重新啟動遊戲。
2. 確認譜面的 `#MP3`、`#VIDEO`、`#COVER` 與同目錄實際檔名完全一致。下載工具的輸出名稱未必與原譜面相同；修改前先備份，不要為了修檔名改動音符或 GAP。
3. 點選歌搜尋框旁的漏斗，播放清單選「所有歌曲」，或用面板底部重設清除篩選。

2026-10-24 已修正繁中、簡中與日文把空的 `Favorites` 排在「所有歌曲」前面的問題。請關閉舊程序後重新開啟上方 Windows 成品；新版預設首項固定為所有歌曲，仍可手動選其他清單。四語 PlayMode 4 項通過，重建後已用隔離設定實際看到本機歌曲卡片及封面，離開再回選歌仍正常。這不代表已校正該歌曲的影音／歌詞同步或驗證評分。

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
