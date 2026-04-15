#define MyAppName      "ValveMasterTool"
#define MyAppPublisher "ATS Inc"
#define MyAppExeName   "ValveMasterTool.exe"
#define MyAppDataDir   "{userappdata}\ATS Inc\ValveMasterTool"

; MyAppVersion is injected at build time by build.bat via:
;   ISCC /DMyAppVersion=1.2.3 installer.iss
; Do NOT hard-code a version here.

[Setup]
AppId={{A7F3C2D1-9B4E-4F6A-8C3D-1E5B7A9F2C4D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://github.com/JustinGlave/valve-master-tool
AppUpdatesURL=https://github.com/JustinGlave/valve-master-tool/releases

; Install to LocalAppData — no admin rights required
DefaultDirName={localappdata}\ATS Inc\{#MyAppName}
DefaultGroupName=ATS Inc\{#MyAppName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=

OutputDir=dist
OutputBaseFilename=ValveMasterToolSetup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Uninstaller
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

; Installer icon / branding
SetupIconFile=valve_master.ico
WizardImageFile=
WizardSmallImageFile=

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; Copy the entire PyInstaller output folder
Source: "dist\ValveMasterTool\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

; Desktop (optional, off by default)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Nothing to run before uninstall

[Code]
// ---------------------------------------------------------------------------
// On uninstall: ask the user whether to delete their saved app data.
// The data folder is %AppData%\ATS Inc\ValveMasterTool.
// If it doesn't exist yet, skip the prompt silently.
// ---------------------------------------------------------------------------
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir : String;
  Response: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataDir := ExpandConstant('{userappdata}\ATS Inc\{#MyAppName}');
    if DirExists(DataDir) then
    begin
      Response := MsgBox(
        'Would you like to delete your saved settings and app data?' + #13#10#13#10 +
        DataDir + #13#10#13#10 +
        'Click Yes to delete everything, or No to keep your data.',
        mbConfirmation, MB_YESNO
      );
      if Response = IDYES then
        DelTree(DataDir, True, True, True);
    end;
  end;
end;
