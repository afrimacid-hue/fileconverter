#define MyAppName "File Converter"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "File Converter"
#define MyAppExeName "FileConverter.exe"

[Setup]
AppId={{A6E69C43-3E8B-4D70-BC8B-07D899EAB5B7}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\File Converter
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=admin
OutputDir=..\release
OutputBaseFilename=FileConverter-Setup-1.0.0
SetupIconFile=FileConverter.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\FileConverter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\File Converter"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\File Converter"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch File Converter"; Flags: nowait postinstall skipifsilent
