#if Product == "MainGame"
  #define AppName "UltraStar Play"
  #define AppId "JontCont.UltraStarPlay.WindowsLanTest"
  #define OutputName "UltraStarPlay-Windows64-Setup"
#elif Product == "Companion"
  #define AppName "UltraStar Play Companion"
  #define AppId "JontCont.UltraStarPlayCompanion.WindowsLanTest"
  #define OutputName "UltraStarPlayCompanion-Windows64-Setup"
#else
  #error Unsupported Product
#endif

[Setup]
AppId={#AppId}
AppName={#AppName} (LAN Test)
AppVersion={#AppVersion}
AppPublisher=UltraStar Play contributors / JontCont
AppPublisherURL=https://github.com/JontCont/UltraStar-Play
DefaultDirName={localappdata}\Programs\{#AppName} LAN Test
DefaultGroupName=UltraStar Play LAN Test
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
WizardStyle=modern
LicenseFile={#RepoRoot}\LICENSE
OutputDir={#OutputDir}
OutputBaseFilename={#OutputName}
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\{#AppName}.exe
CloseApplications=yes
RestartApplications=no
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\{#AppName}.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\UnityPlayer.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\UnityCrashHandler64.exe"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "{#SourceDir}\dstorage*.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "{#SourceDir}\{#AppName}_Data\*"; DestDir: "{app}\{#AppName}_Data"; Excludes: "*.pdb,*.mdb"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceDir}\MonoBleedingEdge\*"; DestDir: "{app}\MonoBleedingEdge"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceDir}\D3D12\*"; DestDir: "{app}\D3D12"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "{#RepoRoot}\LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion
Source: "{#RepoRoot}\UltraStar Play\Assets\StreamingAssets\InfoAndLegalTexts\*.txt"; DestDir: "{app}\Legal"; Flags: ignoreversion
#if Product == "Companion"
Source: "{#RepoRoot}\UltraStar Play\Assets\StreamingAssets\ffmpeg-supported-common-file-extensions.txt"; DestDir: "{app}\{#AppName}_Data\StreamingAssets"; Flags: ignoreversion
#endif

[Icons]
Name: "{group}\{#AppName} (LAN Test)"; Filename: "{app}\{#AppName}.exe"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#AppName} (LAN Test)"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName} (LAN Test)"; Filename: "{app}\{#AppName}.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppName}.exe"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
