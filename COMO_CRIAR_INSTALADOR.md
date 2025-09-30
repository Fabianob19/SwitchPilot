# 📦 Como Criar o Instalador do SwitchPilot

Guia completo para gerar um instalador profissional `.exe` do SwitchPilot.

## 🎯 Resultado Final

O instalador criará:
- ✅ Instalador único `SwitchPilot_v1.5.1_Setup.exe` (~100MB)
- ✅ Atalho no Menu Iniciar
- ✅ Atalho na Área de Trabalho (opcional)
- ✅ Registro em "Programas e Recursos" (desinstalação)
- ✅ Interface profissional em Português

---

## 🚀 Método 1: Automático (RECOMENDADO)

### Passo 1: Execute o Script

```powershell
.\criar_instalador.ps1
```

O script vai:
1. ✅ Verificar se Inno Setup está instalado
2. ✅ Baixar e instalar automaticamente se necessário
3. ✅ Gerar o instalador

### Passo 2: Pronto!

O instalador estará em:
```
installer_output\SwitchPilot_v1.5.1_Setup.exe
```

---

## 🔧 Método 2: Manual

### Passo 1: Instalar Inno Setup

1. Baixe em: https://jrsoftware.org/isdl.php
2. Instale normalmente (Next → Next → Install)

### Passo 2: Gerar Instalador

**Opção A - Via Interface:**
1. Abra `Inno Setup Compiler`
2. File → Open → `SwitchPilot_Installer.iss`
3. Build → Compile (ou F9)

**Opção B - Via Linha de Comando:**
```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" SwitchPilot_Installer.iss
```

---

## 📋 Pré-requisitos

Antes de gerar o instalador, certifique-se de que existe:

```
F:\chat\
  ├── release_v1.5.1\        # Pasta com o build
  │   ├── SwitchPilot.exe
  │   ├── LEIA-ME.txt
  │   └── _internal\
  ├── ICONE.ico              # Ícone do app
  ├── LICENSE                # Licença
  └── SwitchPilot_Installer.iss
```

Se a pasta `release_v1.5.1` não existir, gere o build primeiro:
```powershell
pyinstaller SwitchPilot.spec --clean
```

---

## 🎨 Personalizações

### Alterar Informações do Instalador

Edite `SwitchPilot_Installer.iss`:

```ini
#define MyAppName "SwitchPilot"
#define MyAppVersion "1.5.1"          ← Versão
#define MyAppPublisher "Fabianob19"   ← Seu nome/empresa
```

### Alterar Pasta de Instalação Padrão

```ini
DefaultDirName={autopf}\{#MyAppName}  ← C:\Program Files\SwitchPilot
```

Opções:
- `{autopf}` = `C:\Program Files`
- `{localappdata}` = `C:\Users\USUARIO\AppData\Local`
- `{commonappdata}` = `C:\ProgramData`

### Adicionar/Remover Arquivos

```ini
[Files]
Source: "release_v1.5.1\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "MEU_ARQUIVO.txt"; DestDir: "{app}"; Flags: ignoreversion  ← Adicionar
```

---

## 🧪 Testando o Instalador

### Teste em Máquina Virtual (Recomendado)

1. Crie uma VM Windows limpa
2. Execute o instalador
3. Teste o programa
4. Teste a desinstalação

### Teste na Máquina Local

1. Execute `SwitchPilot_v1.5.1_Setup.exe`
2. Instale normalmente
3. Teste o programa em `C:\Program Files\SwitchPilot\`

**Desinstalar:**
- Painel de Controle → Programas → Desinstalar SwitchPilot

---

## 📦 Distribuição

### Onde Hospedar

**Opção 1: GitHub Releases** ⭐ RECOMENDADO
```
1. Vá em: https://github.com/Fabianob19/SwitchPilot/releases/new
2. Tag: v1.5.1
3. Anexe: SwitchPilot_v1.5.1_Setup.exe
4. Publish
```

**Opção 2: Google Drive / Dropbox**
- Upload do instalador
- Compartilhe o link

**Opção 3: Site Próprio**
- Faça upload para seu servidor
- Link direto para download

### Link de Download

Depois de publicar no GitHub:
```
https://github.com/Fabianob19/SwitchPilot/releases/download/v1.5.1/SwitchPilot_v1.5.1_Setup.exe
```

---

## ❓ Problemas Comuns

### "Inno Setup não encontrado"
- Execute: `.\criar_instalador.ps1` (baixa automaticamente)
- Ou baixe manualmente: https://jrsoftware.org/isdl.php

### "release_v1.5.1 não encontrada"
```powershell
pyinstaller SwitchPilot.spec --clean
```

### "Windows Defender bloqueia o instalador"
- Normal para instaladores novos
- Solicite aos usuários: Clique "Mais informações" → "Executar assim mesmo"
- Para resolver: Assine digitalmente o instalador (requer certificado)

### Instalador muito grande
- Tamanho normal: 90-100MB (inclui Python + PyQt5 + OpenCV)
- Para reduzir: Usar compressão LZMA2 (já configurado)

---

## 🎓 Próximos Passos

### 1. Assinar Digitalmente (Opcional)

Evita avisos do Windows Defender.
Requer: Certificado de código (~$70-300/ano)

### 2. Auto-Atualização

Adicionar verificação de updates no app:
- Verifica GitHub Releases
- Baixa nova versão automaticamente

### 3. Instalador Multi-idioma

Adicionar mais idiomas em `[Languages]`:
```ini
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
```

---

## 📞 Suporte

Problemas ou dúvidas? Abra uma issue:
https://github.com/Fabianob19/SwitchPilot/issues
