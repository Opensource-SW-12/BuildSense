; BuildSense Inno Setup 인스톨러 스크립트
; 빌드 순서: build.ps1 (PyInstaller + 데이터 복사) -> ISCC.exe installer\BuildSense.iss

#define MyAppName "BuildSense"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "BuildSense"
#define MyAppExeName "BuildSense.exe"
#define SourceDir "..\dist\BuildSense"
#define IconFile "..\assets\icon.ico"

[Setup]
AppId={{FB2A2AF2-B101-4E00-B006-2BBB218EB978}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
SetupIconFile={#IconFile}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..
OutputBaseFilename=BuildSense-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--unregister-startup"; Flags: runhidden waituntilterminated; RunOnceId: "UnregisterStartup"
