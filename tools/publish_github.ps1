Param(
    [string]$RepoName = "SwitchPilot",
    [string]$Tag = "v1.5.0-beta1",
    [string]$CleanZip = "SwitchPilot_v1.5.0-beta1_clean.zip",
    [string]$FullZip = "SwitchPilot_v1.5.0-beta1.zip"
)

$ErrorActionPreference = "Stop"

if (-not $env:GITHUB_TOKEN -or $env:GITHUB_TOKEN -eq "") {
    Write-Error "GITHUB_TOKEN not set"
    exit 1
}

# Verificar Git disponível
try {
    git --version | Out-Null
} catch {
    Write-Error "Git não encontrado no PATH. Instale Git e reabra o terminal."
    exit 1
}

$Headers = @{
    Authorization = "token $($env:GITHUB_TOKEN)"
    "User-Agent"  = "SwitchPilotCI"
    Accept         = "application/vnd.github+json"
}

# Descobrir usuário
$user = Invoke-RestMethod -Headers $Headers -Uri "https://api.github.com/user" -Method Get
$login = $user.login
$RepoHttp = "https://github.com/$login/$RepoName.git"

# Garantir repositório Git inicializado e com commit
if (-not (Test-Path ".git")) {
    git init | Out-Null
    git config user.name  "SwitchPilot"
    git config user.email "switchpilot@users.noreply.github.com"
    git add -A | Out-Null
    try { git commit -m "chore: initial commit" | Out-Null } catch { }
}

# Garantir branch main
try { git branch -M main | Out-Null } catch { }

# Criar tag se não existir
$tagExists = git tag --list $Tag
if ([string]::IsNullOrWhiteSpace($tagExists)) {
    try { git tag $Tag | Out-Null } catch { }
}

# Preparar push com askpass sem expor token
$askpass = Join-Path $env:TEMP "git_askpass_token.cmd"
"@echo off`necho %GITHUB_TOKEN%" | Set-Content -Path $askpass -Encoding ASCII
$env:GIT_ASKPASS = $askpass
$pushUrl = "https://$login@github.com/$login/$RepoName.git"

# Criar repo (ignorar erro se já existir)
try {
    $createBody = @{ name=$RepoName; description="SwitchPilot - automação de corte para lives"; private=$false; has_issues=$true; has_wiki=$false } | ConvertTo-Json
    Invoke-RestMethod -Headers $Headers -Uri "https://api.github.com/user/repos" -Method Post -Body $createBody | Out-Null
    Write-Host "Repo criado."
} catch {
    Write-Host "Repo já existe ou não pôde ser criado. Prosseguindo."
}

# Push branch e tags
try { git push $pushUrl main } catch { Write-Host "Tentando push da branch main mesmo assim..." }
try { git push $pushUrl --tags } catch { Write-Host "Sem tags para enviar ou erro ao enviar tags." }

# Fixar remote origin sem credenciais embutidas
try { git remote remove origin 2>$null } catch { }
try { git remote add origin $RepoHttp } catch { }

# Limpar arquivo temporário
Remove-Item $askpass -Force -ErrorAction SilentlyContinue

# Criar release (ou reutilizar)
try {
    $rel = Invoke-RestMethod -Headers $Headers -Uri "https://api.github.com/repos/$login/$RepoName/releases/tags/$Tag"
    Write-Host "Release já existe."
} catch {
    $relBody = @{ tag_name=$Tag; name=$Tag; body="Primeira versão beta oficial."; draft=$false; prerelease=$false } | ConvertTo-Json
    $rel = Invoke-RestMethod -Headers $Headers -Uri "https://api.github.com/repos/$login/$RepoName/releases" -Method Post -Body $relBody
}
$relId = $rel.id

# Upload de assets
if (Test-Path $CleanZip) {
    $uploadUrl = "https://uploads.github.com/repos/$login/$RepoName/releases/$relId/assets?name=$([System.IO.Path]::GetFileName($CleanZip))"
    Invoke-RestMethod -Headers @{ Authorization="token $($env:GITHUB_TOKEN)"; "Content-Type"="application/zip" } -Uri $uploadUrl -Method Post -InFile $CleanZip | Out-Null
}
if (Test-Path $FullZip) {
    $uploadUrl2 = "https://uploads.github.com/repos/$login/$RepoName/releases/$relId/assets?name=$([System.IO.Path]::GetFileName($FullZip))"
    Invoke-RestMethod -Headers @{ Authorization="token $($env:GITHUB_TOKEN)"; "Content-Type"="application/zip" } -Uri $uploadUrl2 -Method Post -InFile $FullZip | Out-Null
}

Write-Host "OK: https://github.com/$login/$RepoName | release: $Tag" 