# Ferramentas de Desenvolvimento

Scripts auxiliares para desenvolvimento do SwitchPilot.

## 🔧 Ferramentas Disponíveis

### `generate_icon.py`
Gera o ícone do aplicativo (ICONE.ico).

**Uso:**
```bash
python tools/generate_icon.py
```

### `publish_github.ps1`
Script PowerShell para automatizar publicação de releases no GitHub.

**Uso:**
```powershell
.\tools\publish_github.ps1
```

## 📋 Workflow de Release

1. Atualizar versão em `main.py`
2. Atualizar `CHANGELOG.md`
3. Fazer commit e criar tag
4. Gerar build: `pyinstaller SwitchPilot.spec --clean`
5. Criar ZIP da release
6. Push para GitHub: `git push origin main --tags`
7. Criar release no GitHub com o ZIP
