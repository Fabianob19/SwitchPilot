# Script para adicionar GitHub CLI ao PATH permanentemente
# Execute como Administrador

Write-Host "=== Configuração Permanente do GitHub CLI ===" -ForegroundColor Cyan
Write-Host ""

# Verificar se está executando como Admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "AVISO: Este script precisa ser executado como Administrador!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Clique com botão direito no PowerShell e selecione 'Executar como Administrador'" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Ou execute este comando manualmente (como Admin):" -ForegroundColor Yellow
    Write-Host '[System.Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\GitHub CLI", [System.EnvironmentVariableTarget]::Machine)' -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

# Verificar se gh existe
$ghPath = "C:\Program Files\GitHub CLI"
if (-not (Test-Path "$ghPath\gh.exe")) {
    Write-Host "ERRO: GitHub CLI não encontrado em: $ghPath" -ForegroundColor Red
    Write-Host "Baixe em: https://cli.github.com/" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "GitHub CLI encontrado em: $ghPath" -ForegroundColor Green
Write-Host ""

# Verificar se já está no PATH
$currentPath = [System.Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::Machine)

if ($currentPath -like "*$ghPath*") {
    Write-Host "GitHub CLI já está no PATH do sistema!" -ForegroundColor Yellow
} else {
    Write-Host "Adicionando GitHub CLI ao PATH do sistema..." -ForegroundColor Yellow
    
    # Adicionar ao PATH
    [System.Environment]::SetEnvironmentVariable(
        "Path",
        $currentPath + ";$ghPath",
        [System.EnvironmentVariableTarget]::Machine
    )
    
    Write-Host "✅ GitHub CLI adicionado ao PATH com sucesso!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Para usar o gh, abra um NOVO PowerShell e execute:" -ForegroundColor Cyan
Write-Host "  gh auth login" -ForegroundColor White
Write-Host ""
Write-Host "Depois, para criar releases:" -ForegroundColor Cyan
Write-Host "  .\criar_release_github.ps1" -ForegroundColor White
Write-Host ""

pause
