# Script PowerShell para criar o instalador do SwitchPilot
# Versao simplificada

Write-Host "========================================"
Write-Host "  SwitchPilot - Gerador de Instalador"
Write-Host "========================================"
Write-Host ""

$InnoSetupPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
$ScriptISS = "SwitchPilot_Installer.iss"

# Verificar se Inno Setup esta instalado
if (-not (Test-Path $InnoSetupPath)) {
    Write-Host "Inno Setup nao encontrado!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Baixe em: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Ou execute:" -ForegroundColor Yellow
    Write-Host "  winget install -e --id JRSoftware.InnoSetup" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "Inno Setup encontrado!" -ForegroundColor Green
Write-Host ""

# Verificar se o script .iss existe
if (-not (Test-Path $ScriptISS)) {
    Write-Host "Arquivo $ScriptISS nao encontrado!" -ForegroundColor Red
    exit 1
}

# Verificar se a pasta release existe
if (-not (Test-Path "release_v1.5.1")) {
    Write-Host "Pasta release_v1.5.1 nao encontrada!" -ForegroundColor Red
    Write-Host "Execute o build primeiro:" -ForegroundColor Yellow
    Write-Host "  pyinstaller SwitchPilot.spec --clean" -ForegroundColor White
    exit 1
}

# Criar pasta de saida
$OutputDir = "installer_output"
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

Write-Host "Gerando instalador..." -ForegroundColor Yellow
Write-Host ""

# Compilar o instalador
$fullPath = (Get-Location).Path + "\" + $ScriptISS
& $InnoSetupPath $fullPath

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================"
    Write-Host "  INSTALADOR CRIADO COM SUCESSO!"
    Write-Host "========================================"
    Write-Host ""
    
    $installerFile = Get-ChildItem -Path $OutputDir -Filter "*.exe" | 
                    Sort-Object LastWriteTime -Descending | 
                    Select-Object -First 1
    
    if ($installerFile) {
        $fileSize = [math]::Round($installerFile.Length / 1MB, 2)
        Write-Host "Arquivo: $($installerFile.Name)"
        Write-Host "Tamanho: $fileSize MB"
        Write-Host "Local: $((Get-Location).Path)\$OutputDir\"
        Write-Host ""
        Write-Host "Pronto para distribuir!" -ForegroundColor Green
    }
}
else {
    Write-Host "Erro ao gerar instalador" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Pressione Enter para sair..."
Read-Host
