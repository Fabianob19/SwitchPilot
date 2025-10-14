# Script para atualizar automaticamente a versao em TODOS os arquivos
# Le o arquivo VERSION e atualiza todos os arquivos de documentacao

$versionFile = "VERSION"
if (-not (Test-Path $versionFile)) {
    Write-Error "Arquivo VERSION nao encontrado!"
    exit 1
}

# Ler versao do arquivo VERSION
$version = Get-Content $versionFile -Raw
$version = $version.Trim()
$versionWithV = "v$version"

Write-Host "Atualizando versao $version em todos os arquivos..."

# Atualizar README.md
if (Test-Path "README.md") {
    $content = Get-Content "README.md" -Raw
    $newContent = $content -replace "v1\.5\.[0-9]+", $versionWithV
    $newContent = $newContent -replace "SwitchPilot v1\.5\.[0-9]+", "SwitchPilot $versionWithV"
    $newContent = $newContent -replace "v1\.5\.[0-9]+_Setup\.exe", "${versionWithV}_Setup.exe"
    $newContent = $newContent -replace "v1\.5\.[0-9]+_Portable\.zip", "${versionWithV}_Portable.zip"
    
    if ($content -ne $newContent) {
        $newContent | Set-Content "README.md" -Encoding UTF8
        Write-Host "README.md atualizado"
    }
}

# Atualizar CHANGELOG.md
if (Test-Path "CHANGELOG.md") {
    $content = Get-Content "CHANGELOG.md" -Raw
    $newContent = $content -replace "## v1\.5\.[0-9]+", "## $versionWithV"
    
    if ($content -ne $newContent) {
        $newContent | Set-Content "CHANGELOG.md" -Encoding UTF8
        Write-Host "CHANGELOG.md atualizado"
    }
}

# Atualizar main_window.py
if (Test-Path "switchpilot/ui/main_window.py") {
    $content = Get-Content "switchpilot/ui/main_window.py" -Raw
    $newContent = $content -replace '"v1\.5\.[0-9]+"', "`"$versionWithV`""
    $newContent = $newContent -replace "v1\.5\.[0-9]+", $versionWithV
    
    if ($content -ne $newContent) {
        $newContent | Set-Content "switchpilot/ui/main_window.py" -Encoding UTF8
        Write-Host "main_window.py atualizado"
    }
}

Write-Host "Versao centralizada atualizada com sucesso!"
Write-Host "Versao atual: $versionWithV"