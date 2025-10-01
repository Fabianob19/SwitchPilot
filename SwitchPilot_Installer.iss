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

// Verificar se o Visual C++ Redistributable está instalado
function VCRedistInstalled(): Boolean;
var
  RegKey: String;
begin
  Result := False;
  
  // Verificar versões 2015-2022 (x64)
  RegKey := 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\X64';
  if RegKeyExists(HKEY_LOCAL_MACHINE, RegKey) then
    Result := True
  else
  begin
    // Verificar versão alternativa
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
      MsgBox('O instalador irá baixar o Visual C++ Redistributable (~25 MB).' + #13#10 +
             'Por favor, aguarde e siga as instruções do instalador.', 
             mbInformation, MB_OK);
      
      // Tentar executar o download e instalação
      if not ShellExec('open', 
                       'https://aka.ms/vs/17/release/vc_redist.x64.exe',
                       '', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
      begin
        MsgBox('Não foi possível baixar automaticamente.' + #13#10#13#10 +
               'Por favor, baixe e instale manualmente de:' + #13#10 +
               'https://aka.ms/vs/17/release/vc_redist.x64.exe' + #13#10#13#10 +
               'Depois execute o instalador do SwitchPilot novamente.', 
               mbError, MB_OK);
      end;
    end
    else
    begin
      MsgBox('AVISO: Sem o Visual C++ Redistributable, o SwitchPilot pode não funcionar.' + #13#10#13#10 +
             'Se encontrar erros ao executar, instale de:' + #13#10 +
             'https://aka.ms/vs/17/release/vc_redist.x64.exe', 
             mbInformation, MB_OK);
    end;
  end;
end;

procedure InitializeWizard();
begin
  // Customizações da janela de instalação podem ser adicionadas aqui
end;

function InitializeSetup(): Boolean;
var
  OldUninstallPath: String;
  ResultCode: Integer;
begin
  Result := True;
  
  // Verificar dependências do sistema
  InstallVCRedist();
  
  // Verificar se existe uma instalação antiga com desinstalador corrompido
  if RegQueryStringValue(HKEY_CURRENT_USER, 
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\{A5B8C3D4-E6F7-4A8B-9C0D-1E2F3A4B5C6D}_is1',
    'UninstallString', OldUninstallPath) then
  begin
    // Se o desinstalador não existe mais, limpar o registro
    if not FileExists(OldUninstallPath) then
    begin
      RegDeleteKeyIncludingSubkeys(HKEY_CURRENT_USER, 
        'Software\Microsoft\Windows\CurrentVersion\Uninstall\{A5B8C3D4-E6F7-4A8B-9C0D-1E2F3A4B5C6D}_is1');
      
      // Informar o usuário
      MsgBox('Detectada instalação antiga corrompida. ' +
             'A instalação será limpa automaticamente.', 
             mbInformation, MB_OK);
    end
    else
    begin
      // Se o desinstalador existe, perguntar se quer desinstalar
      if MsgBox('Uma versão anterior do SwitchPilot foi detectada. ' +
                'Deseja desinstalá-la antes de continuar?' + #13#10#13#10 +
                'Recomendado: Sim', 
                mbConfirmation, MB_YESNO) = IDYES then
      begin
        Exec(OldUninstallPath, '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
      end;
    end;
  end;
end;
