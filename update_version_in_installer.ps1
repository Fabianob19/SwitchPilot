# Script para atualizar automaticamente a versão no instalador Inno Setup
# Lê o arquivo VERSION e atualiza o SwitchPilot_Installer.iss

$versionFile = "VERSION"
$installerFile = "SwitchPilot_Installer.iss"

if (-not (Test-Path $versionFile)) {
    Write-Error "Arquivo VERSION não encontrado!"
    exit 1
}

if (-not (Test-Path $installerFile)) {
    Write-Error "Arquivo SwitchPilot_Installer.iss não encontrado!"
    exit 1
}

# Ler versão do arquivo VERSION
$version = Get-Content $versionFile -Raw
$version = $version.Trim()

Write-Host "Versão lida do arquivo VERSION: $version"

# Ler conteúdo do instalador
$content = Get-Content $installerFile -Raw

# Atualizar a linha #define MyAppVersion
$newContent = $content -replace '#define MyAppVersion "[^"]*"', "#define MyAppVersion `"$version`""

# Verificar se houve mudança
if ($content -eq $newContent) {
    Write-Host "Versão já está atualizada no instalador: $version"
} else {
    # Salvar arquivo atualizado
    $newContent | Set-Content $installerFile -Encoding UTF8
    Write-Host "✅ Instalador atualizado com versão: $version"
}

Write-Host "Versão centralizada atualizada com sucesso!"
