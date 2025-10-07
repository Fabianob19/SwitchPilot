# 📁 ESTRUTURA DO PROJETO SWITCHPILOT

## 🎯 **PASTA PRINCIPAL (F:\chat)**

```
F:\chat\
├── 📂 switchpilot/                 # Código-fonte principal
│   ├── 📂 core/                    # Lógica de negócio
│   │   ├── main_controller.py     # Controlador principal
│   │   └── monitor_thread.py      # Thread de monitoramento
│   ├── 📂 integrations/            # Integrações externas
│   │   ├── ndi_controller.py      # Controle NDI
│   │   ├── obs_controller.py      # Controle OBS
│   │   └── vmix_controller.py     # Controle vMix
│   ├── 📂 ui/                      # Interface gráfica
│   │   ├── main_window.py         # Janela principal
│   │   ├── themes.py              # Gerenciador de temas
│   │   ├── 📂 themes/             # Arquivos .qss de temas
│   │   └── 📂 widgets/            # Widgets personalizados
│   └── 📂 references/              # Imagens de referência (311 arquivos)
│
├── 📂 installer_output/            # Instalador compilado
│   └── SwitchPilot_v1.5.1_Setup.exe
│
├── 📂 release_v1.5.1/              # Build do PyInstaller
│   ├── SwitchPilot.exe
│   └── _internal/                  # Dependências empacotadas
│
├── 📂 docs/                        # Documentação técnica
├── 📂 tools/                       # Scripts auxiliares
│
├── 📄 main.py                      # Ponto de entrada
├── 📄 ICONE.ico                    # Ícone do aplicativo
├── 📄 SwitchPilot.spec             # Config do PyInstaller
├── 📄 SwitchPilot_Installer.iss    # Config do Inno Setup
├── 📄 version_info.txt             # Informações de versão
├── 📄 switchpilot.manifest         # Manifest do Windows
├── 📄 requirements.txt             # Dependências Python
├── 📄 requirements-lint.txt        # Dependências para lint
│
├── 📖 README.md                    # Documentação principal
├── 📖 CHANGELOG.md                 # Histórico de mudanças
├── 📖 CONTRIBUTING.md              # Guia de contribuição
├── 📖 LICENSE                      # Licença do projeto
├── 📖 SECURITY.md                  # Política de segurança
│
└── 📚 GUIAS/
    ├── GUIA_COMPLETO_ANTIVIRUS.md
    ├── REPORTAR_FALSO_POSITIVO_MICROSOFT.md
    ├── SOLUCAO_ERRO_INSTALACAO.md
    ├── COMO_CRIAR_INSTALADOR.md
    └── INSTRUCOES_UPLOAD_RELEASE.txt
```

---

## ✅ **ARQUIVOS IMPORTANTES (NÃO DELETAR):**

### **🔧 Configuração e Build:**
- `main.py` - Entrada principal
- `SwitchPilot.spec` - Configuração do PyInstaller
- `SwitchPilot_Installer.iss` - Configuração do Inno Setup
- `version_info.txt` - Informações de versão
- `switchpilot.manifest` - Manifest do Windows
- `ICONE.ico` - Ícone do aplicativo
- `requirements.txt` - Dependências
- `requirements-lint.txt` - Dependências para lint

### **📖 Documentação:**
- `README.md` - Documentação principal
- `CHANGELOG.md` - Histórico de versões
- `LICENSE` - Licença
- Todos os guias (.md)

### **📦 Build e Release:**
- `release_v1.5.1/` - Build atual do PyInstaller
- `installer_output/` - Instalador compilado

### **💻 Código-Fonte:**
- `switchpilot/` - Todo o código-fonte
- `docs/` - Documentação técnica
- `tools/` - Scripts auxiliares

---

## 🗑️ **ARQUIVOS LIMPOS (DELETADOS):**

### **Temporários do PyInstaller:**
- ❌ `build/` - Arquivos temporários de compilação
- ❌ `dist/` - Build antigo

### **Python Cache:**
- ❌ `__pycache__/` - Cache do Python (todas as pastas)
- ❌ `*.pyc` - Arquivos compilados
- ❌ `*.pyo` - Arquivos otimizados

### **Configurações Locais:**
- ❌ `switchpilot_config.json` - Config de teste local

---

## 🛡️ **ARQUIVOS IGNORADOS (.gitignore):**

O `.gitignore` está configurado para ignorar:
- Builds e distribuições
- Cache do Python
- Ambientes virtuais
- Logs e temporários
- Configurações locais
- Arquivos de IDE

---

## 📊 **TAMANHO APROXIMADO:**

```
📂 release_v1.5.1/          ~240 MB  (build completo)
📂 switchpilot/references/  ~15 MB   (311 imagens)
📂 switchpilot/             ~2 MB    (código-fonte)
📂 installer_output/        ~90 MB   (instalador)
📄 Documentação            ~500 KB   (guias e docs)
```

**Total:** ~350 MB

---

## 🎯 **COMANDOS ÚTEIS:**

### **Limpar tudo:**
```powershell
# Limpar builds
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

# Limpar cache Python
Get-ChildItem -Recurse -Include "__pycache__" | Remove-Item -Recurse -Force

# Limpar configs locais
Remove-Item switchpilot_config.json -ErrorAction SilentlyContinue
```

### **Recompilar:**
```powershell
# Limpar e compilar
pyinstaller SwitchPilot.spec --clean

# Gerar instalador
powershell -File criar_instalador_simples.ps1
```

---

## 📝 **NOTAS:**

1. **`release_v1.5.1/`** pode ser deletada se você recompilar
2. **`installer_output/`** contém o instalador final (distribuir este)
3. **Nunca delete** `switchpilot/` (código-fonte)
4. **`.gitignore`** mantém o repositório limpo automaticamente

---

**Projeto limpo e organizado! ✨**

