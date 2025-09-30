# Script PowerShell para criar o instalador do SwitchPilot automaticamente
# Baixa o Inno Setup se necessário e gera o instalador

param(
    [switch]$SkipDownload = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SwitchPilot - Gerador de Instalador" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configurações
$InnoSetupURL = "https://jrsoftware.org/download.php/is.exe"
$InnoSetupInstaller = "innosetup_installer.exe"
$InnoSetupPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
$ScriptISS = "SwitchPilot_Installer.iss"

# Função para verificar se Inno Setup está instalado
function Test-InnoSetupInstalled {
    return Test-Path $InnoSetupPath
}

# Verificar se Inno Setup está instalado
if (-not (Test-InnoSetupInstalled)) {
    Write-Host "⚠️  Inno Setup não encontrado!" -ForegroundColor Yellow
    Write-Host ""
    
    if ($SkipDownload) {
        Write-Host "❌ Use -SkipDownload:`$false para baixar automaticamente" -ForegroundColor Red
        Write-Host ""
        Write-Host "Ou baixe manualmente em: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "📥 Baixando Inno Setup..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri $InnoSetupURL -OutFile $InnoSetupInstaller -UseBasicParsing
        Write-Host "✅ Download concluído!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📦 Instalando Inno Setup..." -ForegroundColor Yellow
        Write-Host "   (Siga as instruções na janela de instalação)" -ForegroundColor Gray
        Start-Process -FilePath $InnoSetupInstaller -Wait
        
        # Verificar se foi instalado
        if (-not (Test-InnoSetupInstalled)) {
            Write-Host "❌ Instalação cancelada ou falhou" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "✅ Inno Setup instalado com sucesso!" -ForegroundColor Green
        Write-Host ""
        
        # Remover instalador
        Remove-Item $InnoSetupInstaller -ErrorAction SilentlyContinue
    }
    catch {
        Write-Host "❌ Erro ao baixar Inno Setup: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Baixe manualmente em: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
        exit 1
    }
}
else {
    Write-Host "✅ Inno Setup encontrado!" -ForegroundColor Green
    Write-Host ""
}

# Verificar se o script .iss existe
if (-not (Test-Path $ScriptISS)) {
    Write-Host "❌ Arquivo $ScriptISS não encontrado!" -ForegroundColor Red
    exit 1
}

# Verificar se a pasta release_v1.5.1 existe
if (-not (Test-Path "release_v1.5.1")) {
    Write-Host "❌ Pasta release_v1.5.1 não encontrada!" -ForegroundColor Red
    Write-Host "   Execute o build primeiro: pyinstaller SwitchPilot.spec --clean" -ForegroundColor Yellow
    exit 1
}

# Criar pasta de saída
$OutputDir = "installer_output"
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

Write-Host "🔨 Gerando instalador..." -ForegroundColor Yellow
Write-Host ""

# Compilar o instalador
try {
    $process = Start-Process -FilePath $InnoSetupPath `
                             -ArgumentList "/Q`"$((Get-Location).Path)\$ScriptISS`"" `
                             -Wait `
                             -PassThru `
                             -NoNewWindow
    
    if ($process.ExitCode -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  ✅ INSTALADOR CRIADO COM SUCESSO!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        
        # Encontrar o arquivo gerado
        $installerFile = Get-ChildItem -Path $OutputDir -Filter "SwitchPilot_v*_Setup.exe" | 
                        Sort-Object LastWriteTime -Descending | 
                        Select-Object -First 1
        
        if ($installerFile) {
            $fileSize = [math]::Round($installerFile.Length / 1MB, 2)
            Write-Host "📦 Arquivo: $($installerFile.Name)" -ForegroundColor Cyan
            Write-Host "📏 Tamanho: $fileSize MB" -ForegroundColor Cyan
            Write-Host "📁 Local: $((Get-Location).Path)\$OutputDir\" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "🚀 Pronto para distribuir!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Para testar, execute:" -ForegroundColor Yellow
            Write-Host "   .\$OutputDir\$($installerFile.Name)" -ForegroundColor White
        }
    }
    else {
        Write-Host "❌ Erro ao gerar instalador (código: $($process.ExitCode))" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "❌ Erro ao executar Inno Setup: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Pressione Enter para sair..." -ForegroundColor Gray
Read-Host
