; Script de instalaÃ§Ã£o do SwitchPilot usando Inno Setup
; Gera um instalador .exe profissional para Windows

#define MyAppName "SwitchPilot"
#define MyAppVersion "1.5.2"
#define MyAppPublisher "Fabianob19"
#define MyAppURL "https://github.com/Fabianob19/SwitchPilot"
#define MyAppExeName "SwitchPilot.exe"
#define MyAppIconName "ICONE.ico"

[Setup]
; InformaÃ§Ãµes bÃ¡sicas do aplicativo
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
; SaÃ­da do instalador
OutputDir=installer_output
OutputBaseFilename=SwitchPilot_v{#MyAppVersion}_Setup
; CompressÃ£o
Compression=lzma2/ultra64
SolidCompression=yes
; ConfiguraÃ§Ãµes visuais
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
Name: "quicklaunchicon"; Description: "Criar Ã­cone na Barra de Tarefas"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Arquivos principais (toda a pasta release_v1.5.2)
Source: "release_v1.5.2\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Ãcone do aplicativo (garantir que seja copiado)
Source: "{#MyAppIconName}"; DestDir: "{app}"; Flags: ignoreversion
; Arquivos de documentaÃ§Ã£o
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Atalho no Menu Iniciar
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Atalho na Ãrea de Trabalho
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconName}"; Tasks: desktopicon
; Atalho na Barra de Tarefas (Quick Launch)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconName}"; Tasks: quicklaunchicon

[Run]
; Executar apÃ³s instalaÃ§Ã£o (opcional e nÃ£o selecionado por padrÃ£o)
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent unchecked

[UninstallDelete]
; Limpar configuraÃ§Ãµes ao desinstalar (opcional)
Type: filesandordirs; Name: "{app}\switchpilot_config.json"

[Code]
// CÃ³digo Pascal para funcionalidades extras

// Verificar se o Visual C++ Redistributable estÃ¡ instalado
function VCRedistInstalled(): Boolean;
var
  RegKey: String;
begin
  Result := False;
  
  // Verificar versÃµes 2015-2022 (x64)
  RegKey := 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\X64';
  if RegKeyExists(HKEY_LOCAL_MACHINE, RegKey) then
    Result := True
  else
  begin
    // Verificar versÃ£o alternativa
    RegKey := 'SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\X64';
    if RegKeyExists(HKEY_LOCAL_MACHINE, RegKey) then
      Result := True;
  end;
end;

// Baixar e instalar VC++ Redistributable
procedure InstallVCRedist();
var
  ResultCode: Integer;
  DownloadPage: TDownloadWizardPage;
begin
  if not VCRedistInstalled() then
  begin
    if MsgBox('O SwitchPilot requer o Microsoft Visual C++ Redistributable.' + #13#10#13#10 +
              'Deseja baixar e instalar automaticamente?' + #13#10#13#10 +
              '(Recomendado: Sim)', 
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      // Mostrar mensagem de download
      MsgBox('O instalador irÃ¡ baixar o Visual C++ Redistributable (~25 MB).' + #13#10 +
             'Por favor, aguarde e siga as instruÃ§Ãµes do instalador.', 
             mbInformation, MB_OK);
      
      // Tentar executar o download e instalaÃ§Ã£o
      if not ShellExec('open', 
                       'https://aka.ms/vs/17/release/vc_redist.x64.exe',
                       '', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
      begin
        MsgBox('NÃ£o foi possÃ­vel baixar automaticamente.' + #13#10#13#10 +
               'Por favor, baixe e instale manualmente de:' + #13#10 +
               'https://aka.ms/vs/17/release/vc_redist.x64.exe' + #13#10#13#10 +
               'Depois execute o instalador do SwitchPilot novamente.', 
               mbError, MB_OK);
      end;
    end
    else
    begin
      MsgBox('AVISO: Sem o Visual C++ Redistributable, o SwitchPilot pode nÃ£o funcionar.' + #13#10#13#10 +
             'Se encontrar erros ao executar, instale de:' + #13#10 +
             'https://aka.ms/vs/17/release/vc_redist.x64.exe', 
             mbInformation, MB_OK);
    end;
  end;
end;

procedure InitializeWizard();
begin
  // CustomizaÃ§Ãµes da janela de instalaÃ§Ã£o podem ser adicionadas aqui
end;

function InitializeSetup(): Boolean;
var
  OldUninstallPath: String;
  ResultCode: Integer;
begin
  Result := True;
  
  // Verificar dependÃªncias do sistema
  InstallVCRedist();
  
  // Verificar se existe uma instalaÃ§Ã£o antiga com desinstalador corrompido
  if RegQueryStringValue(HKEY_CURRENT_USER, 
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\{A5B8C3D4-E6F7-4A8B-9C0D-1E2F3A4B5C6D}_is1',
    'UninstallString', OldUninstallPath) then
  begin
    // Se o desinstalador nÃ£o existe mais, limpar o registro
    if not FileExists(OldUninstallPath) then
    begin
      RegDeleteKeyIncludingSubkeys(HKEY_CURRENT_USER, 
        'Software\Microsoft\Windows\CurrentVersion\Uninstall\{A5B8C3D4-E6F7-4A8B-9C0D-1E2F3A4B5C6D}_is1');
      
      // Informar o usuÃ¡rio
      MsgBox('Detectada instalaÃ§Ã£o antiga corrompida. ' +
             'A instalaÃ§Ã£o serÃ¡ limpa automaticamente.', 
             mbInformation, MB_OK);
    end
    else
    begin
      // Se o desinstalador existe, perguntar se quer desinstalar
      if MsgBox('Uma versÃ£o anterior do SwitchPilot foi detectada. ' +
                'Deseja desinstalÃ¡-la antes de continuar?' + #13#10#13#10 +
                'Recomendado: Sim', 
                mbConfirmation, MB_YESNO) = IDYES then
      begin
        Exec(OldUninstallPath, '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
      end;
    end;
  end;
end;

