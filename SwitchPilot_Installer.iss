; Script de instalação do SwitchPilot usando Inno Setup
; Gera um instalador .exe profissional para Windows

#define MyAppName "SwitchPilot"
#define MyAppVersion "1.5.1"
#define MyAppPublisher "Fabianob19"
#define MyAppURL "https://github.com/Fabianob19/SwitchPilot"
#define MyAppExeName "SwitchPilot.exe"
#define MyAppIconName "ICONE.ico"

[Setup]
; Informações básicas do aplicativo
AppId={{A5B8C3D4-E6F7-4A8B-9C0D-1E2F3A4B5C6D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
;InfoBeforeFile=release_v1.5.1\LEIA-ME.txt
; Saída do instalador
OutputDir=installer_output
OutputBaseFilename=SwitchPilot_v{#MyAppVersion}_Setup
; Compressão
Compression=lzma2/ultra64
SolidCompression=yes
; Configurações visuais
WizardStyle=modern
SetupIconFile={#MyAppIconName}
UninstallDisplayIcon={app}\{#MyAppExeName}
; Requisitos
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
PrivilegesRequired=lowest
; Idioma
ShowLanguageDialog=no

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "Criar ícone na Barra de Tarefas"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Arquivos principais (toda a pasta release_v1.5.1)
Source: "release_v1.5.1\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Ícone do aplicativo (garantir que seja copiado)
Source: "{#MyAppIconName}"; DestDir: "{app}"; Flags: ignoreversion
; Arquivos de documentação
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Atalho no Menu Iniciar
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Atalho na Área de Trabalho
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconName}"; Tasks: desktopicon
; Atalho na Barra de Tarefas (Quick Launch)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconName}"; Tasks: quicklaunchicon

[Run]
; Executar após instalação
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Limpar configurações ao desinstalar (opcional)
Type: filesandordirs; Name: "{app}\switchpilot_config.json"

[Code]
// Código Pascal para funcionalidades extras
procedure InitializeWizard();
begin
  // Customizações da janela de instalação podem ser adicionadas aqui
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  // Verificações antes da instalação podem ser adicionadas aqui
end;
