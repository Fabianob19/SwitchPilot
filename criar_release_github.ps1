# Script para criar release no GitHub automaticamente
# SwitchPilot - Automação de Releases

Write-Host "=== Criador de Release GitHub - SwitchPilot ===" -ForegroundColor Cyan
Write-Host ""

# Adicionar gh ao PATH se necessário
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "Adicionando GitHub CLI ao PATH..." -ForegroundColor Yellow
    $env:Path += ";C:\Program Files\GitHub CLI"
}

# Verificar se gh está disponível agora
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "ERRO: GitHub CLI não encontrado!" -ForegroundColor Red
    Write-Host "Baixe em: https://cli.github.com/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Ou use o método manual:" -ForegroundColor Yellow
    Write-Host "1. Abra: https://github.com/Fabianob19/SwitchPilot/releases/new" -ForegroundColor White
    Write-Host "2. Siga as instruções em COMO_CRIAR_RELEASE_v1.5.1.txt" -ForegroundColor White
    pause
    exit 1
}

Write-Host "GitHub CLI encontrado!" -ForegroundColor Green
Write-Host ""

# Verificar autenticação
Write-Host "Verificando autenticação..." -ForegroundColor Yellow
gh auth status 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Você não está autenticado. Iniciando login..." -ForegroundColor Yellow
    Write-Host ""
    gh auth login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Erro na autenticação!" -ForegroundColor Red
        pause
        exit 1
    }
}

Write-Host "Autenticado com sucesso!" -ForegroundColor Green
Write-Host ""

# Obter versão atual
$version = "v1.5.1"
Write-Host "Criando release: $version" -ForegroundColor Cyan
Write-Host ""

# Verificar se o ZIP existe
$zipFile = "SwitchPilot_v1.5.1.zip"
if (-not (Test-Path $zipFile)) {
    Write-Host "ERRO: Arquivo $zipFile não encontrado!" -ForegroundColor Red
    Write-Host "Execute primeiro: pyinstaller SwitchPilot.spec --clean" -ForegroundColor Yellow
    pause
    exit 1
}

# Verificar se o arquivo de release notes existe
$notesFile = "RELEASE_NOTES_v1.5.1.md"
if (-not (Test-Path $notesFile)) {
    Write-Host "AVISO: $notesFile não encontrado. Usando descrição padrão." -ForegroundColor Yellow
    $notes = "Release $version do SwitchPilot"
} else {
    $notes = Get-Content $notesFile -Raw
}

# Criar a release
Write-Host "Criando release no GitHub..." -ForegroundColor Yellow
Write-Host ""

try {
    gh release create $version `
        --title "SwitchPilot $version - Otimizações de Detecção" `
        --notes $notes `
        --latest `
        $zipFile

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ RELEASE CRIADA COM SUCESSO!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Acesse em: https://github.com/Fabianob19/SwitchPilot/releases" -ForegroundColor Cyan
    } else {
        Write-Host "Erro ao criar release!" -ForegroundColor Red
    }
} catch {
    Write-Host "Erro: $_" -ForegroundColor Red
}

Write-Host ""
pause
